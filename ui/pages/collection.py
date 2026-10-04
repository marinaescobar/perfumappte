"""Mi colección: lista de tus perfumes y las pestañas Combinaciones favoritas y Mis gustos."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QButtonGroup, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget
from core import db, i18n, recommender as rec
from core.i18n import tr
from ui.pages.base import PerfumeListPage
from ui.pages.favorites import FavCombos
from ui.pages.tastes import Tastes
from ui.widgets import MultiSelect


class CollectionPage(PerfumeListPage):
    """Mi colección: tus perfumes (en propiedad y deseados) con tres pestañas: Perfumes, Combinaciones favoritas y Mis gustos."""
    STATUS = ["browser.filter.all", "browser.filter.owned", "browser.filter.wishlist"]
    STATUS_IDS = ["any", "owned", "wishlist"]

    def __init__(s):
        super().__init__()
        tabs = QHBoxLayout(); s.t_perf, s.t_fav, s.t_taste = QPushButton(), QPushButton(), QPushButton(); s.tab_group = QButtonGroup(s)
        for b in (s.t_perf, s.t_fav, s.t_taste):
            b.setObjectName("tgl"); b.setCheckable(True); b.setCursor(Qt.CursorShape.PointingHandCursor); s.tab_group.addButton(b); tabs.addWidget(b)
        s.t_perf.setChecked(True); tabs.addStretch(1); s.root.addLayout(tabs)
        # pestaña «Perfumes»
        s.body = QWidget(); bv = QVBoxLayout(s.body); bv.setContentsMargins(0, 0, 0, 0); bv.setSpacing(8)
        s.q = QLineEdit(); s.q.setObjectName("search"); s.gen = MultiSelect(); s.fam = QComboBox(); s.st = QComboBox()
        top = QHBoxLayout(); top.addWidget(s.q, 1)
        for w in (s.gen, s.fam, s.st): top.addWidget(w)
        bv.addLayout(top); bv.addWidget(s.lv, 1); bv.addWidget(s.info)
        s.q.textChanged.connect(s.refresh_soon)
        for sig in (s.st.currentIndexChanged, s.fam.currentIndexChanged, s.gen.changed): sig.connect(s.refresh)
        s.root.addWidget(s.body, 1)
        # las otras dos pestañas
        s.favs = FavCombos(); s.favs.open_profile.connect(s.open_profile.emit); s.favs.hide(); s.root.addWidget(s.favs, 1)
        s.tastes = Tastes(); s.tastes.hide(); s.root.addWidget(s.tastes, 1)
        for b in (s.t_perf, s.t_fav, s.t_taste): b.toggled.connect(lambda on: on and s.show_tab())          # al final: show_tab necesita todos los widgets
        s.retranslate()

    def show_tab(s):
        fav, taste = s.t_fav.isChecked(), s.t_taste.isChecked()
        s.body.setVisible(not (fav or taste)); s.favs.setVisible(fav); s.tastes.setVisible(taste); s.refresh()

    def retranslate(s):
        s.h.setText(tr("nav.collection"))
        for b, k in ((s.t_perf, "col.tab.perf"), (s.t_fav, "col.tab.fav"), (s.t_taste, "col.tab.taste")): b.setText(tr(k)); b.setToolTip(tr("tip." + k))
        s.q.setPlaceholderText(tr("browser.search.ph"))
        s.st.blockSignals(True); s.st.clear(); s.st.addItems([tr(k) for k in s.STATUS]); s.st.blockSignals(False)
        s.fam.blockSignals(True); s.fam.clear(); s.fam.addItem(tr("browser.filter.family.all"), "")
        for n in rec.FAMILIES: s.fam.addItem(i18n.tr_family_word(n), n)
        s.fam.blockSignals(False)
        s.gen.set_items([(g, i18n.tr_gender(g)) for g in ("male", "female", "unisex")], tr("browser.gender"))
        for w, k in ((s.q, "search"), (s.st, "status"), (s.fam, "family"), (s.gen, "gender")): w.setToolTip(tr("tip." + k))
        s.refresh()

    def refresh(s, *_):
        if s.t_fav.isChecked(): s.favs.reload(); return
        if s.t_taste.isChecked(): s.tastes.reload(); return
        rows = db.search(s.q.text(), s.fam.currentData(), "", s.STATUS_IDS[s.st.currentIndex()], s.MAX_ROWS, gender=s.gen.values())
        s.show_rows(rows); s.info.setText(s.count_text("info.col", len(rows), db.count()))
