"""Ventana de Configuración: de momento, las actualizaciones de la aplicación (búsqueda manual o automática una vez al día)."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from core import db, selfupdate
from core.i18n import tr
from core.version import VERSION
from ui.theme import ACCENT, MUTED


def auto_update_enabled(): return db.get_meta("auto_update") != "0"


class SettingsDialog(QDialog):
    def __init__(s, parent, open_versions, new_version=None):
        super().__init__(parent); s.setMinimumWidth(480); s.open_versions = open_versions
        v = QVBoxLayout(s); v.setSpacing(10); v.setContentsMargins(24, 22, 24, 20)
        s.h = QLabel(); s.h.setObjectName("h1"); s.h.setStyleSheet("font-size:24px;"); v.addWidget(s.h)
        s.sec = QLabel(); s.sec.setStyleSheet(f"font-size:14px;font-weight:600;color:{ACCENT};background:transparent;margin-top:8px;"); v.addWidget(s.sec)
        s.cur = QLabel(); s.cur.setStyleSheet(f"color:{MUTED};"); v.addWidget(s.cur)
        s.new = QLabel(new_version and tr("ver.available", new_version) or ""); s.new.setStyleSheet(f"color:{ACCENT};font-weight:600;"); s.new.setVisible(bool(new_version)); v.addWidget(s.new)
        s.auto = QCheckBox(); s.auto.setChecked(auto_update_enabled()); s.auto.setEnabled(selfupdate.configured())
        s.auto.toggled.connect(lambda on: db.set_meta("auto_update", "1" if on else "0")); v.addWidget(s.auto)
        s.check = QPushButton(); s.check.setObjectName("gold"); s.check.setCursor(Qt.CursorShape.PointingHandCursor); s.check.clicked.connect(s._check)
        row = QHBoxLayout(); row.addWidget(s.check); row.addStretch(1); v.addLayout(row); v.addStretch(1)
        s.close_b = QPushButton(); s.close_b.clicked.connect(s.accept); r2 = QHBoxLayout(); r2.addStretch(1); r2.addWidget(s.close_b); v.addLayout(r2)
        s.retranslate()
    def retranslate(s):
        s.setWindowTitle(tr("set.title")); s.h.setText(tr("set.title")); s.sec.setText(tr("set.updates")); s.cur.setText(tr("ver.current", VERSION))
        s.auto.setText(tr("set.auto")); s.auto.setToolTip(tr("set.auto.tip")); s.check.setText(tr("set.check")); s.close_b.setText(tr("ver.close"))
    def _check(s): s.accept(); s.open_versions()
