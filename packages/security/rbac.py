"""
Role-Based Access Control (RBAC) implementation.

Manages roles, permissions, and authorization decisions.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from apps.api.core.config import settings

logger = logging.getLogger(__name__)


# ===============================
# PERMISSION CONSTANTS
# ===============================


class PermissionType(str, Enum):
    """
    Permission type constants.
    """

    # Resource operations
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    EXECUTE = "execute"
    ADMIN = "admin"

    # Resource types
    USER = "user"
    WORKFLOW = "workflow"
    EXECUTION = "execution"
    EVENT = "event"
    METRIC = "metric"
    AUDIT = "audit"

    # Combined permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_CREATE = "user:create"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"

    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_ADMIN = "workflow:admin"

    EXECUTION_READ = "execution:read"
    EXECUTION_WRITE = "execution:write"
    EXECUTION_CREATE = "execution:create"
    EXECUTION_DELETE = "execution:delete"
    EXECUTION_ADMIN = "execution:admin"


# ===============================
# ROLE DEFINITIONS
# ===============================


def get_default_roles() -> Dict[str, Dict[str, Any]]:
    """
    Get default role definitions.

    Returns:
        Dictionary of role definitions
    """
    return {
        "admin": {
            "name": "admin",
            "description": "System administrator with full access",
            "permissions": PermissionType.ADMIN.value,
            "resources": ["*"],
        },
        "superuser": {
            "name": "superuser",
            "description": "Superuser with elevated permissions",
            "permissions": [
                PermissionType.USER_ADMIN.value,
                PermissionType.WORKFLOW_ADMIN.value,
                PermissionType.EXECUTION_ADMIN.value,
            ],
            "resources": ["*"],
        },
        "user": {
            "name": "user",
            "description": "Regular user with basic permissions",
            "permissions": [
                PermissionType.READ.value,
                PermissionType.WRITE.value,
            ],
            "resources": ["user", "workflow", "execution"],
        },
        "developer": {
            "name": "developer",
            "description": "Developer with workflow creation permissions",
            "permissions": [
                PermissionType.READ.value,
                PermissionType.CREATE.value,
                PermissionType.EXECUTE.value,
            ],
            "resources": ["user", "workflow", "execution", "event"],
        },
        "analyst": {
            "name": "analyst",
            "description": "Analyst with read-only analytics access",
            "permissions": [
                PermissionType.READ.value,
                PermissionType.EXECUTE.value,
            ],
            "resources": ["user", "workflow", "execution", "event", "metric"],
        },
        "viewer": {
            "name": "viewer",
            "description": "Viewer with read-only access",
            "permissions": [PermissionType.READ.value],
            "resources": ["user", "workflow", "execution"],
        },
        "support": {
            "name": "support",
            "description": "Support user with limited permissions",
            "permissions": [
                PermissionType.READ.value,
                PermissionType.EXECUTE.value,
            ],
            "resources": ["user"],
        },
    }


def get_role_permissions(
    role_name: str,
) -> List[str]:
    """
    Get permissions for role.

    Args:
        role_name: Role name

    Returns:
        List of permission strings
    """
    roles = get_default_roles()

    if role_name not in roles:
        logger.warning(f"Unknown role: {role_name}")
        return []

    role = roles[role_name]

    # Expand permission strings
    permissions: List[str] = []

    for perm in role.get("permissions", []):
        if ":" in perm:
            # Expand combined permission (e.g., "user:read" -> "user:read")
            permissions.append(perm)
        else:
            # Expand base permission to all resources
            for resource in role.get("resources", []):
                if resource == "*":
                    # Admin can access all resources
                    permissions.append(f"{resource}:{perm}")
                else:
                    permissions.append(f"{resource}:{perm}")

    return permissions


def get_resource_permissions(
    resource: str,
    permission: str,
) -> Set[str]:
    """
    Get resource-specific permissions.

    Args:
        resource: Resource name
        permission: Permission name

    Returns:
        Set of permission strings for resource
    """
    permissions: Set[str] = set()

    # Get role permissions
    role_perms = get_role_permissions("user")

    for perm in role_perms:
        if perm.endswith(f":{permission}") or perm.endswith(":read"):
            permissions.add(perm)

    return permissions


# ===============================
# ROLE MANAGEMENT
# ===============================


class RoleManager:
    """
    Role manager for RBAC operations.
    """

    def __init__(self):
        """
        Initialize role manager.
        """
        self._roles: Dict[str, Dict[str, Any]] = {}
        self._load_default_roles()

    def _load_default_roles(self) -> None:
        """
        Load default roles.
        """
        self._roles.update(get_default_roles())

    def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str],
        resources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create role.

        Args:
            name: Role name
            description: Role description
            permissions: List of permissions
            resources: List of resources

        Returns:
            Created role
        """
        if name in self._roles:
            logger.warning(f"Role already exists: {name}")
            return None

        role = {
            "name": name,
            "description": description,
            "permissions": permissions,
            "resources": resources or [],
        }

        self._roles[name] = role

        logger.info(f"Role created: {name}")
        return role

    def update_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        resources: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update role.

        Args:
            name: Role name
            description: New description
            permissions: New permissions
            resources: New resources

        Returns:
            Updated role or None
        """
        if name not in self._roles:
            logger.warning(f"Role not found: {name}")
            return None

        role = self._roles[name]

        if description is not None:
            role["description"] = description

        if permissions is not None:
            role["permissions"] = permissions

        if resources is not None:
            role["resources"] = resources

        logger.info(f"Role updated: {name}")
        return role

    def delete_role(
        self,
        name: str,
    ) -> bool:
        """
        Delete role.

        Args:
            name: Role name

        Returns:
            True if deleted
        """
        if name not in self._roles:
            logger.warning(f"Role not found: {name}")
            return False

        del self._roles[name]

        logger.info(f"Role deleted: {name}")
        return True

    def get_role(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get role by name.

        Args:
            name: Role name

        Returns:
            Role definition or None
        """
        return self._roles.get(name)

    def get_roles(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all roles.

        Returns:
            Dictionary of roles
        """
        return self._roles.copy()

    def has_role(
        self,
        name: str,
    ) -> bool:
        """
        Check if role exists.

        Args:
            name: Role name

        Returns:
            True if role exists
        """
        return name in self._roles

    def add_permission(
        self,
        name: str,
        permission: str,
        resource: Optional[str] = None,
    ) -> bool:
        """
        Add permission to role.

        Args:
            name: Role name
            permission: Permission to add
            resource: Resource for permission (optional)

        Returns:
            True if added
        """
        if name not in self._roles:
            logger.warning(f"Role not found: {name}")
            return False

        role = self._roles[name]

        # Format permission
        if resource:
            formatted = f"{resource}:{permission}"
        else:
            formatted = permission

        if formatted not in role["permissions"]:
            role["permissions"].append(formatted)

        logger.info(f"Permission added to role: {name} - {formatted}")
        return True

    def remove_permission(
        self,
        name: str,
        permission: str,
        resource: Optional[str] = None,
    ) -> bool:
        """
        Remove permission from role.

        Args:
            name: Role name
            permission: Permission to remove
            resource: Resource for permission (optional)

        Returns:
            True if removed
        """
        if name not in self._roles:
            logger.warning(f"Role not found: {name}")
            return False

        role = self._roles[name]

        # Format permission
        if resource:
            formatted = f"{resource}:{permission}"
        else:
            formatted = permission

        if formatted in role["permissions"]:
            role["permissions"].remove(formatted)
            logger.info(f"Permission removed from role: {name} - {formatted}")
            return True

        return False


# ===============================
# AUTHORIZATION
# ===============================


class Authorizer:
    """
    Authorizer for authorization decisions.
    """

    def __init__(
        self,
        roles_manager: Optional[RoleManager] = None,
    ):
        """
        Initialize authorizer.

        Args:
            roles_manager: Role manager instance
        """
        self.roles_manager = roles_manager or RoleManager()

    def has_permission(
        self,
        user_role: str,
        resource: str,
        action: str,
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user_role: User's role name
            resource: Resource name
            action: Action (read, write, delete, etc.)

        Returns:
            True if user has permission
        """
        # Normalize action
        action = action.lower()

        # Check if user has any permission for this resource
        permissions = get_role_permissions(user_role)

        for perm in permissions:
            # Check if permission matches resource:action
            if f"{resource}:{action}" in perm or f"{action}" in perm:
                return True

        return False

    def check_authorization(
        self,
        user_role: str,
        resource: str,
        action: str,
    ) -> Dict[str, Any]:
        """
        Check authorization and return result.

        Args:
            user_role: User's role name
            resource: Resource name
            action: Action

        Returns:
            Authorization result
        """
        has_permission = self.has_permission(user_role, resource, action)

        return {
            "allowed": has_permission,
            "user_role": user_role,
            "resource": resource,
            "action": action,
        }

    def check_admin(
        self,
        user_role: str,
    ) -> bool:
        """
        Check if user is admin.

        Args:
            user_role: User's role name

        Returns:
            True if admin
        """
        return user_role in ("admin", "superuser")

    def check_write(
        self,
        user_role: str,
    ) -> bool:
        """
        Check if user can write.

        Args:
            user_role: User's role name

        Returns:
            True if write allowed
        """
        permissions = get_role_permissions(user_role)

        for perm in permissions:
            if perm.endswith(":write") or perm.endswith(":create"):
                return True

        return False

    def check_delete(
        self,
        user_role: str,
    ) -> bool:
        """
        Check if user can delete.

        Args:
            user_role: User's role name

        Returns:
            True if delete allowed
        """
        permissions = get_role_permissions(user_role)

        for perm in permissions:
            if perm.endswith(":delete"):
                return True

        return False

    def check_read(
        self,
        user_role: str,
    ) -> bool:
        """
        Check if user can read.

        Args:
            user_role: User's role name

        Returns:
            True if read allowed
        """
        permissions = get_role_permissions(user_role)

        for perm in permissions:
            if perm.endswith(":read"):
                return True

        return False

    def get_allowed_actions(
        self,
        user_role: str,
        resource: str,
    ) -> List[str]:
        """
        Get allowed actions for user on resource.

        Args:
            user_role: User's role name
            resource: Resource name

        Returns:
            List of allowed actions
        """
        permissions = get_role_permissions(user_role)
        actions: List[str] = []

        for perm in permissions:
            if f"{resource}:" in perm or perm == "*:*":
                # Extract action
                parts = perm.split(":")
                if len(parts) == 2:
                    actions.append(parts[1])

        return actions


# ===============================
# FACTORY
# ===============================


def create_role_manager() -> RoleManager:
    """
    Create role manager.

    Returns:
        RoleManager instance
    """
    return RoleManager()


def create_authorizer(
    roles_manager: Optional[RoleManager] = None,
) -> Authorizer:
    """
    Create authorizer.

    Args:
        roles_manager: Role manager instance

    Returns:
        Authorizer instance
    """
    return Authorizer(roles_manager)
