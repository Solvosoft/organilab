#!/usr/bin/env python
"""Verifica que el entorno pueda correr la suite (incluida la de Selenium).

Se ejecuta con el python del entorno virtual (`make check-env`). No importa
Django settings: solo comprueba que estén las piezas que hacen fallar una
corrida de Selenium *antes* de esperar 20 minutos a que reviente en setUpClass.
"""
import importlib
import os
import shutil
import subprocess
import sys

OK = "  OK   "
BAD = " FALLA "

errors = []
warnings = []


def report(ok, label, detail=""):
    print(f"[{OK if ok else BAD}] {label}{(' — ' + detail) if detail else ''}")


def check_module(module, label=None, attr="__version__", required=True):
    label = label or module
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - queremos el motivo textual
        report(False, label, str(exc))
        (errors if required else warnings).append(f"falta el módulo {module}")
        return None
    version = getattr(mod, attr, "")
    if module == "django":
        version = mod.get_version()
    report(True, label, str(version))
    return mod


def check_binary(name, env_var=None, default=None, required=True):
    path = os.getenv(env_var) if env_var else None
    path = path or default or shutil.which(name)
    ok = bool(path) and os.path.exists(path) and os.access(path, os.X_OK)
    report(ok, name, path or "no encontrado")
    if not ok:
        (errors if required else warnings).append(f"falta el binario {name}")
    return path if ok else None


def main():
    print(f"python: {sys.executable} ({sys.version.split()[0]})\n")

    print("Dependencias de runtime")
    check_module("django")
    check_module("psycopg")
    check_module("djgentelella", attr="__version__", required=True)
    check_module("celery")

    print("\nDependencias de pruebas")
    check_module("selenium")
    check_module("Screenshot", label="Screenshot (selenium-screenshot)")
    check_module("tblib")  # sin él, --parallel aborta al primer fallo
    check_module("PIL", label="Pillow")

    print("\nBinarios del navegador")
    driver = check_binary("chromedriver", env_var="CHROMEDRIVER_DIR",
                          default="/usr/bin/chromedriver")
    if driver:
        try:
            out = subprocess.run([driver, "--version"], capture_output=True,
                                 text=True, timeout=20)
            print(f"         {out.stdout.strip() or out.stderr.strip()}")
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"chromedriver no respondió a --version: {exc}")
    browser = shutil.which("chromium") or shutil.which("google-chrome") or \
        shutil.which("chromium-browser")
    report(bool(browser), "chromium/google-chrome", browser or "no encontrado")
    if not browser:
        errors.append("falta el navegador (chromium o google-chrome)")
    check_binary("xvfb-run", required=False)

    print("\nBase de datos")
    try:
        import psycopg

        dsn = dict(
            host=os.getenv("DBHOST", "127.0.0.1"),
            port=os.getenv("DBPORT", "5432"),
            user=os.getenv("DBUSER", "organilab_user"),
            password=os.getenv("DBPASSWORD", "0rg4n1l4b"),
            dbname="postgres",
        )
        with psycopg.connect(**dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("select version()")
                report(True, "postgresql", cur.fetchone()[0].split(",")[0])
    except Exception as exc:  # noqa: BLE001
        report(False, "postgresql", str(exc).strip().splitlines()[0])
        errors.append("no se pudo conectar a PostgreSQL")

    print()
    for warning in warnings:
        print(f"aviso: {warning}")
    if errors:
        for error in errors:
            print(f"error: {error}")
        print("\nEntorno incompleto. Corré `make setup`.")
        return 1
    print("Entorno listo para correr las pruebas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
