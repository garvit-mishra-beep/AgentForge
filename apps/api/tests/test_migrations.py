import pytest

from app.main import app
from models.schemas import AgentRole, MessageType


@pytest.mark.asyncio
async def test_database_enums_match_python_schemas():
    """Verify that all enums defined in AgentRole and MessageType schemas exist in the DB."""
    pool = app.state.db

    # Query database for all values of agent_role enum type
    db_agent_roles = await pool.fetch(
        "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'agent_role'"
    )
    db_agent_roles_set = {r["enumlabel"] for r in db_agent_roles}

    # Query database for all values of message_type enum type
    db_message_types = await pool.fetch(
        "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'message_type'"
    )
    db_message_types_set = {t["enumlabel"] for t in db_message_types}

    # Validate AgentRole
    for role in AgentRole:
        assert role.value in db_agent_roles_set, f"AgentRole '{role.value}' is missing from the database agent_role enum!"

    # Validate MessageType
    for msg_type in MessageType:
        assert msg_type.value in db_message_types_set, f"MessageType '{msg_type.value}' is missing from the database message_type enum!"
