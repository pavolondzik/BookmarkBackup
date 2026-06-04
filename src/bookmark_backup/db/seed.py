from sqlalchemy import select
from sqlalchemy.orm import Session
from bookmark_backup.db.models import Module, Permission, Role, User, SystemRole, SystemModule
from bookmark_backup.services.authentication_service import hash_password

# 1. Define the system capabilities (Modules and Actions)
APP_PERMISSIONS = {
    SystemModule.BOOKMARKS: {
        "description": "Management of individual bookmark entries",
        "actions": ["view", "import", "create", "edit", "delete", "reorder"]
    },
    SystemModule.FOLDERS: {
        "description": "Management of the folder hierarchy",
        "actions": ["view", "create", "rename", "delete", "reorder"]
    },
    SystemModule.ADMINISTRATION: {
        "description": "Site administration: users, roles, and permissions",
        "actions": ["view", "manage"]
    },
}

DEFAULT_ADMIN_EMAIL = "administrator@bookmarkbackup.com"
DEFAULT_ADMIN_PASSWORD = "Administrator"


# 2. Define how these permissions map to default roles
# Wildcard '*' can be used for all actions in a module
DEFAULT_ROLES = {
    SystemRole.ADMINISTRATOR: {
        SystemModule.BOOKMARKS: ["*"],
        SystemModule.FOLDERS: ["*"],
        SystemModule.ADMINISTRATION: ["*"],
    },
    SystemRole.EDITOR: {
        SystemModule.BOOKMARKS: ["*"],
        SystemModule.FOLDERS: ["*"],
    },
    SystemRole.VIEWER: {
        SystemModule.BOOKMARKS: ["view"],
        SystemModule.FOLDERS: ["view"],
    }
}

def seed_permissions(session: Session):
    """Idempotently seed modules, permissions, and default roles."""
    permission_map: dict[tuple[str, str], Permission] = {}

    for mod_name, info in APP_PERMISSIONS.items():
        module = session.scalar(select(Module).where(Module.name == mod_name))
        if not module:
            module = Module(name=mod_name, description=info["description"])
            session.add(module)
            session.flush()
        else:
            module.description = info["description"]

        existing_perms = {p.action: p for p in module.permissions}

        for action in info["actions"]:
            if action not in existing_perms:
                perm = Permission(
                    module_id=module.id,
                    action=action,
                    description=f"Can {action} in {mod_name}"
                )
                session.add(perm)
                permission_map[(mod_name, action)] = perm
            else:
                permission_map[(mod_name, action)] = existing_perms[action]

    session.flush()

    for role_name, modules_map in DEFAULT_ROLES.items():
        role = session.scalar(select(Role).where(Role.name == role_name))
        if not role:
            role = Role(name=role_name)
            session.add(role)
        
        assigned_permissions = []
        for mod_name, actions in modules_map.items():
            if actions == ["*"]:
                target_actions = APP_PERMISSIONS[mod_name]["actions"]
            else:
                target_actions = actions
            
            for action in target_actions:
                perm = permission_map.get((mod_name, action))
                if perm:
                    assigned_permissions.append(perm)
        
        role.permissions = assigned_permissions
    
    # 3. Seed default Administrator user
    admin_email = DEFAULT_ADMIN_EMAIL
    admin_user = session.scalar(select(User).where(User.email == admin_email))
    if not admin_user:
        admin_user = User(
            email=admin_email,
            password=hash_password(DEFAULT_ADMIN_PASSWORD),
        )
        session.add(admin_user)
        session.flush()

    admin_role = session.scalar(select(Role).where(Role.name == SystemRole.ADMINISTRATOR))
    if admin_role and admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)

    session.commit()