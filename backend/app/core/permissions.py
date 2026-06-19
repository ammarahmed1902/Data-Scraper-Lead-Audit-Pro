"""
Role-based permission system.
Defines granular permissions and role-to-permission mappings.
"""

from enum import Enum

from app.core.security import ROLE_HIERARCHY, UserRole


class Permission(str, Enum):
    # User management
    USERS_LIST = "users:list"
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Websites (Phase 03)
    WEBSITES_LIST = "websites:list"
    WEBSITES_CREATE = "websites:create"
    WEBSITES_UPDATE = "websites:update"
    WEBSITES_DELETE = "websites:delete"

    # Audits (Phase 04)
    AUDITS_RUN = "audits:run"
    AUDITS_VIEW = "audits:view"
    AUDITS_CANCEL = "audits:cancel"

    # Reports & exports (Phase 05)
    REPORTS_GENERATE = "reports:generate"
    REPORTS_DOWNLOAD = "reports:download"
    EXPORTS_CREATE = "exports:create"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"

    # System
    SYSTEM_ADMIN = "system:admin"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.SUPER_ADMIN: set(Permission),
    UserRole.ADMIN: {
        Permission.USERS_LIST,
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.WEBSITES_LIST,
        Permission.WEBSITES_CREATE,
        Permission.WEBSITES_UPDATE,
        Permission.WEBSITES_DELETE,
        Permission.AUDITS_RUN,
        Permission.AUDITS_VIEW,
        Permission.AUDITS_CANCEL,
        Permission.REPORTS_GENERATE,
        Permission.REPORTS_DOWNLOAD,
        Permission.EXPORTS_CREATE,
        Permission.ANALYTICS_VIEW,
    },
    UserRole.MANAGER: {
        Permission.USERS_READ,
        Permission.WEBSITES_LIST,
        Permission.WEBSITES_CREATE,
        Permission.WEBSITES_UPDATE,
        Permission.WEBSITES_DELETE,
        Permission.AUDITS_RUN,
        Permission.AUDITS_VIEW,
        Permission.AUDITS_CANCEL,
        Permission.REPORTS_GENERATE,
        Permission.REPORTS_DOWNLOAD,
        Permission.EXPORTS_CREATE,
        Permission.ANALYTICS_VIEW,
    },
    UserRole.ANALYST: {
        Permission.WEBSITES_LIST,
        Permission.WEBSITES_CREATE,
        Permission.AUDITS_RUN,
        Permission.AUDITS_VIEW,
        Permission.REPORTS_GENERATE,
        Permission.REPORTS_DOWNLOAD,
        Permission.EXPORTS_CREATE,
        Permission.ANALYTICS_VIEW,
    },
    UserRole.VIEWER: {
        Permission.WEBSITES_LIST,
        Permission.AUDITS_VIEW,
        Permission.REPORTS_DOWNLOAD,
        Permission.ANALYTICS_VIEW,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def can_assign_role(actor_role: UserRole, target_role: UserRole) -> bool:
    """Determine if actor can assign target_role to another user."""
    if actor_role == UserRole.SUPER_ADMIN:
        return True
    if actor_role == UserRole.ADMIN:
        return target_role in {
            UserRole.MANAGER,
            UserRole.ANALYST,
            UserRole.VIEWER,
        }
    return False


def can_modify_user(actor_role: UserRole, target_role: UserRole) -> bool:
    """Determine if actor can modify a user with target_role."""
    if actor_role == UserRole.SUPER_ADMIN:
        return True
    if actor_role == UserRole.ADMIN:
        return ROLE_HIERARCHY[target_role] < ROLE_HIERARCHY[UserRole.ADMIN]
    return False
