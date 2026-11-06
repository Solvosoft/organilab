from auth_and_perms.management.roles import ROLE_DEFINITIONS, ROOT_ORGANIZATION

ROLES = {key: role["name"] for key, role in ROLE_DEFINITIONS.items()}

__all__ = ["ROLES", "ROLE_DEFINITIONS", "ROOT_ORGANIZATION"]
