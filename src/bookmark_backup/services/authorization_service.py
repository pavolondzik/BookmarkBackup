from bookmark_backup.db.models import User


class AuthorizationService:
    @staticmethod
    def get_allowed_modules(user: User) -> list[str]:
        """Return a unique list of module names allowed for this user."""
        allowed = set()
        for role in user.roles:
            for permission in role.permissions:
                allowed.add(permission.module.name)
        return sorted(list(allowed))

    @staticmethod
    def is_authorized(user: User, module_name: str, action: str) -> bool:
        """Check if the user has a specific permission."""
        for role in user.roles:
            for permission in role.permissions:
                return permission.module.name == module_name and permission.action == action
        return False

    def check_access(self, user: User, module_name: str, action: str) -> None:
        """
        Validates access.

        Raises:
            PermissionError: If the action is not allowed.
        """
        if not self.is_authorized(user, module_name, action):
            raise PermissionError(
                f"Access to action '{action}' in module '{module_name}' is not allowed."
            )