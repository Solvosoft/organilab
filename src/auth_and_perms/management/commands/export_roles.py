import json
import textwrap
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand

from auth_and_perms.models import Rol
from auth_and_perms.roles import ROLES

OUTPUT = Path(settings.BASE_DIR) / "auth_and_perms" / "management" / "roles.py"

HEADER = '''ROOT_ORGANIZATION = "UNA"

ROLE_DEFINITIONS = {
'''


def format_role(key, name, description, permissions):
    parts = textwrap.wrap(description, 90, drop_whitespace=False) or [""]
    lines = [
        "    %s: {" % json.dumps(key),
        "        \"name\": %s," % json.dumps(name, ensure_ascii=False),
    ]
    if len(parts) == 1:
        lines.append("        \"description\": %s," % json.dumps(parts[0], ensure_ascii=False))
    else:
        lines.append("        \"description\": (")
        lines += ["            %s" % json.dumps(part, ensure_ascii=False) for part in parts]
        lines.append("        ),")
    lines.append("        \"permissions\": [")
    lines += ["            %s," % json.dumps(p) for p in sorted(permissions)]
    lines += ["        ],", "    },"]
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Write auth_and_perms/management/roles.py from the roles in the database"

    def add_arguments(self, parser):
        parser.add_argument("--output", default=str(OUTPUT))

    def role_block(self, key, rol):
        permissions = rol.permissions.values_list("content_type__app_label", "codename")
        return format_role(key, rol.name, rol.description or "", ["%s.%s" % p for p in permissions])

    def handle(self, *args, **options):
        blocks, missing = [], []
        for key, name in ROLES.items():
            rol = Rol.objects.filter(name=name).order_by("pk").first()
            if rol is None:
                missing.append(name)
                continue
            blocks.append(self.role_block(key, rol))
        Path(options["output"]).write_text(HEADER + "\n".join(blocks) + "\n}\n", encoding="utf-8")
        self.stdout.write("%s: %d roles" % (options["output"], len(blocks)))
        for name in missing:
            self.stdout.write(self.style.WARNING("Rol '%s' no existe en la base: no se exporta" % name))
