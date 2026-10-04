"""Mi colección > Combinaciones favoritas: las combinaciones de layering marcadas con el corazón."""
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget
from core import db, recommender as rec
from core.i18n import tr
from ui import images
from ui.cards import PairCard
from ui.theme import MUTED


class FavCombos(QWidget):
    """Mi colección > Combinaciones favoritas: las combinaciones de layering marcadas con el corazón."""
    open_profile = pyqtSignal(int)
    def __init__(s):
        super().__init__(); v = QVBoxLayout(s); v.setContentsMargins(0, 0, 0, 0)
        s.empty = QLabel(); s.empty.setWordWrap(True); s.empty.setStyleSheet(f"color:{MUTED};background:transparent;"); v.addWidget(s.empty)
        s.sc = QScrollArea(); s.sc.setWidgetResizable(True); s.sc.setFrameShape(QFrame.Shape.NoFrame)
        s.inner = QWidget(); s.l = QVBoxLayout(s.inner); s.l.setContentsMargins(0, 0, 8, 0); s.l.setSpacing(8); s.l.addStretch(1); s.sc.setWidget(s.inner); v.addWidget(s.sc, 1)
        s.cards = []; images.get_cache().loaded.connect(s._img)
    def _img(s, key, *_):
        for pc in s.cards:
            for c in pc.cards:
                if c.key == key: c.set_pix()
    def reload(s):
        while s.l.count() > 1:
            w = s.l.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
        s.cards = []; favs = db.fav_list(); n = 0
        for a, b in favs:
            pa, pb = db.get(a), db.get(b)
            if not pa or not pb: continue
            pa, pb = rec.fill_axes(pa), rec.fill_axes(pb)
            sc, why = rec.layer_score(pa, pb)
            base, top = (pa, pb) if rec.layer_weight(pa) >= rec.layer_weight(pb) else (pb, pa)
            pc = PairCard(base, top, why or [tr("fav.nowhy")], True); pc.opened.connect(s.open_profile.emit); pc.fav_toggled.connect(s._fav)
            s.l.insertWidget(n, pc); s.cards.append(pc); n += 1
        s.empty.setText(tr("fav.empty")); s.empty.setVisible(n == 0)
    def _fav(s, a, b, on):
        db.fav_set(a, b, on)
        if not on: QTimer.singleShot(0, s.reload)
