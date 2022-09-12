all_actions = ["add", "change", "delete", "view"]
all_models = ["account"]

admin_perms = [f"{a}_{m}" for a in all_actions for m in all_models]
content_perms = admin_perms
editor_perms = admin_perms

PERMISSIONS = {
    "admin": admin_perms,
    "content-admin": content_perms,
    "editor": [],
    "manager": []
}
