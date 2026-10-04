"""Descubrimientos: explora toda la base de datos por familias olfativas, notas y género."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
                             QWidget)
from core import db, i18n
from core.i18n import tr
from core.note_emoji import note_emoji
from ui.pages.base import PerfumeListPage
from ui.theme import FAMILY_ICONS
from ui.widgets import MultiSelect


def _section_label():
    lab = QLabel(); lab.setStyleSheet("font-weight:600;background:transparent;"); return lab


class NotesDialog(QDialog):
    """Listado completo de notas con buscador y casillas (multiselección)."""
    def __init__(s, selected, parent=None):
        super().__init__(parent); s.setWindowTitle(tr("notes.all.title")); s.resize(420, 560); s.sel = list(selected); s._busy = False
        v = QVBoxLayout(s); s.q = QLineEdit(); s.q.setObjectName("search"); s.q.setPlaceholderText(tr("browser.filter.notes.ph")); v.addWidget(s.q)
        s.lst = QListWidget(); v.addWidget(s.lst, 1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText(tr("dlg.ok")); bb.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("dlg.cancel"))
        bb.accepted.connect(s.accept); bb.rejected.connect(s.reject); v.addWidget(bb)
        s.lst.itemChanged.connect(s._changed); s.q.textChanged.connect(s.fill); s.labels = {}; s.fill()
    def fill(s, *_):
        s._busy = True; s.lst.clear()
        for label, key, n in db.note_chips(s.q.text(), 100000):
            s.labels[key] = label
            it = QListWidgetItem(f"{note_emoji(label)}  {i18n.tr_note(label).title()}   ·  {n:,}"); it.setData(Qt.ItemDataRole.UserRole, key)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable); it.setCheckState(Qt.CheckState.Checked if key in s.sel else Qt.CheckState.Unchecked)
            s.lst.addItem(it)
        s._busy = False
    def _changed(s, it):
        if s._busy: return
        k = it.data(Qt.ItemDataRole.UserRole); on = it.checkState() == Qt.CheckState.Checked
        if on and k not in s.sel: s.sel.append(k)
        if not on and k in s.sel: s.sel.remove(k)


class DiscoverPage(PerfumeListPage):
    """Descubrimientos: toda la base de datos, filtrable por texto, género, estado, familias olfativas y notas."""
    update_requested = pyqtSignal()
    STATUS = ["browser.filter.all", "browser.filter.incol", "browser.filter.wishlist", "browser.filter.none"]
    STATUS_IDS = [None, "owned", "wishlist", "none"]
    COLS, NOTE_TOP = 6, 11                       # 6 columnas; 11 notas + el botón «Ver más» = 12 casillas (6 + 6)

    def __init__(s):
        super().__init__(cols=s.COLS)
        s.fam_sel, s.note_sel, s.note_lbl, s._chips_for = set(), [], {}, -1
        s.q = QLineEdit(); s.q.setObjectName("search"); s.gen = MultiSelect(); s.st = QComboBox(); s.clr = QPushButton()
        top = QHBoxLayout(); top.addWidget(s.q, 1)
        for w in (s.gen, s.st, s.clr): top.addWidget(w)
        s.root.addLayout(top)
        s.q.textChanged.connect(s.refresh_soon); s.st.currentIndexChanged.connect(s.refresh); s.gen.changed.connect(s.refresh); s.clr.clicked.connect(s.clear_filters)
        # panel de filtros: familias y notas completas, sin barras de desplazamiento
        s.panel = QWidget(); pv = QVBoxLayout(s.panel); pv.setContentsMargins(4, 0, 18, 0); pv.setSpacing(4)
        s.lab_fam, s.lab_notes = _section_label(), _section_label()
        pv.addWidget(s.lab_fam)
        s.fgrid = QGridLayout(); s.fgrid.setSpacing(8); pv.addLayout(s.fgrid, 1); s.fbtn = {}
        for i, (n, ic) in enumerate(FAMILY_ICONS.items()):
            b = QPushButton(); b.setObjectName("chip"); b.setCheckable(True); s._flex(b)
            b.toggled.connect(lambda on, n=n: s.toggle_fam(n, on)); s.fgrid.addWidget(b, i // s.COLS, i % s.COLS); s.fbtn[n] = (b, ic)
        pv.addWidget(s.lab_notes)
        s.ngrid = QGridLayout(); s.ngrid.setSpacing(8); pv.addLayout(s.ngrid, 1)
        for r in range(2): s.fgrid.setRowStretch(r, 1); s.ngrid.setRowStretch(r, 1)
        s.root.addWidget(s.panel, 1); s.root.addWidget(s.lv, 2); s.root.addWidget(s.info)
        bar = QHBoxLayout(); s.update_btn = QPushButton(); s.update_btn.clicked.connect(s.update_requested.emit); bar.addWidget(s.update_btn); bar.addStretch(); s.root.addLayout(bar)
        s.retranslate()

    @staticmethod
    def _flex(b):
        b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); b.setMinimumHeight(38); b.setMaximumHeight(90)

    def retranslate(s):
        s.h.setText(tr("nav.finder")); s.q.setPlaceholderText(tr("browser.search.ph"))
        s.st.blockSignals(True); s.st.clear(); s.st.addItems([tr(k) for k in s.STATUS]); s.st.blockSignals(False)
        s.clr.setText(tr("browser.filter.clear")); s.lab_fam.setText(tr("browser.filter.families")); s.lab_notes.setText(tr("browser.filter.notes"))
        s.gen.set_items([(g, i18n.tr_gender(g)) for g in ("male", "female", "unisex")], tr("browser.gender"))
        s.update_btn.setText(tr("btn.update")); s.update_btn.setToolTip(tr("tip.btn.update"))
        for n, (b, ic) in s.fbtn.items(): b.setText(f"{ic}  {i18n.tr_family_word(n)}"); b.setToolTip(tr("tip.fchip", i18n.tr_family_word(n)))
        for w, k in ((s.q, "search"), (s.st, "status"), (s.clr, "clear"), (s.gen, "gender")): w.setToolTip(tr("tip." + k))
        s.load_chips(); s.refresh()

    def toggle_fam(s, n, on):
        (s.fam_sel.add if on else s.fam_sel.discard)(n); s.refresh()

    def toggle_note(s, k, on):
        if on and k not in s.note_sel: s.note_sel.append(k)
        if not on and k in s.note_sel: s.note_sel.remove(k)
        s.refresh()

    def clear_filters(s):
        s.fam_sel.clear(); s.note_sel.clear()
        for b, _ in s.fbtn.values(): b.blockSignals(True); b.setChecked(False); b.blockSignals(False)
        s.q.blockSignals(True); s.q.clear(); s.q.blockSignals(False)
        s.st.blockSignals(True); s.st.setCurrentIndex(0); s.st.blockSignals(False); s.gen.clear(); s.load_chips(); s.refresh()

    def all_notes(s):
        dlg = NotesDialog(s.note_sel, s)
        if dlg.exec():
            s.note_sel = list(dlg.sel); s.note_lbl.update({k: (l, None) for k, l in dlg.labels.items() if k not in s.note_lbl}); s.load_chips(); s.refresh()

    def load_chips(s):
        """Las notas más comunes (más las que hayas marcado) y el botón «Ver más…»."""
        while s.ngrid.count():
            w = s.ngrid.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
        chips = db.note_chips("", s.NOTE_TOP)
        for label, key, n in chips: s.note_lbl[key] = (label, n)
        def chip(key, i):
            label, n = s.note_lbl.get(key, (key.title(), None))
            txt = i18n.tr_note(label).title() if i18n.is_es() else label.title()
            b = QPushButton(f"{note_emoji(label)}  {s.fontMetrics().elidedText(txt, Qt.TextElideMode.ElideRight, 90)}" + (f"  ·  {n:,}" if n else ""))
            b.setObjectName("chip"); s._flex(b); b.setCheckable(True); b.setToolTip(tr("tip.notechip", i18n.tr_note(label).title())); b.setChecked(key in s.note_sel)
            b.toggled.connect(lambda on, k=key: s.toggle_note(k, on)); s.ngrid.addWidget(b, i // s.COLS, i % s.COLS)
        keys = list(s.note_sel) + [key for _l, key, _n in chips if key not in s.note_sel]
        keys = keys[:max(s.NOTE_TOP, len(s.note_sel))]
        for i, k in enumerate(keys): chip(k, i)
        b = QPushButton("＋  " + tr("browser.more")); b.setObjectName("chip"); s._flex(b); b.setToolTip(tr("tip.more")); b.clicked.connect(s.all_notes)
        s.ngrid.addWidget(b, len(keys) // s.COLS, len(keys) % s.COLS)

    def refresh(s, *_):
        n = db.count()
        if s._chips_for != n: s._chips_for = n; s.load_chips()          # tras una actualización de la base hay notas nuevas
        rows = db.search(s.q.text(), sorted(s.fam_sel), list(s.note_sel), s.STATUS_IDS[s.st.currentIndex()], s.MAX_ROWS, note_exact=True, sort="pop_rating", gender=s.gen.values())
        s.show_rows(rows)
        s.info.setText(tr("info.empty") if n == 0 else s.count_text("info.found", len(rows), n))
