"""Repository Context API routes."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import require_user
from app.file_parser import ParsedFile, parse_file

router = APIRouter(prefix="/projects/{project_id}/context", tags=["context"])


def _db(request: Request):
    return request.app.state.db


async def _ensure_project_access(db, project_id: str, user_id: str):
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


async def _ensure_file_exists(db, project_id: str, file_id: str, user_id: str):
    await _ensure_project_access(db, project_id, user_id)
    row = await db.fetchrow(
        "SELECT id FROM project_files WHERE id = $1 AND project_id = $2",
        file_id, project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")


# ── Parse & Store ────────────────────────────────────────────────────────


@router.post("/parse/{file_id}", status_code=201)
async def parse_file_context(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Parse a single file and store its context."""
    db = _db(request)
    await _ensure_file_exists(db, project_id, file_id, user_id)

    row = await db.fetchrow(
        "SELECT id, filename, filepath, mime_type, size_bytes FROM project_files WHERE id = $1",
        file_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = str(row["filepath"])

    # Parse
    try:
        parsed: ParsedFile = parse_file(file_id, file_path)
    except Exception as e:
        parsed = ParsedFile(
            file_id=file_id,
            file_path=file_path,
            language="",
            symbols=[],
            imports=[],
            chunks=[],
        )
        # Store error
        ctx_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO repository_contexts (id, project_id, file_id, file_path, language, error_message)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (file_id) DO UPDATE SET
                language = EXCLUDED.language,
                parsed_at = NOW(),
                error_message = EXCLUDED.error_message
            """,
            ctx_id, project_id, file_id, file_path, "", str(e),
        )
        return {"status": "error", "error": str(e)}

    # Upsert context
    ctx_id = str(uuid.uuid4())
    await db.execute(
        """
        INSERT INTO repository_contexts (id, project_id, file_id, file_path, language)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (file_id) DO UPDATE SET
            language = EXCLUDED.language,
            parsed_at = NOW(),
            error_message = NULL
        RETURNING id
        """,
        ctx_id, project_id, file_id, file_path, parsed.language,
    )

    # Get actual context_id
    ctx_row = await db.fetchrow(
        "SELECT id FROM repository_contexts WHERE file_id = $1", file_id,
    )
    if not ctx_row:
        raise HTTPException(status_code=500, detail="Failed to create context")
    actual_ctx_id = str(ctx_row["id"])

    # Clear old symbols/imports/chunks
    await db.execute("DELETE FROM code_symbols WHERE context_id = $1", actual_ctx_id)
    await db.execute("DELETE FROM code_imports WHERE context_id = $1", actual_ctx_id)
    await db.execute("DELETE FROM code_chunks WHERE context_id = $1", actual_ctx_id)

    # Insert symbols
    for sym in parsed.symbols:
        await db.execute(
            """
            INSERT INTO code_symbols (id, context_id, symbol_type, name, line_start, line_end, signature, docstring, visibility, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            str(uuid.uuid4()), actual_ctx_id, sym.symbol_type, sym.name,
            sym.line_start, sym.line_end, sym.signature[:500],
            sym.docstring, sym.visibility,
            json.dumps(sym.metadata) if sym.metadata else "{}",
        )

    # Insert imports
    for imp in parsed.imports:
        await db.execute(
            """
            INSERT INTO code_imports (id, context_id, source, alias, is_relative, line_number)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(uuid.uuid4()), actual_ctx_id, imp.source[:500],
            imp.alias[:255], imp.is_relative, imp.line_number,
        )

    # Insert chunks
    for ch in parsed.chunks:
        await db.execute(
            """
            INSERT INTO code_chunks (id, context_id, chunk_type, name, content, line_start, line_end, tokens_estimate, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            str(uuid.uuid4()), actual_ctx_id, ch.chunk_type, ch.name,
            ch.content, ch.line_start, ch.line_end, ch.tokens_estimate,
            json.dumps(ch.metadata) if ch.metadata else "{}",
        )

    return {
        "status": "ok",
        "context_id": actual_ctx_id,
        "language": parsed.language,
        "symbols": len(parsed.symbols),
        "imports": len(parsed.imports),
        "chunks": len(parsed.chunks),
    }


@router.post("/parse-all")
async def parse_all_files(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Parse all unparsed files in a project."""
    db = _db(request)
    await _ensure_project_access(db, project_id, user_id)

    # Get all files that don't have a context yet (or errored)
    rows = await db.fetch(
        """
        SELECT f.id, f.filename, f.filepath
        FROM project_files f
        LEFT JOIN repository_contexts rc ON rc.file_id = f.id
        WHERE f.project_id = $1
          AND (
            f.filename ILIKE '%.py' OR f.filename ILIKE '%.js'
            OR f.filename ILIKE '%.ts' OR f.filename ILIKE '%.tsx'
            OR f.filename ILIKE '%.jsx' OR f.filename ILIKE '%.java'
            OR f.filename ILIKE '%.go' OR f.filename ILIKE '%.rs'
            OR f.filename ILIKE '%.c' OR f.filename ILIKE '%.cpp'
            OR f.filename ILIKE '%.h' OR f.filename ILIKE '%.hpp'
            OR f.filename ILIKE '%.cs' OR f.filename ILIKE '%.rb'
            OR f.filename ILIKE '%.php' OR f.filename ILIKE '%.swift'
            OR f.filename ILIKE '%.kt' OR f.filename ILIKE '%.scala'
            OR f.filename ILIKE '%.sql' OR f.filename ILIKE '%.sh'
          )
          AND (rc.id IS NULL OR rc.error_message IS NOT NULL)
        """,
        project_id,
    )

    results: list[dict[str, Any]] = []
    for row in rows:
        file_id = str(row["id"])
        file_path = str(row["filepath"])
        try:
            parsed = parse_file(file_id, file_path)
            results.append({
                "file_id": file_id,
                "filename": str(row["filename"]),
                "language": parsed.language,
                "symbols": len(parsed.symbols),
                "imports": len(parsed.imports),
                "status": "parsed",
            })
        except Exception as e:
            results.append({
                "file_id": file_id,
                "filename": str(row["filename"]),
                "status": "error",
                "error": str(e),
            })

    return {"total": len(results), "results": results}


# ── Query ────────────────────────────────────────────────────────────────


@router.get("/summary")
async def get_context_summary(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Get a summary of all parsed contexts in a project."""
    db = _db(request)
    await _ensure_project_access(db, project_id, user_id)

    rows = await db.fetch(
        """
        SELECT rc.file_id, rc.file_path, rc.language, rc.parsed_at, rc.error_message,
               pf.filename,
               (SELECT count(*) FROM code_symbols WHERE context_id = rc.id) AS symbol_count,
               (SELECT count(*) FROM code_imports WHERE context_id = rc.id) AS import_count,
               (SELECT count(*) FROM code_chunks WHERE context_id = rc.id) AS chunk_count
        FROM repository_contexts rc
        JOIN project_files pf ON pf.id = rc.file_id
        WHERE rc.project_id = $1
        ORDER BY rc.parsed_at DESC
        """,
        project_id,
    )

    return [
        {
            "file_id": str(r["file_id"]),
            "filename": r["filename"],
            "file_path": r["file_path"],
            "language": r["language"],
            "parsed_at": r["parsed_at"].isoformat() if r["parsed_at"] else None,
            "error_message": r["error_message"],
            "symbol_count": r["symbol_count"],
            "import_count": r["import_count"],
            "chunk_count": r["chunk_count"],
        }
        for r in rows
    ]


@router.get("/symbols")
async def list_symbols(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    file_id: str = Query(default=""),
    symbol_type: str = Query(default=""),
    search: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
):
    """List symbols across project files."""
    db = _db(request)
    await _ensure_project_access(db, project_id, user_id)

    conditions = ["rc.project_id = $1"]
    params: list[Any] = [project_id]
    idx = 2

    if file_id:
        conditions.append(f"rc.file_id = ${idx}")
        params.append(file_id)
        idx += 1
    if symbol_type:
        conditions.append(f"cs.symbol_type = ${idx}")
        params.append(symbol_type)
        idx += 1
    if search:
        conditions.append(f"cs.name ILIKE ${idx}")
        params.append(f"%{search}%")
        idx += 1

    query = f"""
        SELECT cs.id, cs.symbol_type, cs.name, cs.line_start, cs.line_end,
               cs.signature, cs.docstring, cs.visibility,
               pf.filename, pf.filepath
        FROM code_symbols cs
        JOIN repository_contexts rc ON rc.id = cs.context_id
        JOIN project_files pf ON pf.id = rc.file_id
        WHERE {' AND '.join(conditions)}
        ORDER BY cs.name
        LIMIT ${idx}
    """
    params.append(limit)

    rows = await db.fetch(query, *params)
    return [
        {
            "id": str(r["id"]),
            "symbol_type": r["symbol_type"],
            "name": r["name"],
            "line_start": r["line_start"],
            "line_end": r["line_end"],
            "signature": r["signature"],
            "docstring": r["docstring"],
            "visibility": r["visibility"],
            "filename": r["filename"],
            "filepath": r["filepath"],
        }
        for r in rows
    ]


@router.get("/imports")
async def list_imports(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    file_id: str = Query(default=""),
    limit: int = Query(default=200, ge=1, le=1000),
):
    """List imports across project files."""
    db = _db(request)
    await _ensure_project_access(db, project_id, user_id)

    if file_id:
        rows = await db.fetch(
            """
            SELECT ci.source, ci.alias, ci.is_relative, ci.line_number, pf.filename
            FROM code_imports ci
            JOIN repository_contexts rc ON rc.id = ci.context_id
            JOIN project_files pf ON pf.id = rc.file_id
            WHERE rc.project_id = $1 AND rc.file_id = $2
            ORDER BY ci.line_number
            LIMIT $3
            """,
            project_id, file_id, limit,
        )
    else:
        rows = await db.fetch(
            """
            SELECT ci.source, ci.alias, ci.is_relative, ci.line_number, pf.filename
            FROM code_imports ci
            JOIN repository_contexts rc ON rc.id = ci.context_id
            JOIN project_files pf ON pf.id = rc.file_id
            WHERE rc.project_id = $1
            ORDER BY pf.filename, ci.line_number
            LIMIT $2
            """,
            project_id, limit,
        )

    return [
        {
            "source": r["source"],
            "alias": r["alias"],
            "is_relative": r["is_relative"],
            "line_number": r["line_number"],
            "filename": r["filename"],
        }
        for r in rows
    ]


@router.get("/chunks")
async def list_chunks(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    file_id: str = Query(default=""),
    chunk_type: str = Query(default=""),
    search: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List code chunks, optionally filtered."""
    db = _db(request)
    await _ensure_project_access(db, project_id, user_id)

    conditions = ["rc.project_id = $1"]
    params: list[Any] = [project_id]
    idx = 2

    if file_id:
        conditions.append(f"rc.file_id = ${idx}")
        params.append(file_id)
        idx += 1
    if chunk_type:
        conditions.append(f"cc.chunk_type = ${idx}")
        params.append(chunk_type)
        idx += 1
    if search:
        conditions.append(f"cc.name ILIKE ${idx}")
        params.append(f"%{search}%")
        idx += 1

    query = f"""
        SELECT cc.id, cc.chunk_type, cc.name, cc.content, cc.line_start, cc.line_end,
               cc.tokens_estimate, pf.filename
        FROM code_chunks cc
        JOIN repository_contexts rc ON rc.id = cc.context_id
        JOIN project_files pf ON pf.id = rc.file_id
        WHERE {' AND '.join(conditions)}
        ORDER BY cc.line_start
        LIMIT ${idx}
    """
    params.append(limit)

    rows = await db.fetch(query, *params)
    return [
        {
            "id": str(r["id"]),
            "chunk_type": r["chunk_type"],
            "name": r["name"],
            "content": r["content"],
            "line_start": r["line_start"],
            "line_end": r["line_end"],
            "tokens_estimate": r["tokens_estimate"],
            "filename": r["filename"],
        }
        for r in rows
    ]


@router.get("/file/{file_id}")
async def get_file_context(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Get full context for a single file."""
    db = _db(request)
    await _ensure_file_exists(db, project_id, file_id, user_id)

    ctx = await db.fetchrow(
        "SELECT id, language, parsed_at, error_message FROM repository_contexts WHERE file_id = $1",
        file_id,
    )
    if not ctx:
        raise HTTPException(status_code=404, detail="File not parsed yet")

    ctx_id = str(ctx["id"])

    symbols = await db.fetch(
        "SELECT * FROM code_symbols WHERE context_id = $1 ORDER BY line_start", ctx_id,
    )
    imports = await db.fetch(
        "SELECT * FROM code_imports WHERE context_id = $1 ORDER BY line_number", ctx_id,
    )
    chunks = await db.fetch(
        "SELECT * FROM code_chunks WHERE context_id = $1 ORDER BY line_start", ctx_id,
    )

    return {
        "context_id": ctx_id,
        "language": ctx["language"],
        "parsed_at": ctx["parsed_at"].isoformat() if ctx["parsed_at"] else None,
        "error_message": ctx["error_message"],
        "symbols": [
            {
                "id": str(s["id"]),
                "symbol_type": s["symbol_type"],
                "name": s["name"],
                "line_start": s["line_start"],
                "line_end": s["line_end"],
                "signature": s["signature"],
                "docstring": s["docstring"],
                "visibility": s["visibility"],
            }
            for s in symbols
        ],
        "imports": [
            {
                "id": str(i["id"]),
                "source": i["source"],
                "alias": i["alias"],
                "is_relative": i["is_relative"],
                "line_number": i["line_number"],
            }
            for i in imports
        ],
        "chunks": [
            {
                "id": str(c["id"]),
                "chunk_type": c["chunk_type"],
                "name": c["name"],
                "content": c["content"],
                "line_start": c["line_start"],
                "line_end": c["line_end"],
                "tokens_estimate": c["tokens_estimate"],
            }
            for c in chunks
        ],
    }


@router.delete("/file/{file_id}", status_code=204)
async def delete_file_context(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    """Delete parsed context for a file."""
    db = _db(request)
    await _ensure_file_exists(db, project_id, file_id, user_id)

    await db.execute(
        "DELETE FROM repository_contexts WHERE file_id = $1 AND project_id = $2",
        file_id, project_id,
    )
