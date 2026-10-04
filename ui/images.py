"""Caché de imágenes: descarga bajo demanda (sin bloquear la interfaz) y guarda en ./images."""
import os
from collections import OrderedDict
from PyQt6.QtCore import QObject, QUrl, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from core.paths import app_dir

# Si el JSONL no trae URL de imagen se construye con el id de Fragrantica. Puedes cambiarlo con la variable PERFUMAPP_IMG_URL.
TEMPLATE = os.environ.get("PERFUMAPP_IMG_URL", "https://fimgs.net/mdimg/perfume/375x500.{id}.jpg")

def src(d):
    """(clave de caché, url) de un perfume; (None, None) si no hay forma de obtener imagen."""
    eid, url = d.get("ext_id"), d.get("image_url")
    if eid: return str(eid), url or TEMPLATE.format(id=eid)
    if url and d.get("id"): return f"u{d['id']}", url
    return None, None

class ImageCache(QObject):
    loaded = pyqtSignal(str)
    def __init__(s):
        super().__init__(); s.nam = QNetworkAccessManager(s); s.mem = OrderedDict(); s.queue = []; s.active = set(); s.failed = set(); s.reps = set()
        s.dir = os.path.join(app_dir(), "images"); os.makedirs(s.dir, exist_ok=True)
    def path(s, key): return os.path.join(s.dir, f"{key}.jpg")
    def get(s, key, url):
        """Pixmap (miniatura) o None; si falta, encola la descarga."""
        if key in s.mem: s.mem.move_to_end(key); return s.mem[key]
        p = s.path(key)
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull(): return s._put(key, pm)
        if url and key not in s.failed and key not in s.active and all(k != key for k, _ in s.queue):
            s.queue.append((key, url)); s._pump()
        return None
    def _put(s, key, pm):
        pm = pm.scaled(240, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        s.mem[key] = pm
        while len(s.mem) > 400: s.mem.popitem(last=False)
        return pm
    def _pump(s):
        while s.queue and len(s.active) < 6:
            key, url = s.queue.pop(0); s.active.add(key)
            req = QNetworkRequest(QUrl(url)); req.setRawHeader(b"User-Agent", b"Mozilla/5.0 Perfumappte"); req.setRawHeader(b"Referer", b"https://www.fragrantica.com/")
            req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            rep = s.nam.get(req); s.reps.add(rep); rep.finished.connect(lambda key=key, rep=rep: s._done(key, rep))
    def abort_all(s):
        """Al cerrar la app: cancela las descargas en curso para no cerrar con peticiones de red vivas."""
        s.queue.clear()
        for rep in list(s.reps): rep.abort()
        s.mem.clear()                      # los QPixmap no pueden sobrevivir a la QApplication
    def _done(s, key, rep):
        s.reps.discard(rep); s.active.discard(key); ok = rep.error() == QNetworkReply.NetworkError.NoError; data = bytes(rep.readAll()) if ok else b""; rep.deleteLater()
        pm = QPixmap()
        if data and pm.loadFromData(data):
            with open(s.path(key), "wb") as f: f.write(data)
            s._put(key, pm); s.loaded.emit(key)
        else: s.failed.add(key)
        s._pump()

_cache = None
def get_cache():
    global _cache
    if _cache is None: _cache = ImageCache()
    return _cache
