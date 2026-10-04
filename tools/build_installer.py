"""Genera el instalador de Windows:  python -m tools.build_installer [--no-seed] [--skip-exe] [--seed-from RUTA.db]

Pasos:
  1. Base de datos inicial limpia (build/seed/perfumappte.db): copia la tuya SIN colección, favoritas, claves ni preferencias.
  2. PyInstaller -> build/dist/Perfumappte/  (aplicación en una carpeta, sin consola).
  3. Inno Setup -> dist/Perfumappte-Setup-<versión>.exe  (sin base de datos: la que se publica en GitHub)
     o dist/Perfumappte-Setup-<versión>-con-base-de-datos.exe  (solo para uso personal).
Requisitos: pip install pyinstaller  y  Inno Setup 6 (winget install JRSoftware.InnoSetup).
"""
import argparse, os, shutil, sqlite3, subprocess, sys
from core.paths import PROJECT_ROOT
from core.version import VERSION

BUILD = os.path.join(PROJECT_ROOT, "build")
SEED = os.path.join(BUILD, "seed", "perfumappte.db")
APP_DIST = os.path.join(BUILD, "dist", "Perfumappte")
ISS = os.path.join(PROJECT_ROOT, "installer", "perfumappte.iss")


def step(msg): print(f"\n==> {msg}", flush=True)


def make_seed(source):
    """Copia la base de datos con la API de copia de SQLite (válida aunque la app esté abierta) y borra todo lo personal."""
    os.makedirs(os.path.dirname(SEED), exist_ok=True)
    for ext in ("", "-wal", "-shm"):
        try: os.remove(SEED + ext)
        except OSError: pass
    src, dst = sqlite3.connect(source), sqlite3.connect(SEED)
    src.backup(dst); src.close()
    dst.execute("DELETE FROM collection"); dst.execute("DELETE FROM fav_combos")
    dst.execute("DELETE FROM meta WHERE k NOT IN ('last_update')")        # fuera claves, idioma y preferencias; se conserva la fecha de la descarga
    dst.commit(); dst.execute("PRAGMA journal_mode=DELETE"); dst.execute("VACUUM"); n = dst.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]; dst.close()
    print(f"    {n:,} perfumes · {os.path.getsize(SEED) / 2**20:.0f} MB · sin colección ni claves")


def build_exe():
    shutil.rmtree(os.path.join(BUILD, "dist"), ignore_errors=True)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir", "--name", "Perfumappte",
           "--icon", os.path.join(PROJECT_ROOT, "assets", "icon.ico"), "--add-data", f"{os.path.join(PROJECT_ROOT, 'assets')}{os.pathsep}assets",
           "--collect-all", "kaggle", "--collect-all", "kagglesdk",
           "--exclude-module", "tkinter", "--exclude-module", "matplotlib", "--exclude-module", "pytest",
           "--distpath", os.path.join(BUILD, "dist"), "--workpath", os.path.join(BUILD, "work"), "--specpath", BUILD,
           os.path.join(PROJECT_ROOT, "main.py")]
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    if not os.path.exists(os.path.join(APP_DIST, "Perfumappte.exe")): raise SystemExit("PyInstaller no generó Perfumappte.exe")


def find_iscc():
    found = shutil.which("iscc")
    candidates = [found] if found else []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if base: candidates.append(os.path.join(base, "Inno Setup 6", "ISCC.exe"))
    for c in candidates:
        if c and os.path.exists(c): return c
    raise SystemExit("No encuentro Inno Setup 6. Instálalo con:  winget install JRSoftware.InnoSetup")


def build_setup(with_seed):
    cmd = [find_iscc(), f"/DAppVersion={VERSION}", f"/DSourceDir={APP_DIST}"] + ([f"/DSeedDb={SEED}"] if with_seed else []) + [ISS]
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
    out = os.path.join(PROJECT_ROOT, "dist", f"Perfumappte-Setup-{VERSION}{'-con-base-de-datos' if with_seed else ''}.exe")
    print(f"\nInstalador listo: {out}  ({os.path.getsize(out) / 2**20:.0f} MB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-seed", action="store_true", help="no incluir la base de datos (la app tendrá que descargarla de Kaggle)")
    ap.add_argument("--skip-exe", action="store_true", help="reutilizar build/dist sin volver a ejecutar PyInstaller")
    ap.add_argument("--seed-from", default=os.path.join(PROJECT_ROOT, "perfumappte.db"), help="base de datos de la que sale la inicial")
    a = ap.parse_args()
    if not a.no_seed: step("Base de datos inicial limpia"); make_seed(a.seed_from)
    if not a.skip_exe: step("Empaquetando con PyInstaller"); build_exe()
    step("Creando el instalador con Inno Setup"); build_setup(not a.no_seed)


if __name__ == "__main__":
    main()
