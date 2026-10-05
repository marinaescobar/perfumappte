"""Caché de imágenes: descarga bajo demanda (sin bloquear la interfaz) y guarda en ./images."""
import os
from collections import OrderedDict, deque
from PyQt6.QtCore import QObject, QUrl, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
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

WHITE_MIN = 244            # un píxel cuenta como fondo si sus tres canales llegan a este valor (blanco o casi)
MIN_KEPT = 0.22            # fracción mínima de la imagen que debe quedar tras quitar el fondo
MASK_W, MASK_H = 120, 160  # la máscara del fondo se calcula en pequeño (rápido en Python) y se amplía suavizada

def remove_white(pm):
    """Quita el fondo blanco de la foto: lo que es casi blanco y está conectado con los bordes pasa a transparente (los blancos del interior del frasco se respetan)."""
    small = pm.toImage().scaled(MASK_W, MASK_H, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation).convertToFormat(QImage.Format.Format_RGB32)
    w, h = small.width(), small.height(); raw = bytes(small.constBits().asarray(small.sizeInBytes())); bpl = small.bytesPerLine()
    def white(x, y): i = y * bpl + x * 4; return raw[i] >= WHITE_MIN and raw[i + 1] >= WHITE_MIN and raw[i + 2] >= WHITE_MIN
    bg = bytearray(w * h); q = deque()
    for x in range(w): q.extend(((x, 0), (x, h - 1)))
    for y in range(h): q.extend(((0, y), (w - 1, y)))
    while q:
        x, y = q.popleft()
        if 0 <= x < w and 0 <= y < h and not bg[y * w + x] and white(x, y):
            bg[y * w + x] = 1; q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    keep = 1 - sum(bg) / (w * h)
    if keep > 0.97 or keep < MIN_KEPT: return pm            # no había fondo, o el frasco es casi blanco y se confunde con él: se deja la foto como está
    mask = QImage(w, h, QImage.Format.Format_Alpha8)
    for y in range(h):
        row = mask.scanLine(y); row.setsize(mask.bytesPerLine()); row[0:w] = bytes(0 if bg[y * w + x] else 255 for x in range(w))
    big = mask.scaled(pm.width(), pm.height(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    img = pm.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied); p = QPainter(img)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn); p.drawImage(0, 0, big); p.end()
    return QPixmap.fromImage(img)

def enabled():
    from core import db
    return db.get_meta("remove_white_bg") != "0"

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
        if enabled(): pm = remove_white(pm)
        s.mem[key] = pm
        while len(s.mem) > 400: s.mem.popitem(last=False)
        return pm
    def _pump(s):
        while s.queue and len(s.active) < 6:
            key, url = s.queue.pop(0); s.active.add(key)
            req = QNetworkRequest(QUrl(url)); req.setRawHeader(b"User-Agent", b"Mozilla/5.0 Perfumappte"); req.setRawHeader(b"Referer", b"https://www.fragrantica.com/")
            req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            rep = s.nam.get(req); s.reps.add(rep); rep.finished.connect(lambda key=key, rep=rep: s._done(key, rep))
    def clear_mem(s): s.mem.clear()                    # al cambiar el ajuste del fondo: se vuelven a preparar desde los archivos
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
