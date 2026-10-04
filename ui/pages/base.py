"""Base común de las páginas con lista de tarjetas de perfumes."""
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QMenu, QVBoxLayout, QWidget
from core import db
from core.i18n import tr
from ui.cards import CardList
from ui.theme import MUTED


class PerfumeListPage(QWidget):
    """Base de las páginas que muestran una lista de tarjetas de perfumes (Mi colección y Descubrimientos): título, tarjetas, pie
    informativo y las acciones comunes (añadir a propiedad o a deseados desde la tarjeta, menú contextual y abrir el perfil)."""
    open_profile = pyqtSignal(int)
    changed = pyqtSignal()                       # la colección cambió: la ventana principal refresca la página visible
    MAX_ROWS = 500

    def __init__(s, cols=None):
        super().__init__()
        s.root = QVBoxLayout(s); s.root.setContentsMargins(26, 22, 26, 16); s.root.setSpacing(8)
        s.h = QLabel(); s.h.setObjectName("h1"); s.root.addWidget(s.h)
        s.lv = CardList(); s.lv.cols = cols
        s.lv.doubleClicked.connect(lambda _=None: s.profile())
        s.lv.dg.badge.connect(s.toggle_badge); s.lv.dg.heart.connect(s.toggle_heart)
        s.lv.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); s.lv.customContextMenuRequested.connect(s.ctx)
        s.info = QLabel(); s.info.setStyleSheet(f"color:{MUTED}")
        s.delay = QTimer(s); s.delay.setSingleShot(True); s.delay.setInterval(180); s.delay.timeout.connect(s.refresh)

    def refresh_soon(s, *_):
        """Espera a que termines de teclear antes de consultar la base de datos."""
        s.delay.start()

    def refresh(s, *_): raise NotImplementedError

    def sel(s): return s.lv.current_id()

    def show_rows(s, rows):
        """Muestra las tarjetas conservando la selección si el perfume sigue en la lista."""
        keep = s.sel(); s.lv.set_rows(rows)
        if keep is not None:
            for i, p in enumerate(rows):
                if p["id"] == keep: s.lv.setCurrentIndex(s.lv.mdl.index(i, 0)); break

    def _toggle_status(s, pid, status):
        """Quita el perfume de la colección si ya tenía ese estado; si no, se lo pone."""
        if (db.get(pid) or {}).get("status") == status: db.remove_from_collection(pid)
        else: db.set_collection(pid, status)
        s.changed.emit()

    def toggle_badge(s, pid): s._toggle_status(pid, "owned")
    def toggle_heart(s, pid): s._toggle_status(pid, "wishlist")

    def ctx(s, pos):
        i = s.lv.indexAt(pos)
        if not i.isValid(): return
        s.lv.setCurrentIndex(i); m = QMenu(s)
        m.addAction(tr("ctx.add"), lambda: s.mark("owned")); m.addAction(tr("ctx.wish"), lambda: s.mark("wishlist"))
        m.addAction(tr("ctx.remove"), s.remove_sel); m.addAction(tr("ctx.profile"), s.profile); m.exec(s.lv.viewport().mapToGlobal(pos))

    def mark(s, status):
        pid = s.sel()
        if pid is not None: db.set_collection(pid, status); s.changed.emit()

    def remove_sel(s):
        pid = s.sel()
        if pid is not None: db.remove_from_collection(pid); s.changed.emit()

    def profile(s):
        pid = s.sel()
        if pid is not None: s.open_profile.emit(pid)

    def count_text(s, key, n, total):
        return tr(key, n, total) + (tr("info.max") if n >= s.MAX_ROWS else "")
