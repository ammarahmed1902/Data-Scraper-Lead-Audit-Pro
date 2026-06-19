"""Permission system tests."""

from app.core.permissions import Permission, can_assign_role, can_modify_user, has_permission
from app.core.security import UserRole


def test_super_admin_has_all_permissions():
    for perm in Permission:
        assert has_permission(UserRole.SUPER_ADMIN, perm)


def test_viewer_limited_permissions():
    assert has_permission(UserRole.VIEWER, Permission.WEBSITES_LIST)
    assert not has_permission(UserRole.VIEWER, Permission.USERS_CREATE)


def test_admin_can_assign_manager():
    assert can_assign_role(UserRole.ADMIN, UserRole.MANAGER)


def test_admin_cannot_assign_super_admin():
    assert not can_assign_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)


def test_admin_can_modify_viewer():
    assert can_modify_user(UserRole.ADMIN, UserRole.VIEWER)


def test_admin_cannot_modify_super_admin():
    assert not can_modify_user(UserRole.ADMIN, UserRole.SUPER_ADMIN)
