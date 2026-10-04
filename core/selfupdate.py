"""Nuevas versiones de la propia aplicación: consulta las Releases de GitHub, descarga el instalador y lo lanza en modo silencioso.

No depende de Qt. Las funciones de red lanzan `UpdateError` con un código corto ("net", "notfound", "ratelimit", "http500", "asset", "hash"…)
que la interfaz traduce. Solo se descargan instaladores de github.com / githubusercontent.com (https) y, si la Release trae la huella SHA-256
del archivo, se comprueba antes de ejecutarlo.
"""
import hashlib, json, os, re, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass
from core import db
from core.version import GITHUB_REPO, VERSION

API = os.environ.get("PERFUMAPP_RELEASES_API") or "https://api.github.com/repos/{repo}/releases"      # la variable sirve para pruebas
CHECK_EVERY = 24 * 3600                                  # como mucho una comprobación automática al día
TRUSTED_HOSTS = ("github.com", "githubusercontent.com")


class UpdateError(Exception):
    """El mensaje es un código corto; ver ui/versions.py para sus textos."""


@dataclass
class Release:
    version: str                    # «1.2.0» (sin la «v» de la etiqueta)
    name: str
    notes: str                      # Markdown tal como se escribió en GitHub
    page: str                       # URL de la Release
    published: str                  # fecha ISO
    asset_name: str = ""
    asset_url: str = ""
    asset_size: int = 0
    sha256: str = ""


def configured():
    """¿Hay un repositorio real configurado? (si no, no se busca nada)"""
    return bool(re.fullmatch(r"[\w.-]+/[\w.-]+", GITHUB_REPO or "")) and not GITHUB_REPO.upper().startswith("TU_USUARIO")

def parse_version(v):
    nums = re.findall(r"\d+", str(v)); return tuple(int(n) for n in nums[:4]) or (0,)

def is_newer(latest, current=VERSION):
    return parse_version(latest) > parse_version(current)

def releases_page():
    return f"https://github.com/{GITHUB_REPO}/releases"


# ------------------------------------------------------------------ consulta
def _get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": f"Perfumappte/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise UpdateError("notfound" if e.code == 404 else "ratelimit" if e.code in (403, 429) else f"http{e.code}") from e
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise UpdateError("net") from e
    except ValueError as e:
        raise UpdateError("badjson") from e

def _to_release(o):
    asset = next((a for a in o.get("assets") or [] if re.search(r"setup.*\.exe$", a.get("name", ""), re.I)), None) or {}
    digest = asset.get("digest") or ""
    return Release(version=str(o.get("tag_name") or "").lstrip("vV"), name=o.get("name") or o.get("tag_name") or "", notes=o.get("body") or "",
                   page=o.get("html_url") or releases_page(), published=(o.get("published_at") or "")[:10], asset_name=asset.get("name", ""),
                   asset_url=asset.get("browser_download_url", ""), asset_size=int(asset.get("size") or 0),
                   sha256=digest.split(":", 1)[1].lower() if digest.lower().startswith("sha256:") else "")

def releases(n=8):
    """Las últimas Releases publicadas (sin borradores ni prelanzamientos), la más nueva primero."""
    if not configured(): raise UpdateError("notconfigured")
    data = _get_json(API.format(repo=GITHUB_REPO) + f"?per_page={int(n)}")
    return [_to_release(o) for o in data if isinstance(o, dict) and not o.get("draft") and not o.get("prerelease")]

def newest(rels):
    """La Release más nueva que la instalada (o None)."""
    best = max(rels, key=lambda r: parse_version(r.version), default=None)
    return best if best and is_newer(best.version) else None

def due():
    try: last = float(db.get_meta("last_version_check", 0) or 0)
    except ValueError: last = 0
    return time.time() - last > CHECK_EVERY

def mark_checked(): db.set_meta("last_version_check", time.time())
def skipped(): return db.get_meta("skip_version", "")
def skip(version): db.set_meta("skip_version", version)


# ------------------------------------------------------------------ descarga e instalación
def _check_url(url):
    p = urllib.parse.urlparse(url)
    if API != "https://api.github.com/repos/{repo}/releases": return                       # pruebas con un servidor local
    if p.scheme != "https" or not any(p.hostname == h or (p.hostname or "").endswith("." + h) for h in TRUSTED_HOSTS): raise UpdateError("untrusted")

def download(rel, progress=lambda done, total: None):
    """Descarga el instalador de la Release a una carpeta temporal y devuelve su ruta (comprobando tamaño y SHA-256 si se conocen)."""
    if not rel.asset_url: raise UpdateError("asset")
    _check_url(rel.asset_url)
    folder = os.path.join(tempfile.gettempdir(), "Perfumappte-update"); os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, re.sub(r"[^\w.-]", "_", rel.asset_name or f"Perfumappte-Setup-{rel.version}.exe"))
    req = urllib.request.Request(rel.asset_url, headers={"User-Agent": f"Perfumappte/{VERSION}"}); h = hashlib.sha256(); done = 0
    try:
        with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
            total = int(r.headers.get("Content-Length") or rel.asset_size or 0)
            while True:
                chunk = r.read(256 * 1024)
                if not chunk: break
                f.write(chunk); h.update(chunk); done += len(chunk); progress(done, total)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise UpdateError("net") from e
    if rel.asset_size and done != rel.asset_size: raise UpdateError("size")
    if rel.sha256 and h.hexdigest().lower() != rel.sha256: raise UpdateError("hash")
    return path

def install(path):
    """Lanza el instalador sin ventanas de preguntas; conserva los datos y vuelve a abrir la app al terminar. La app debe cerrarse justo después."""
    if not sys.platform.startswith("win"): raise UpdateError("platform")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", "/CLOSEAPPLICATIONS", "/RELAUNCH=1"], close_fds=True, creationflags=flags)
