"""Ventana «Versiones»: versión instalada, novedades de cada versión publicada en GitHub y actualización con un clic."""
import html
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton, QTextBrowser, QVBoxLayout
from core import selfupdate
from core.i18n import tr
from core.paths import FROZEN
from core.version import VERSION
from ui.theme import ACCENT, ERR, MUTED
from ui.workers import DownloadWorker, ReleasesWorker


class VersionsDialog(QDialog):
    installing = pyqtSignal()                 # el instalador ya se ha lanzado: la ventana principal debe cerrar la app

    def __init__(s, parent=None, releases=None, recheck=False):
        super().__init__(parent); s.setMinimumSize(660, 620); s.rels = list(releases or []); s.wk = None; s.dl = None
        v = QVBoxLayout(s); v.setSpacing(8); v.setContentsMargins(22, 20, 22, 18)
        s.h = QLabel(); s.h.setObjectName("h1"); s.h.setStyleSheet("font-size:24px;"); v.addWidget(s.h)
        s.cur = QLabel(); s.cur.setStyleSheet(f"color:{MUTED};"); v.addWidget(s.cur)
        s.status = QLabel(); s.status.setWordWrap(True); s.status.setTextFormat(Qt.TextFormat.RichText); v.addWidget(s.status)
        s.bar = QProgressBar(); s.bar.setTextVisible(True); s.bar.hide(); v.addWidget(s.bar)
        s.lst = QListWidget(); s.lst.setMaximumHeight(130); s.lst.currentRowChanged.connect(s._show_notes); v.addWidget(s.lst)
        s.notes = QTextBrowser(); s.notes.setOpenExternalLinks(True); v.addWidget(s.notes, 1)
        row, row2 = QHBoxLayout(), QHBoxLayout(); v.addLayout(row); v.addLayout(row2)
        s.b_check = QPushButton(); s.b_check.clicked.connect(s.check)
        s.b_update = QPushButton(); s.b_update.setObjectName("gold"); s.b_update.clicked.connect(s.update_now)
        s.b_skip = QPushButton(); s.b_skip.clicked.connect(s.skip_version)
        s.b_web = QPushButton(); s.b_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(selfupdate.releases_page())))
        s.b_close = QPushButton(); s.b_close.clicked.connect(s.close)
        for b in (s.b_update, s.b_check, s.b_skip): row.addWidget(b)
        row.addStretch(1)
        row2.addWidget(s.b_web); row2.addStretch(1); row2.addWidget(s.b_close)
        s.retranslate(); s._fill()
        if recheck or not s.rels: s.check()

    # ---------- textos
    def retranslate(s):
        s.setWindowTitle(tr("ver.title")); s.h.setText(tr("ver.title")); s.cur.setText(tr("ver.current", VERSION))
        s.b_check.setText(tr("ver.check")); s.b_skip.setText(tr("ver.skip")); s.b_web.setText(tr("ver.github")); s.b_close.setText(tr("ver.close"))

    def _say(s, text, color=None):
        s.status.setText(f"<span style='color:{color or MUTED}'>{text}</span>")

    # ---------- consulta
    def check(s):
        if s.wk is not None: return
        if not selfupdate.configured(): s._fill(); return
        s.b_check.setEnabled(False); s._say(html.escape(tr("ver.checking")))
        s.wk = ReleasesWorker(); s.wk.done.connect(s._loaded); s.wk.failed.connect(s._failed); s.wk.start()

    def _loaded(s, rels):
        s._end_worker(); s.rels = rels; selfupdate.mark_checked(); s._fill()

    def _failed(s, code):
        s._end_worker(); s._say(html.escape(s._err(code)), ERR); s.b_check.setEnabled(True)

    def _end_worker(s):
        w, s.wk = s.wk, None
        if w: w.wait(); w.deleteLater()

    @staticmethod
    def _err(code):
        key = "ver.err." + (code if code in ("net", "notfound", "ratelimit", "notconfigured", "asset", "hash", "size", "untrusted", "platform", "badjson") else "other")
        return tr(key, code)

    # ---------- contenido
    def _fill(s):
        s.new = selfupdate.newest(s.rels)
        s.lst.blockSignals(True); s.lst.clear()
        for r in s.rels:
            tag = tr("ver.tag.installed") if r.version == VERSION else tr("ver.tag.new") if s.new and r.version == s.new.version else ""
            it = QListWidgetItem(f"v{r.version}   {r.published}   {tag}".rstrip()); s.lst.addItem(it)
        s.lst.blockSignals(False)
        if not selfupdate.configured(): s._say(html.escape(tr("ver.err.notconfigured")))
        elif s.new:
            s._say(f"<b style='color:{ACCENT}'>{html.escape(tr('ver.available', s.new.version))}</b>")
        elif s.rels: s._say(html.escape(tr("ver.uptodate")))
        elif s.wk is None: s._say(html.escape(tr("ver.none")))
        can = bool(s.new) and FROZEN
        s.b_update.setVisible(bool(s.new)); s.b_update.setEnabled(can); s.b_skip.setVisible(bool(s.new))
        s.b_update.setText(tr("ver.update", s.new.version) if s.new else "")
        if s.new and not FROZEN: s.status.setText(s.status.text() + f"<br><span style='color:{MUTED}'>{html.escape(tr('ver.source'))}</span>")
        s.b_check.setEnabled(s.wk is None and selfupdate.configured())
        if s.rels: s.lst.setCurrentRow(0); s._show_notes(0)
        else: s.notes.setPlainText("")

    def _show_notes(s, row):
        if 0 <= row < len(s.rels):
            r = s.rels[row]; s.notes.setMarkdown(f"## {r.name or 'v' + r.version}\n\n" + (r.notes.strip() or tr("ver.nonotes")))

    # ---------- acciones
    def skip_version(s):
        if s.new: selfupdate.skip(s.new.version); s.close()

    def update_now(s):
        if not s.new or s.dl is not None: return
        s.b_update.setEnabled(False); s.b_check.setEnabled(False); s.b_skip.setEnabled(False)
        s.bar.setRange(0, 0); s.bar.show(); s._say(html.escape(tr("ver.downloading")))
        s.dl = DownloadWorker(s.new); s.dl.progress.connect(s._progress); s.dl.done.connect(s._downloaded); s.dl.failed.connect(s._dl_failed); s.dl.start()

    def _progress(s, done, total):
        if total: s.bar.setRange(0, 100); s.bar.setValue(int(100 * done / total))

    def _end_download(s):
        w, s.dl = s.dl, None
        if w: w.wait(); w.deleteLater()
        s.bar.hide()

    def _dl_failed(s, code):
        s._end_download(); s._say(html.escape(s._err(code)), ERR); s.b_update.setEnabled(True); s.b_check.setEnabled(True); s.b_skip.setEnabled(True)

    def _downloaded(s, path):
        s._end_download(); s._say(html.escape(tr("ver.installing")))
        try: selfupdate.install(path)
        except (selfupdate.UpdateError, OSError) as e:
            s._say(html.escape(s._err(str(e))), ERR); s.b_update.setEnabled(True); return
        s.installing.emit()

    def closeEvent(s, e):
        if s.dl is not None: e.ignore(); return                  # no se cierra a mitad de una descarga
        s._end_worker(); super().closeEvent(e)
