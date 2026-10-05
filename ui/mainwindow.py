"""Ventana principal: barra lateral plegable, páginas, chat de Góngora, perfil emergente y actualizaciones."""
from PyQt6.QtCore import QEasingCurve, QRectF, QSize, QTimer, QVariantAnimation, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QToolTip, QVBoxLayout, QWidget
from core import db, i18n, selfupdate, updater
from core.version import VERSION
from core.i18n import tr
from ui import icons, logo, theme
from ui.chat import Bubble, ChatPanel
from ui.pages.collection import CollectionPage
from ui.pages.discover import DiscoverPage
from ui.pages.profile import ProfilePopup
from ui.pages.recs import RecsPage
from ui.settings import SettingsDialog, auto_update_enabled
from ui.theme import ACCENT, MUTED, PANEL
from ui.widgets import LangPicker, ThemeToggle
from ui.versions import VersionsDialog
from ui.workers import ReleasesWorker, UpdateWorker


def apply_tooltip_palette():
    pal = QPalette(); pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.TT_BG)); pal.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.TIP_BODY)); QToolTip.setPalette(pal)


class Main(QMainWindow):
    NAV = ["nav.collection", "nav.finder", "nav.recs"]
    NAV_ICONS = ["nav_col", "nav_find", "nav_rec"]
    SIDE_W, SIDE_MINI = 220, 68
    def __init__(s):
        super().__init__(); s.setWindowTitle("Perfúmappte"); s.resize(1300, 820)
        root = QWidget(); h = QHBoxLayout(root); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        side = QWidget(); side.setObjectName("side"); s.side = side; s.side_open = db.get_meta("side_collapsed") != "1"; side.setFixedWidth(s.SIDE_W if s.side_open else s.SIDE_MINI); sl = QVBoxLayout(side); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(0)
        s.logo_lbl = QLabel(); s.logo_lbl.setObjectName("logo"); s.logo_lbl.setStyleSheet(""); sl.addWidget(s.logo_lbl)
        s.pages = [CollectionPage(), DiscoverPage(), RecsPage()]
        s.stack = QStackedWidget(); s.btns = []
        for i, pg in enumerate(s.pages):
            b = QPushButton(); b.setObjectName("nav"); b.setCheckable(True); b.setIcon(s._nav_icon(s.NAV_ICONS[i])); b.setIconSize(QSize(22, 22)); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(lambda _, i=i: s.go(i)); sl.addWidget(b); s.btns.append(b)
            s.stack.addWidget(pg)
            pg.open_profile.connect(s.show_profile)
            if hasattr(pg, "changed"): pg.changed.connect(s.refresh_page)
            if hasattr(pg, "update_requested"): pg.update_requested.connect(lambda: s.start_update(True))
        sl.addStretch(); s.setb = QPushButton(); s.setb.setObjectName("nav"); s.setb.setIcon(s._nav_icon("nav_set")); s.setb.setIconSize(QSize(22, 22)); s.setb.setCursor(Qt.CursorShape.PointingHandCursor); s.setb.clicked.connect(s.open_settings); sl.addWidget(s.setb)
        s.fold = QPushButton(); s.fold.setObjectName("sidetoggle"); s.fold.setFixedSize(34, 34); s.fold.setCursor(Qt.CursorShape.PointingHandCursor)
        s.fold.clicked.connect(s.toggle_side); sl.addWidget(s.fold, 0, Qt.AlignmentFlag.AlignHCenter); sl.addSpacing(6)
        s.stat = QLabel(); s.stat.setWordWrap(True)
        s.stat.setStyleSheet(f"color:{MUTED};font-size:11px;padding:12px 20px 4px 20px;background:transparent;"); sl.addWidget(s.stat)
        s.ver = QPushButton(); s.ver.setObjectName("verlink"); s.ver.setCursor(Qt.CursorShape.PointingHandCursor); s.ver.clicked.connect(s.open_versions); sl.addWidget(s.ver)
        s.releases, s.new_release, s.vw, s.vdlg = [], None, None, None
        h.addWidget(side)
        right = QWidget(); rv = QVBoxLayout(right); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        bar = QWidget(); bar.setObjectName("topbar"); bl = QHBoxLayout(bar); bl.setContentsMargins(26, 12, 26, 4)
        s.lang = LangPicker(); s.lang.set_code(i18n.LANG); s.lang.picked.connect(s.set_lang)
        s.themer = ThemeToggle(); s.themer.set_mode(theme.MODE); s.themer.picked.connect(s.set_theme); bl.setSpacing(10)
        bl.addStretch(); bl.addWidget(s.themer); bl.addWidget(s.lang); rv.addWidget(bar); rv.addWidget(s.stack, 1)
        h.addWidget(right, 1); s.setCentralWidget(root)
        s.chat = ChatPanel(root); s.chat.open_profile.connect(s.show_profile); s.chat.hide(); s.bubble = Bubble(root); s.bubble.clicked.connect(s.toggle_chat)
        s.prof = ProfilePopup(root); s.prof.closed.connect(s.refresh_page)
        s.uw = None; s.tmr = QTimer(s); s.tmr.setInterval(3600 * 1000); s.tmr.timeout.connect(s.check_update); s.tmr.timeout.connect(s.check_version); s.tmr.start()
        QTimer.singleShot(1500, s.check_update); QTimer.singleShot(5000, s.check_version)
        s.apply_side(); s.retranslate(); s.go(0)
    @staticmethod
    def _nav_icon(kind):
        ic = QIcon()
        for state, col in ((QIcon.State.Off, MUTED), (QIcon.State.On, ACCENT)):
            pm = QPixmap(44, 44); pm.fill(Qt.GlobalColor.transparent); pm.setDevicePixelRatio(2); q = QPainter(pm)
            icons.draw(q, kind, QRectF(0, 0, 22, 22), 1.0, col, col, PANEL); q.end(); ic.addPixmap(pm, QIcon.Mode.Normal, state)
        return ic
    def toggle_side(s):
        s.side_open = not s.side_open; db.set_meta("side_collapsed", "0" if s.side_open else "1")
        a = QVariantAnimation(s); a.setDuration(220); a.setStartValue(s.side.width()); a.setEndValue(s.SIDE_W if s.side_open else s.SIDE_MINI)
        a.setEasingCurve(QEasingCurve.Type.OutCubic); a.valueChanged.connect(lambda w: s.side.setFixedWidth(int(w)))
        if s.side_open: a.finished.connect(s.apply_side)
        else: s.apply_side()
        s._anim = a; a.start()
    def apply_side(s):
        """Texto, logo y estado de la barra lateral según esté desplegada o plegada."""
        o = s.side_open
        s.side.setFixedWidth(s.SIDE_W if o else s.SIDE_MINI)
        s.logo_lbl.setProperty("compact", not o); s.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft if o else Qt.AlignmentFlag.AlignHCenter)
        s.logo_lbl.setPixmap(logo.wordmark_pixmap(32) if o else logo.mark_pixmap(36, tile=False))
        for b, key in zip(s.btns, s.NAV):
            b.setProperty("compact", not o); b.setText(("  " + tr(key)) if o else ""); b.setToolTip(tr("tip." + key) if o else tr(key) + "\n" + tr("tip." + key))
            b.style().unpolish(b); b.style().polish(b)
        s.setb.setProperty("compact", not o); s.setb.setText(("  " + tr("nav.settings")) if o else ""); s.setb.setToolTip(tr("tip.nav.settings") if o else tr("nav.settings") + chr(10) + tr("tip.nav.settings"))
        s.setb.style().unpolish(s.setb); s.setb.style().polish(s.setb)
        s.logo_lbl.style().unpolish(s.logo_lbl); s.logo_lbl.style().polish(s.logo_lbl)
        s.stat.setVisible(o); s.update_version_button(); s.fold.setText("‹" if o else "›"); s.fold.setToolTip(tr("tip.fold.close") if o else tr("tip.fold.open"))
    def set_theme(s, mode):
        """Cambia entre tema claro y oscuro y lo recuerda para la próxima vez."""
        if mode == theme.MODE: return
        old = theme.palette(); theme.apply(mode); db.set_meta("theme", theme.MODE); apply_tooltip_palette()
        theme.restyle(QApplication.instance(), old); s.retheme()
    def retheme(s):
        """Lo que se pinta con imágenes ya hechas (iconos, logo) hay que regenerarlo con los colores nuevos."""
        s.themer.set_mode(theme.MODE)
        for b, kind in zip(s.btns, s.NAV_ICONS): b.setIcon(s._nav_icon(kind))
        s.setb.setIcon(s._nav_icon("nav_set")); s.apply_side(); s.chat.retheme(); s.prof.update()
    def set_lang(s, code):
        if code and code != i18n.LANG:
            i18n.set_lang(code); db.set_meta("lang", code); s.retranslate()
    def retranslate(s):
        s.lang.set_code(i18n.LANG)
        s.apply_side()
        s.lang.setToolTip(tr("tip.lang"))
        s.stat.setText(updater.status_text()); s.update_version_button()
        for pg in s.pages:
            if hasattr(pg, "retranslate"): pg.retranslate()
        s.chat.retranslate(); s.bubble.retranslate()
        s.prof.retranslate()
    # ---------- versiones de la propia aplicación (Releases de GitHub)
    def update_version_button(s):
        new = s.new_release is not None
        s.ver.setProperty("new", new); s.ver.setProperty("compact", not s.side_open)
        s.ver.setText((tr("ver.footer.new", s.new_release.version) if new else tr("ver.footer", VERSION)) if s.side_open else ("⬆" if new else ""))
        s.ver.setVisible(s.side_open or new); s.ver.setToolTip(tr("tip.ver"))
        s.ver.style().unpolish(s.ver); s.ver.style().polish(s.ver)

    def check_version(s):
        """Busca una versión nueva (como mucho una vez al día, en segundo plano). Si la hay, avisa una sola vez por versión."""
        if s.vw is not None or not auto_update_enabled() or not selfupdate.configured() or not selfupdate.due(): return
        s.vw = ReleasesWorker(); s.vw.done.connect(s._versions_loaded); s.vw.failed.connect(lambda _c: s._end_version_worker()); s.vw.start()

    def _end_version_worker(s):
        w, s.vw = s.vw, None
        if w: w.wait(); w.deleteLater()

    def _versions_loaded(s, rels):
        s._end_version_worker(); selfupdate.mark_checked(); s.releases = rels; s.new_release = selfupdate.newest(rels); s.update_version_button()
        if s.new_release and selfupdate.skipped() != s.new_release.version: s.open_versions(manual=False)

    def open_settings(s):
        SettingsDialog(s, s.open_versions, s.new_release.version if s.new_release else None, s.refresh_page).exec()

    def open_versions(s, manual=True):
        """`manual`: la abre la persona (busca de nuevo al abrirse); si no, es el aviso automático y ya trae las Releases."""
        if s.vdlg is not None and s.vdlg.isVisible(): s.vdlg.raise_(); s.vdlg.activateWindow(); return
        s.vdlg = VersionsDialog(s, s.releases, recheck=manual); s.vdlg.installing.connect(s._quit_for_update); s.vdlg.finished.connect(lambda _r: s._refresh_new_release())
        s.vdlg.show()

    def _refresh_new_release(s):
        if s.vdlg is not None and s.vdlg.rels: s.releases = s.vdlg.rels; s.new_release = selfupdate.newest(s.releases)
        s.update_version_button()

    def _quit_for_update(s):
        QTimer.singleShot(400, QApplication.instance().quit)           # el instalador ya está en marcha y reabrirá la app

    def check_update(s):
        if (s.uw and s.uw.isRunning()) or not (db.count() == 0 or updater.due()): return
        if updater.has_credentials(): s.start_update(False)
        elif db.count() == 0: QMessageBox.information(s, tr("up.help.title"), updater.help_text())
    def start_update(s, manual):
        if s.uw and s.uw.isRunning(): return
        s.uw = UpdateWorker(); disc = s.pages[1]; disc.set_update_status(tr("up.starting"), True)
        s.uw.status.connect(lambda t: disc.set_update_status(t, True)); s.uw.done.connect(s._upd_done)
        s.uw.failed.connect(lambda msg: (disc.set_update_status("", False), s.stat.setText(updater.status_text()), manual and QMessageBox.warning(s, tr("up.title"), msg)))
        s.uw.start()
    def _upd_done(s, new, upd):
        s.stat.setText(updater.status_text()); s.pages[1].set_update_status(tr("up.done", tr("db.res", new, upd)), False); s.refresh_page()
    def toggle_chat(s):
        s.chat.setVisible(not s.chat.isVisible()); s.place(); s.chat.raise_(); s.bubble.raise_()
        if s.chat.isVisible(): s.chat.inp.setFocus()
    def place(s):
        w, h = s.width(), s.height(); s.bubble.move(w - 80, h - 80); ch = max(360, min(620, h - 120)); s.chat.setGeometry(w - 424, h - 92 - ch, 400, ch)
    def resizeEvent(s, e): super().resizeEvent(e); s.place(); s.bubble.raise_()
    def go(s, i):
        for j, b in enumerate(s.btns): b.setChecked(j == i)
        s.stack.setCurrentIndex(i); s.pages[i].refresh()
    def show_profile(s, pid): s.prof.open(pid)
    def refresh_page(s): s.pages[s.stack.currentIndex()].refresh()
