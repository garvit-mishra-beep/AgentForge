import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_user
from models.schemas import (
    TeamCreate,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    TeamResponse,
    TeamTemplateCreate,
)

router = APIRouter(prefix="/teams", tags=["teams"])


def _db(request: Request):
    return request.app.state.db


@router.post("/template", status_code=201)
async def create_team_from_template(
    body: TeamTemplateCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    team_id = str(uuid.uuid4())

    async with db.transaction() as conn:
        await conn.execute(
            "INSERT INTO teams (id, name, description, created_by) VALUES ($1, $2, $3, $4)",
            team_id, body.name, body.description, user_id,
        )

        for member in body.members:
            existing = await conn.fetchrow(
                "SELECT id FROM team_members WHERE team_id = $1 AND role = $2",
                team_id, member.role.value,
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Role '{member.role.value}' already assigned",
                )

            member_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO team_members (id, team_id, role, model, instructions) VALUES ($1, $2, $3, $4, $5)",
                member_id, team_id, member.role.value, member.model, member.instructions,
            )

    return await _get_team_by_id(db, team_id, user_id)


@router.post("", status_code=201)
async def create_team(
    body: TeamCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    team_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO teams (id, name, description, created_by) VALUES ($1, $2, $3, $4)",
        team_id, body.name, body.description, user_id,
    )
    return await _get_team_by_id(db, team_id, user_id)


@router.get("")
async def list_teams(
    request: Request,
    user_id: str = Depends(require_user),
    limit: int = 50,
    offset: int = 0,
):
    db = _db(request)
    rows = await db.fetch(
        """
        SELECT t.id, t.name, t.description, t.created_by, t.created_at, t.updated_at,
               COALESCE(
                 jsonb_agg(
                   jsonb_build_object(
                     'id', tm.id, 'team_id', tm.team_id,
                     'role', tm.role::text, 'model', tm.model,
                     'instructions', COALESCE(tm.instructions, ''),
                     'created_at', tm.created_at
                   )
                 ) FILTER (WHERE tm.id IS NOT NULL),
                 '[]'::jsonb
               ) AS members
        FROM teams t
        LEFT JOIN team_members tm ON tm.team_id = t.id
        WHERE t.created_by = $1
        GROUP BY t.id, t.name, t.description, t.created_by, t.created_at, t.updated_at
        ORDER BY t.created_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_id, limit, offset,
    )
    return [_row_to_team_response(r) for r in rows]


@router.get("/{team_id}")
async def get_team(
    team_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    team = await _get_team_by_id(db, team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}")
async def update_team(
    team_id: str,
    body: TeamCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    existing = await db.fetchrow(
        "SELECT id FROM teams WHERE id = $1 AND created_by = $2",
        team_id, user_id,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Team not found")

    await db.execute(
        "UPDATE teams SET name = $1, description = $2, updated_at = NOW() WHERE id = $3",
        body.name, body.description, team_id,
    )
    return await _get_team_by_id(db, team_id, user_id)


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    result = await db.execute(
        "DELETE FROM teams WHERE id = $1 AND created_by = $2",
        team_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Team not found")


@router.post("/{team_id}/members", status_code=201)
async def add_team_member(
    team_id: str,
    body: TeamMemberCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    team = await db.fetchrow(
        "SELECT id FROM teams WHERE id = $1 AND created_by = $2",
        team_id, user_id,
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing = await db.fetchrow(
        "SELECT id FROM team_members WHERE team_id = $1 AND role = $2",
        team_id, body.role.value,
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Role '{body.role.value}' already assigned to this team",
        )

    member_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO team_members (id, team_id, role, model) VALUES ($1, $2, $3, $4)",
        member_id, team_id, body.role.value, body.model,
    )

    row = await db.fetchrow(
        "SELECT id, team_id, role::text, model, COALESCE(instructions, '') as instructions, created_at FROM team_members WHERE id = $1",
        member_id,
    )
    return TeamMemberResponse(
        id=row["id"], team_id=row["team_id"], role=row["role"],
        model=row["model"], instructions=row["instructions"],
        created_at=row["created_at"],
    )


@router.put("/{team_id}/members/{member_id}")
async def update_team_member(
    team_id: str, member_id: str,
    body: TeamMemberUpdate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    team = await db.fetchrow(
        "SELECT id FROM teams WHERE id = $1 AND created_by = $2",
        team_id, user_id,
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        "UPDATE team_members SET model = $1 WHERE id = $2 AND team_id = $3",
        body.model, member_id, team_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Member not found")

    row = await db.fetchrow(
        "SELECT id, team_id, role::text, model, COALESCE(instructions, '') as instructions, created_at FROM team_members WHERE id = $1",
        member_id,
    )
    return TeamMemberResponse(
        id=row["id"], team_id=row["team_id"], role=row["role"],
        model=row["model"], instructions=row["instructions"],
        created_at=row["created_at"],
    )


@router.delete("/{team_id}/members/{member_id}", status_code=204)
async def remove_team_member(
    team_id: str,
    member_id: str,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    result = await db.execute(
        "DELETE FROM team_members WHERE id = $1 AND team_id = $2 AND team_id IN (SELECT id FROM teams WHERE created_by = $3)",
        member_id, team_id, user_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Member not found")


async def _get_team_by_id(db, team_id: str, user_id: str) -> TeamResponse | None:
    row = await db.fetchrow(
        """
        SELECT t.id, t.name, t.description, t.created_by, t.created_at, t.updated_at,
               COALESCE(
                 jsonb_agg(
                   jsonb_build_object(
                     'id', tm.id, 'team_id', tm.team_id,
                     'role', tm.role::text, 'model', tm.model,
                     'instructions', COALESCE(tm.instructions, ''),
                     'created_at', tm.created_at
                   )
                 ) FILTER (WHERE tm.id IS NOT NULL),
                 '[]'::jsonb
               ) AS members
        FROM teams t
        LEFT JOIN team_members tm ON tm.team_id = t.id
        WHERE t.id = $1 AND t.created_by = $2
        GROUP BY t.id, t.name, t.description, t.created_by, t.created_at, t.updated_at
        """,
        team_id, user_id,
    )
    if not row:
        return None
    return _row_to_team_response(row)


def _row_to_team_response(row) -> TeamResponse:
    members_data = row.get("members") or []
    if isinstance(members_data, str):
        import json
        members_data = json.loads(members_data)

    return TeamResponse(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"],
        created_by=str(row["created_by"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        members=[
            TeamMemberResponse(
                id=str(m["id"]),
                team_id=str(m["team_id"]),
                role=m["role"],
                model=m["model"],
                instructions=m.get("instructions", ""),
                created_at=m["created_at"],
            )
            for m in members_data
        ],
    )
