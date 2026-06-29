import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile

from app.auth import require_user
from core.config import settings
from models.schemas import (
    FileResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectTeamAssign,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])

UPLOAD_DIR = Path(settings.upload_dir) if hasattr(settings, "upload_dir") else Path("uploads")
MAX_FILE_SIZE = settings.max_upload_size if hasattr(settings, "max_upload_size") else 100 * 1024 * 1024

_ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".html", ".css", ".scss", ".sass", ".less",
    ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".md", ".txt", ".rst",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".sh", ".bat", ".ps1", ".env", ".dockerfile",
    ".sql", ".graphql",
}


def _sanitize_filename(filename: str) -> str:
    """Remove path separators and dangerous characters from filename."""
    filename = filename.replace("\\", "/").split("/")[-1]
    filename = re.sub(r'[^\w.\- ]', '', filename)
    if not filename or filename in (".", ".."):
        return f"upload_{uuid.uuid4().hex[:8]}"
    return filename


def _validate_filepath(storage_path: Path, allowed_base: Path) -> None:
    """Ensure resolved path is within the allowed base directory (path traversal guard)."""
    resolved = storage_path.resolve()
    base_resolved = allowed_base.resolve()
    if not str(resolved).startswith(str(base_resolved)):
        raise HTTPException(status_code=400, detail="Invalid file path")


def _db(request: Request):
    return request.app.state.db


async def _require_project_owner(db, project_id: str, user_id: str) -> None:
    """Raise 404 unless ``project_id`` exists and is owned by ``user_id``.

    Closes the file-scoped IDOR: file routes filter by ``project_id`` only,
    so without this check any authenticated user could reach another tenant's
    project files by guessing/leaking ids.
    """
    owns = await db.fetchval(
        "SELECT 1 FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not owns:
        raise HTTPException(status_code=404, detail="Project not found")


def _ensure_upload_dir(project_id: str):
    path = UPLOAD_DIR / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


# â”€â”€ Projects CRUD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("", status_code=201)
async def create_project(
    body: ProjectCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    project_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO projects (id, name, description, created_by) VALUES ($1, $2, $3, $4)",
        project_id, body.name, body.description, user_id,
    )
    return await _get_project_by_id(db, project_id, user_id)


@router.get("")
async def list_projects(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    db = _db(request)
    rows = await db.fetch(
        """
        SELECT p.id, p.name, p.description, p.created_by, p.created_at, p.updated_at,
               COALESCE(
                 jsonb_agg(pt.team_id) FILTER (WHERE pt.team_id IS NOT NULL),
                 '[]'::jsonb
               ) AS team_ids
        FROM projects p
        LEFT JOIN project_teams pt ON pt.project_id = p.id
        WHERE p.created_by = $1
        GROUP BY p.id, p.name, p.description, p.created_by, p.created_at, p.updated_at
        ORDER BY p.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset,
    )
    return [_row_to_project_response(r) for r in rows]


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    project = await _get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    existing = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    sets = []
    values = []
    idx = 1
    if body.name is not None:
        sets.append(f"name = ${idx}")
        values.append(body.name)
        idx += 1
    if body.description is not None:
        sets.append(f"description = ${idx}")
        values.append(body.description)
        idx += 1
    if sets:
        sets.append("updated_at = NOW()")
        values.append(project_id)
        await db.execute(
            f"UPDATE projects SET {', '.join(sets)} WHERE id = ${idx}",
            *values,
        )

    return await _get_project_by_id(db, project_id, user_id)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    result = await db.execute(
        "DELETE FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Project not found")

    # Clean up uploaded files
    upload_path = UPLOAD_DIR / project_id
    if upload_path.exists():
        shutil.rmtree(upload_path, ignore_errors=True)


# â”€â”€ Project-Team Association â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{project_id}/teams", status_code=201)
async def assign_team_to_project(
    project_id: str,
    body: ProjectTeamAssign,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    team = await db.fetchrow(
        "SELECT id FROM teams WHERE id = $1 AND created_by = $2",
        body.team_id, user_id,
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    try:
        await db.execute(
            "INSERT INTO project_teams (project_id, team_id) VALUES ($1, $2)",
            project_id, body.team_id,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Team already assigned to this project")

    return {"status": "ok"}


@router.delete("/{project_id}/teams/{team_id}", status_code=204)
async def remove_team_from_project(
    project_id: str,
    team_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        "DELETE FROM project_teams WHERE project_id = $1 AND team_id = $2",
        project_id, team_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Team not assigned to this project")


# â”€â”€ File Upload â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@router.post("/{project_id}/upload", status_code=201)
async def upload_file(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    file: UploadFile = File(...),
    parent_id: str = Form(default=""),
):
    db = _db(request)
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_filename = _sanitize_filename(file.filename)
    ext = Path(safe_filename).suffix.lower()
    if ext and ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File extension '{ext}' is not allowed")

    # Read file in chunks to check size before fully loading into memory
    size = 0
    chunks = []
    while chunk := await file.read(8192):  # Read in 8KB chunks
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB")
        chunks.append(chunk)
    content = b"".join(chunks)

    file_hash = hashlib.sha256(content).hexdigest()
    file_id = str(uuid.uuid4())
    storage_path = _ensure_upload_dir(project_id) / f"{file_id}_{safe_filename}"
    _validate_filepath(storage_path, _ensure_upload_dir(project_id))

    with open(storage_path, "wb") as f:
        f.write(content)

    file_record_id = str(uuid.uuid4())
    parent_uuid = uuid.UUID(parent_id) if parent_id else None

    await db.execute(
        """
        INSERT INTO project_files (id, project_id, parent_id, filename, filepath, mime_type, size_bytes, file_hash, status, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        file_record_id, project_id, parent_uuid,
        safe_filename, str(storage_path),
        file.content_type or "application/octet-stream",
        len(content), file_hash, "uploaded", user_id,
    )

    row = await db.fetchrow(
        """
        SELECT id, project_id, parent_id, filename, filepath, mime_type, size_bytes,
               is_directory, file_hash, status, created_by, created_at, updated_at
        FROM project_files WHERE id = $1
        """,
        file_record_id,
    )

    _trigger_context_parse(db, uuid.UUID(file_record_id), str(row["filepath"]), str(row["filename"]))

    return _row_to_file_response(row)


@router.post("/{project_id}/upload/zip", status_code=201)
async def upload_zip(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    file: UploadFile = File(...),
):
    """Upload and extract a ZIP archive into the project."""
    import io
    import zipfile

    db = _db(request)
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename or not file.filename.endswith((".zip", ".tar.gz", ".tgz")):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported")

    # Read file in chunks to check size before fully loading into memory
    size = 0
    chunks = []
    while chunk := await file.read(8192):  # Read in 8KB chunks
        size += len(chunk)
        if size > MAX_FILE_SIZE * 2:
            raise HTTPException(status_code=413, detail="Archive too large")
        chunks.append(chunk)
    content = b"".join(chunks)

    storage_root = _ensure_upload_dir(project_id) / "archive"
    storage_root.mkdir(exist_ok=True)

    archive_id = str(uuid.uuid4())
    archive_path = storage_root / f"{archive_id}_{file.filename}"
    with open(archive_path, "wb") as f:
        f.write(content)

    extracted = []
    total_uncompressed_size = 0

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for zip_info in zf.infolist():
                if zip_info.is_dir():
                    continue

                total_uncompressed_size += zip_info.file_size
                if total_uncompressed_size > MAX_FILE_SIZE * 10:
                    raise HTTPException(status_code=400, detail="ZIP bomb detected: aggregate uncompressed size exceeds limit")

                # Check for ZIP bombs by comparing compressed vs uncompressed size
                if zip_info.file_size > MAX_FILE_SIZE * 10:  # Allow 10x expansion
                    raise HTTPException(status_code=400, detail="ZIP bomb detected: excessive uncompressed size")

                normalized = zip_info.filename.replace("\\", "/")
                safe_name = _sanitize_filename(Path(normalized).name)
                ext = Path(safe_name).suffix.lower()
                if ext and ext not in _ALLOWED_EXTENSIONS:
                    continue

                # Use normalized path for validation and extraction
                entry_path = (storage_root / normalized).resolve()
                _validate_filepath(entry_path, storage_root)
                entry_path.parent.mkdir(parents=True, exist_ok=True)

                # Read file data using the validated path
                file_data = zf.read(zip_info.filename)
                file_hash = hashlib.sha256(file_data).hexdigest()
                entry_id = str(uuid.uuid4())

                zf.extract(zip_info, storage_root)

                await db.execute(
                    """
                    INSERT INTO project_files (id, project_id, filename, filepath, mime_type, size_bytes, file_hash, status, metadata, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    entry_id, project_id,
                    safe_name,
                    str(entry_path),
                    "application/octet-stream",
                    zip_info.file_size,
                    file_hash, "uploaded",
                    json.dumps({"source_archive": file.filename, "original_path": normalized}),
                    user_id,
                )
                extracted.append({"id": entry_id, "path": normalized})
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP archive")

    # Auto-parse extracted code files
    for entry_data in extracted:
        _trigger_context_parse(db, uuid.UUID(entry_data["id"]), str(storage_root / entry_data["path"]), entry_data["path"])

    return {"status": "ok", "files_extracted": len(extracted), "files": extracted}


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str,
    request: Request,
    user_id: str = Depends(require_user),
    parent_id: str = Query(default=""),
):
    db = _db(request)
    project = await db.fetchrow(
        "SELECT id FROM projects WHERE id = $1 AND created_by = $2",
        project_id, user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if parent_id:
        rows = await db.fetch(
            """
            SELECT id, project_id, parent_id, filename, filepath, mime_type, size_bytes,
                   is_directory, file_hash, status, created_by, created_at, updated_at
            FROM project_files
            WHERE project_id = $1 AND parent_id = $2
            ORDER BY is_directory DESC, filename ASC
            """,
            project_id, uuid.UUID(parent_id),
        )
    else:
        rows = await db.fetch(
            """
            SELECT id, project_id, parent_id, filename, filepath, mime_type, size_bytes,
                   is_directory, file_hash, status, created_by, created_at, updated_at
            FROM project_files
            WHERE project_id = $1 AND parent_id IS NULL
            ORDER BY is_directory DESC, filename ASC
            """,
            project_id,
        )

    return [_row_to_file_response(r) for r in rows]


@router.get("/{project_id}/files/{file_id}")
async def get_file_metadata(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    await _require_project_owner(db, project_id, user_id)
    row = await db.fetchrow(
        """
        SELECT id, project_id, parent_id, filename, filepath, mime_type, size_bytes,
               is_directory, file_hash, status, created_by, created_at, updated_at
        FROM project_files
        WHERE id = $1 AND project_id = $2
        """,
        file_id, project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return _row_to_file_response(row)


@router.delete("/{project_id}/files/{file_id}", status_code=204)
async def delete_file(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    await _require_project_owner(db, project_id, user_id)
    row = await db.fetchrow(
        "SELECT filepath FROM project_files WHERE id = $1 AND project_id = $2",
        file_id, project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    await db.execute(
        "DELETE FROM project_files WHERE id = $1 AND project_id = $2",
        file_id, project_id,
    )

    file_path = Path(str(row["filepath"]))
    if file_path.exists():
        file_path.unlink(missing_ok=True)


@router.get("/{project_id}/files/{file_id}/download")
async def download_file(
    project_id: str,
    file_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    from fastapi.responses import FileResponse as FastAPIFileResponse

    db = _db(request)
    await _require_project_owner(db, project_id, user_id)
    row = await db.fetchrow(
        """
        SELECT id, project_id, filename, filepath, mime_type, size_bytes
        FROM project_files
        WHERE id = $1 AND project_id = $2
        """,
        file_id, project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(str(row["filepath"]))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FastAPIFileResponse(
        path=file_path,
        filename=str(row["filename"]),
        media_type=str(row["mime_type"]),
    )


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _trigger_context_parse(db, file_id: uuid.UUID, filepath: str, filename: str):
    """Asynchronously parse file context after upload."""

    async def _parse():
        try:
            pf_row = await db.fetchrow(
                "SELECT project_id FROM project_files WHERE id = $1", str(file_id),
            )
            if not pf_row or not pf_row["project_id"]:
                return
            project_id = str(pf_row["project_id"])

            from app.file_parser import parse_file

            parsed = parse_file(str(file_id), filepath)
            if not parsed.symbols and not parsed.imports:
                return  # Not a code file

            import json
            import uuid as _uuid

            ctx_id = str(_uuid.uuid4())
            await db.execute(
                """
                INSERT INTO repository_contexts (id, project_id, file_id, file_path, language)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (file_id) DO UPDATE SET
                    language = EXCLUDED.language, parsed_at = NOW(), error_message = NULL
                """,
                ctx_id, project_id, str(file_id), filepath, parsed.language,
            )

            actual = await db.fetchrow(
                "SELECT id FROM repository_contexts WHERE file_id = $1", str(file_id),
            )
            if not actual:
                return
            actual_id = str(actual["id"])

            await db.execute("DELETE FROM code_symbols WHERE context_id = $1", actual_id)
            await db.execute("DELETE FROM code_imports WHERE context_id = $1", actual_id)
            await db.execute("DELETE FROM code_chunks WHERE context_id = $1", actual_id)

            for sym in parsed.symbols:
                await db.execute(
                    "INSERT INTO code_symbols (id, context_id, symbol_type, name, line_start, line_end, signature, docstring, visibility, metadata) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                    str(_uuid.uuid4()), actual_id, sym.symbol_type, sym.name, sym.line_start,
                    sym.line_end, sym.signature[:500], sym.docstring, sym.visibility,
                    json.dumps(sym.metadata) if sym.metadata else "{}",
                )

            for imp in parsed.imports:
                await db.execute(
                    "INSERT INTO code_imports (id, context_id, source, alias, is_relative, line_number) VALUES ($1,$2,$3,$4,$5,$6)",
                    str(_uuid.uuid4()), actual_id, imp.source[:500], imp.alias[:255],
                    imp.is_relative, imp.line_number,
                )

            for ch in parsed.chunks:
                await db.execute(
                    "INSERT INTO code_chunks (id, context_id, chunk_type, name, content, line_start, line_end, tokens_estimate, metadata) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)",
                    str(_uuid.uuid4()), actual_id, ch.chunk_type, ch.name, ch.content,
                    ch.line_start, ch.line_end, ch.tokens_estimate,
                    json.dumps(ch.metadata) if ch.metadata else "{}",
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Auto-parse failed for %s: %s", filename, e)

    from core.task_tracker import tracker
    tracker.create_task(_parse(), name=f"parse-{str(file_id)[:8]}")


async def _get_project_by_id(db, project_id: str, user_id: str) -> ProjectResponse | None:
    row = await db.fetchrow(
        """
        SELECT p.id, p.name, p.description, p.created_by, p.created_at, p.updated_at,
               COALESCE(
                 jsonb_agg(pt.team_id) FILTER (WHERE pt.team_id IS NOT NULL),
                 '[]'::jsonb
               ) AS team_ids
        FROM projects p
        LEFT JOIN project_teams pt ON pt.project_id = p.id
        WHERE p.id = $1 AND p.created_by = $2
        GROUP BY p.id, p.name, p.description, p.created_by, p.created_at, p.updated_at
        """,
        project_id, user_id,
    )
    if not row:
        return None
    return _row_to_project_response(row)


def _row_to_project_response(row) -> ProjectResponse:
    team_ids = row.get("team_ids") or []
    if isinstance(team_ids, str):
        team_ids = json.loads(team_ids)

    return ProjectResponse(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"],
        created_by=str(row["created_by"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        team_ids=[str(t) for t in team_ids],
    )


def _row_to_file_response(row) -> FileResponse:
    return FileResponse(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        parent_id=str(row["parent_id"]) if row.get("parent_id") else None,
        filename=row["filename"],
        filepath=row["filepath"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        is_directory=row["is_directory"],
        file_hash=row["file_hash"],
        status=row["status"],
        created_by=str(row["created_by"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
