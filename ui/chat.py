"""Góngora: botón flotante y panel de chat con el perfumista con IA."""
import html
import re
from PyQt6.QtCore import QPoint, QPointF, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap, QPolygon
from PyQt6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                             QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)
from core import db, gongora, recommender as rec
from core.i18n import tr
from ui import avatar
from ui import theme
from ui.theme import ACCENT, BORDER, MUTED, SHADOW, TXT
from ui.widgets import IconButton
from ui.workers import GongoraWorker


class Bubble(QPushButton):
    def __init__(s, parent):
        super().__init__(parent); s.setFixedSize(56, 56); s.setCursor(Qt.CursorShape.PointingHandCursor)
        s.retranslate()
    def retranslate(s): s.setToolTip(tr("tip.chat"))
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(ACCENT)); p.drawEllipse(0, 0, 56, 56); p.setBrush(QColor("white"))
        p.drawRoundedRect(15, 16, 26, 19, 6, 6); p.drawPolygon(QPolygon([QPoint(20, 33), QPoint(20, 42), QPoint(29, 34)]))

def tool_icon(kind, color):
    """Iconos de trazo para los botones del chat (el engranaje y la cruz como texto dependían de la tipografía)."""
    import math as _m
    pm = QPixmap(40, 40); pm.setDevicePixelRatio(2); pm.fill(Qt.GlobalColor.transparent); q = QPainter(pm); q.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.7); pen.setCapStyle(Qt.PenCapStyle.RoundCap); q.setPen(pen); q.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "close": q.drawLine(QPointF(5, 5), QPointF(15, 15)); q.drawLine(QPointF(15, 5), QPointF(5, 15))
    else:
        q.drawEllipse(QPointF(10, 10), 3.2, 3.2); q.drawEllipse(QPointF(10, 10), 6.2, 6.2)
        for k in range(8):
            a = _m.radians(k * 45); q.drawLine(QPointF(10 + 6.2 * _m.cos(a), 10 + 6.2 * _m.sin(a)), QPointF(10 + 8.6 * _m.cos(a), 10 + 8.6 * _m.sin(a)))
    q.end(); ic = QIcon(); ic.addPixmap(pm); return ic

def md_html(t):
    """Markdown mínimo (negrita, cursiva, viñetas) a HTML para las burbujas del chat."""
    t = html.escape(t or "")
    lines = []
    for ln in t.split("\n"):
        m = re.match(r"\s*[\*\-•]\s+(.*)", ln)
        lines.append("&nbsp;•&nbsp;" + m.group(1) if m else ln)
    t = "<br>".join(lines)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    return re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)

class SuggestCard(QFrame):
    """Tarjeta bajo la respuesta de Góngora: una combinación o un perfume que se puede guardar con un corazón."""
    open_profile = pyqtSignal(int)
    def __init__(s, sug):
        super().__init__(); s.setObjectName("gcard"); s.sug = sug
        h = QHBoxLayout(s); h.setContentsMargins(12, 8, 8, 8); h.setSpacing(8); box = QVBoxLayout(); box.setSpacing(1); box.setContentsMargins(0, 0, 0, 0)
        kind = QLabel(tr("gongora.card.layer" if sug["type"] == "layering" else "gongora.card.perfume").upper())
        kind.setStyleSheet(f"color:{ACCENT};font-size:9px;font-weight:700;letter-spacing:1px;background:transparent;"); box.addWidget(kind)
        items = [(sug["base"], tr("gongora.card.base")), (sug["top"], tr("gongora.card.top"))] if sug["type"] == "layering" else [(sug["perfume"], "")]
        for p, role in items:
            full = f"{p['name']}" + (f" · {p['brand']}" if sug["type"] == "perfume" and p.get("brand") else "") + (f"  ({role})" if role else "")
            b = QPushButton(); f_ = QFont(b.font()); f_.setBold(True); b.setText(QFontMetrics(f_).elidedText(full, Qt.TextElideMode.ElideRight, 205))
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.setToolTip(full + "\n" + tr("gongora.card.open")); b.clicked.connect(lambda _=False, i=p["id"]: s.open_profile.emit(i))
            b.setStyleSheet(f"QPushButton{{border:none;background:transparent;text-align:left;padding:1px 0;font-weight:600;color:{TXT};}}QPushButton:hover{{color:{ACCENT};}}"); box.addWidget(b)
        h.addLayout(box, 1)
        s.heart = IconButton("wish", 28); s.heart.setToolTip(tr("tip.gongora.fav" if sug["type"] == "layering" else "tip.gongora.wish"))
        s.heart.set_active(s.saved()); s.heart.clicked.connect(s.flip); h.addWidget(s.heart, 0, Qt.AlignmentFlag.AlignVCenter)
    def saved(s):
        if s.sug["type"] == "layering": return db.fav_has(s.sug["base"]["id"], s.sug["top"]["id"])
        p = db.get(s.sug["perfume"]["id"]); return bool(p and p.get("status") == "wishlist")
    def flip(s):
        on = not s.heart.active
        if s.sug["type"] == "layering": db.fav_set(s.sug["base"]["id"], s.sug["top"]["id"], on)
        else:
            pid = s.sug["perfume"]["id"]
            if on: db.set_collection(pid, "wishlist")
            elif (db.get(pid) or {}).get("status") == "wishlist": db.remove_from_collection(pid)
        s.heart.set_active(on)

class ChatPanel(QFrame):
    """Góngora: chat con el perfumista con IA (Gemini), que conoce tu colección y puede consultar la base de datos."""
    BUBBLE_W = 292
    open_profile = pyqtSignal(int)
    def __init__(s, parent):
        super().__init__(parent); s.setObjectName("chat"); s.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        s.g = gongora.Gongora(); s.rows = []; s.cur = None; s.cur_text = ""; s.wk = None
        v = QVBoxLayout(s); v.setContentsMargins(18, 16, 18, 16); v.setSpacing(10)
        top = QHBoxLayout(); top.setSpacing(10)
        av = QLabel(); av.setPixmap(avatar.pixmap(44)); av.setFixedSize(44, 44)
        head = QVBoxLayout(); head.setSpacing(0)
        s.t = QLabel(); s.t.setStyleSheet("font-family:Georgia,serif;font-size:21px;"); s.sub = QLabel(); s.sub.setStyleSheet(f"color:{MUTED};font-size:11px;")
        head.addWidget(s.t); head.addWidget(s.sub)
        s.clr = QPushButton(); s.clr.setCursor(Qt.CursorShape.PointingHandCursor); s.clr.clicked.connect(s.clear)
        s.clr.setObjectName("gclear")
        s.cfg = QPushButton(); s.cfg.setFixedSize(30, 30); s.cfg.setCursor(Qt.CursorShape.PointingHandCursor); s.cfg.setIcon(tool_icon("cog", MUTED)); s.cfg.setIconSize(QSize(20, 20))
        s.cfg.setObjectName("gtool"); s.cfg.clicked.connect(s.ask_key)
        s.xb = x = QPushButton(); x.setToolTip(tr("tip.close")); x.setFixedSize(30, 30); x.setCursor(Qt.CursorShape.PointingHandCursor); x.setIcon(tool_icon("close", MUTED)); x.setIconSize(QSize(20, 20))
        x.setObjectName("gtool"); x.clicked.connect(s.hide)
        top.addWidget(av); top.addLayout(head); top.addStretch(); top.addWidget(s.clr); top.addWidget(s.cfg); top.addWidget(x); v.addLayout(top)
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet(f"background:{BORDER};"); v.addWidget(line)
        s.sc = QScrollArea(); s.sc.setWidgetResizable(True); s.sc.setFrameShape(QFrame.Shape.NoFrame); s.sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        s.inner = QWidget(); s.inner.setObjectName("gscroll"); s.col = QVBoxLayout(s.inner); s.col.setContentsMargins(0, 4, 6, 4); s.col.setSpacing(10); s.col.addStretch(1)
        s.sc.setWidget(s.inner); s.sc.viewport().setAutoFillBackground(False); v.addWidget(s.sc, 1)
        s.chips = QWidget(); s.chips.setObjectName("gscroll"); cl = QVBoxLayout(s.chips); cl.setContentsMargins(36, 0, 0, 0); cl.setSpacing(6); s.chipb = []
        for k in ("gongora.s1", "gongora.s2", "gongora.s3"):
            b = QPushButton(); b.setObjectName("ms"); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(lambda _=False, k=k: s.send(tr(k + ".q"))); cl.addWidget(b); s.chipb.append((k, b))
        s.status = QLabel(); s.status.setStyleSheet(f"color:{ACCENT};font-size:11px;"); v.addWidget(s.status)
        row = QHBoxLayout(); s.inp = QLineEdit(); s.inp.setObjectName("search"); s.inp.returnPressed.connect(lambda: s.send())
        s.go = QPushButton("↑"); s.go.setObjectName("gold"); s.go.setFixedSize(40, 40); s.go.setCursor(Qt.CursorShape.PointingHandCursor)
        s.go.setStyleSheet("border-radius:20px;padding:0;font-size:17px;"); s.go.clicked.connect(lambda: s.send())
        row.addWidget(s.inp, 1); row.addWidget(s.go); v.addLayout(row)
        s.retheme()
        s.hello = s.add("bot", "", html_text=True); s.col.insertWidget(s.col.count() - 1, s.chips); s.retranslate()
    def retheme(s):
        """Colores que no salen de la hoja de estilos: iconos de los botones y sombra del panel."""
        s.cfg.setIcon(tool_icon("cog", theme.MUTED)); s.xb.setIcon(tool_icon("close", theme.MUTED))
        eff = QGraphicsDropShadowEffect(s); eff.setBlurRadius(36); eff.setOffset(0, 8); eff.setColor(QColor(*theme.SHADOW, 70)); s.setGraphicsEffect(eff)
    # ---------- burbujas
    def add(s, kind, text, html_text=False):
        """Añade una burbuja ('user', 'bot' o 'note') y devuelve su QLabel."""
        lab = QLabel(); lab.setWordWrap(True); lab.setTextFormat(Qt.TextFormat.RichText); lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lab.setObjectName({"user": "guser", "bot": "gbot", "note": "gnote"}[kind]); s.set_text(lab, text, html_text)
        if kind != "note": lab.setMaximumWidth(s.BUBBLE_W)
        w = QWidget(); w.setObjectName("gscroll"); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
        if kind == "user": h.addStretch(1); h.addWidget(lab)
        elif kind == "note": h.addStretch(1); h.addWidget(lab); h.addStretch(1); lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            av = QLabel(); av.setPixmap(avatar.pixmap(30)); av.setFixedSize(30, 30); h.addWidget(av, 0, Qt.AlignmentFlag.AlignTop)
            lab.box = QVBoxLayout(); lab.box.setSpacing(6); lab.box.setContentsMargins(0, 0, 0, 0); lab.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum); lab.box.addWidget(lab); h.addLayout(lab.box); h.addStretch(1)
        s.col.insertWidget(s.col.count() - 1, w); s.rows.append((kind, w, lab)); s.to_bottom(); return lab
    @staticmethod
    def set_text(lab, text, html_text=False): lab.setText(text if html_text else md_html(text))
    def to_bottom(s): QTimer.singleShot(30, lambda: s.sc.verticalScrollBar().setValue(s.sc.verticalScrollBar().maximum()))
    def drop(s, lab):
        for i, (_k, w, l) in enumerate(s.rows):
            if l is lab: s.rows.pop(i); w.hide(); w.deleteLater(); return
    def retranslate(s):
        s.t.setText(tr("chat.title")); s.sub.setText(tr("gongora.sub")); s.inp.setPlaceholderText(tr("chat.ph")); s.inp.setToolTip(tr("tip.chatinp"))
        s.cfg.setToolTip(tr("gongora.cfg")); s.go.setToolTip(tr("gongora.send")); s.clr.setText(tr("gongora.clear")); s.clr.setToolTip(tr("gongora.clear.tip"))
        for k, b in s.chipb: b.setText(tr(k))
        s.set_text(s.hello, tr("gongora.hello"))
    # ---------- conversación
    def busy(s, on, msg=""):
        s.inp.setEnabled(not on); s.go.setEnabled(not on); s.clr.setEnabled(not on); s.status.setText(msg if on else "")
        if not on: s.inp.setFocus()
    def clear(s):
        """Borra la conversación (burbujas y memoria de Góngora) y vuelve al saludo con los atajos."""
        if s.wk is not None: return
        for _k, w, _l in s.rows[1:]: w.hide(); w.deleteLater()
        s.rows = s.rows[:1]; s.g.reset(); s.cur = None; s.cur_text = ""; s.sugs = []; s.status.setText(""); s.chips.show(); s.inp.clear(); s.inp.setFocus(); s.to_bottom()
    def ask_key(s):
        key, ok = QInputDialog.getText(s, tr("gongora.key.title"), tr("gongora.key.label"), QLineEdit.EchoMode.Password)
        if not ok: return False
        gongora.save_key(key); s.add("note", tr("gongora.key.saved") if key.strip() else tr("gongora.key.cleared")); return bool(key.strip())
    def send(s, text=None):
        t = (text if text is not None else s.inp.text()).strip()
        if not t or s.wk is not None: return
        s.inp.clear(); s.chips.hide(); s.add("user", t); s.start(t)
    def start(s, question):
        s.cur_text = ""; s.sugs = []; s.cur = s.add("bot", "", html_text=True); s.cur.setText(f"<i style='color:{MUTED}'>{html.escape(tr('gongora.thinking'))}</i>")
        s.busy(True, tr("gongora.thinking"))
        s.wk = GongoraWorker(s.g, question); s.wk.chunk.connect(s._chunk)
        s.wk.tool.connect(lambda n: (s.status.setText(tr("gongora.t." + n)), not s.cur_text and s.cur.setText(f"<i style='color:{MUTED}'>{html.escape(tr('gongora.t.' + n))}</i>")))
        s.wk.suggest.connect(s.sugs.append); s.wk.done.connect(s._done); s.wk.failed.connect(lambda kind, msg, q=question: s._failed(kind, msg, q)); s.wk.start()
    def _chunk(s, piece):
        s.cur_text += piece; s.set_text(s.cur, s.cur_text); s.to_bottom()
    def _finish(s):
        w, s.wk = s.wk, None
        if w: w.wait(); w.deleteLater()
        s.busy(False)
    def _done(s, text):
        s._finish()
        if not s.cur_text.strip(): s.set_text(s.cur, text or ("…" if not s.sugs else ""))
        if not s.cur_text.strip() and not text and s.sugs: s.cur.hide()                    # solo hay tarjetas: sin burbuja vacía
        for sug in s.sugs:
            card = SuggestCard(sug); card.open_profile.connect(s.open_profile.emit); s.cur.box.addWidget(card); card.setMaximumWidth(s.BUBBLE_W)
        s.to_bottom()
    def _failed(s, kind, msg, question):
        s._finish(); s.drop(s.cur); s.cur = None                       # quita la burbuja vacía de la respuesta
        if kind == "nokey":
            s.add("note", tr("gongora.nokey"))                            # la clave se pide al instalar; aquí no se interrumpe con ningún diálogo
            s.add("bot", rec.chat_answer(question, db.collection_rows("owned"), db.all_rows()), html_text=True); return
        s.add("note", tr("gongora.err.rate") if kind == "rate" else tr("gongora.err.net") if kind == "net" else tr("gongora.err.api", msg))
