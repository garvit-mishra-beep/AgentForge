from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import declared_attr, Mapped

from packages.state.models.base import Base, TimestampMixin, GUIDMixin


# ===============================
# USER MODEL
# ===============================


class User(GUIDMixin, TimestampMixin, Base):
    """
    User model.

    Represents a user in the system.
    """

    __tablename__ = "users"

    # User credentials
    email: Mapped[str] = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    full_name: Mapped[str] = Column(
        String(100),
        nullable=True,
    )
    username: Mapped[str] = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = Column(
        String(128),
        nullable=False,
        default="placeholder",
    )

    # User flags
    is_active: Mapped[bool] = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_verified: Mapped[bool] = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    # User preferences
    settings: Mapped[dict] = Column(
        Text,
        default="{}",
        nullable=True,
    )

    # Last login
    last_login_at: Mapped[datetime] = Column(
        DateTime,
        nullable=True,
    )

    # Metadata
    meta_data: Mapped[dict] = Column(
        Text,
        default="{}",
        nullable=True,
    )

    @declared_attr.directive
    def __table_args__(self):
        return (
            CheckConstraint("is_active = TRUE OR is_active = FALSE"),
            CheckConstraint("is_superuser = TRUE OR is_superuser = FALSE"),
        )

    def __repr__(self) -> str:
        """
        String representation.
        """
        return f"<User(username={self.username}, id={self.id})>"

    def to_dict(self) -> dict:
        """
        Get user as dictionary.
        """
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "username": self.username,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "is_verified": self.is_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ===============================
# ROLE MODEL
# ===============================


class Role(GUIDMixin, TimestampMixin, Base):
    """
    Role model.

    Represents a role (admin, user, etc.).
    """

    __tablename__ = "roles"

    name: Mapped[str] = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=True,
    )
    permissions: Mapped[dict] = Column(
        Text,
        default="{}",
        nullable=True,
    )


# ===============================
# USER-ROLE RELATIONSHIP
# ===============================


class UserRole(Base):
    """
    User-Role relationship model.

    Links users to roles.
    """

    __tablename__ = "user_roles"

    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    role_id: Mapped[str] = Column(
        String(36),
        ForeignKey("roles.id"),
        primary_key=True,
        nullable=False,
    )
    granted_at: Mapped[datetime] = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    granted_by: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )


# ===============================
# PERMISSION MODEL
# ===============================


class Permission(GUIDMixin, TimestampMixin, Base):
    """
    Permission model.

    Represents a permission (read, write, delete, etc.).
    """

    __tablename__ = "permissions"

    name: Mapped[str] = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = Column(
        Text,
        nullable=True,
    )
    resource: Mapped[str] = Column(
        String(100),
        nullable=True,
    )


# ===============================
# USER-PERMISSION RELATIONSHIP
# ===============================


class UserPermission(Base):
    """
    User-Permission relationship model.

    Links users to permissions.
    """

    __tablename__ = "user_permissions"

    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    permission_id: Mapped[str] = Column(
        String(36),
        ForeignKey("permissions.id"),
        primary_key=True,
        nullable=False,
    )
