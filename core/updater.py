"""Descarga semanal de perfumes.jsonl desde Kaggle e importación. Uso sin interfaz: python -m core.updater [--force] [--lang en]"""
import os, sys, time, zipfile, datetime
from core import db, i18n
from core.i18n import tr
from core.paths import app_dir

DATASET, FILE, EVERY_DAYS = "ledecanteur/fragrantica-perfumes", "perfumes.jsonl", 7

def help_text():
    return tr("up.help")

def data_dir():
    d = os.path.join(app_dir(), "data"); os.makedirs(d, exist_ok=True); return d

def has_credentials():
    """¿Hay credenciales de Kaggle? Vale kaggle.json (clave clásica), el archivo access_token (token nuevo) o las variables de entorno."""
    if os.environ.get("KAGGLE_API_TOKEN") or (os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")): return True
    cfg = os.environ.get("KAGGLE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".kaggle")
    return any(os.path.exists(os.path.join(cfg, f)) for f in ("kaggle.json", "access_token"))

def due():
    try: last = float(db.get_meta("last_update", 0) or 0)
    except ValueError: last = 0
    return time.time() - last > EVERY_DAYS * 86400

def status_text():
    last = db.get_meta("last_update")
    if not last: return tr("up.none")
    return tr("up.at", datetime.datetime.fromtimestamp(float(last)).strftime("%d/%m/%Y" if i18n.is_es() else "%x"))

def download(log=lambda m: None):
    try: from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as e: raise RuntimeError(tr("up.nopkg")) from e
    api = KaggleApi()
    try: api.authenticate()
    except Exception as e: raise RuntimeError(tr("up.nocred") + "\n\n" + help_text()) from e
    d = data_dir(); log(tr("up.downloading"))
    api.dataset_download_file(DATASET, FILE, path=d, force=True, quiet=True)
    z = os.path.join(d, FILE + ".zip")
    if os.path.exists(z):
        with zipfile.ZipFile(z) as zf: zf.extract(FILE, d)
        os.remove(z)
    p = os.path.join(d, FILE)
    if not os.path.exists(p): raise RuntimeError(tr("up.nofile") + FILE)
    return p

def update(progress=None, log=lambda m: None):
    """Descarga + importa (upsert por slug: no duplica ni toca tu colección). Devuelve (nuevos, actualizados)."""
    path = download(log); log(tr("up.importing"))
    res = db.import_file(path, progress)
    db.set_meta("last_update", time.time())
    try: os.remove(path)
    except OSError: pass
    return res

if __name__ == "__main__":
    if "--lang" in sys.argv:
        i18n.set_lang(sys.argv[sys.argv.index("--lang") + 1])
    db.init_db()
    if "--force" in sys.argv or due():
        print(tr("db.res") % update(lambda n: print(f"{n:,}"), print))
    else: print(tr("db.uptodate"), "·", status_text())