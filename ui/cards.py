"""Tarjetas de perfume: la lista de resultados, la miniatura de «parecido a» y la tarjeta de una combinación de layering."""
import html
from PyQt6.QtCore import QEvent, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QFrame, QHBoxLayout, QLabel, QListView, QStyle, QStyledItemDelegate, QVBoxLayout, QWidget
from core import recommender as rec
from core.i18n import tr
from ui import images
from ui.theme import ACCENT, BORDER, BOTTLE, BOTTLE_CAP, MUTED, PANEL, SOFT, TXT
from ui.widgets import IconButton, IconMeter, tip_html


class CardDelegate(QStyledItemDelegate):
    badge = pyqtSignal(int); heart = pyqtSignal(int)
    badges = True
    W, H = 178, 242
    def sizeHint(s, o, i): return QSize(s.W, s.H)
    @staticmethod
    def _card(rect): return rect.adjusted(4, 4, -4, -4)
    @staticmethod
    def _badge(card): return QRect(card.right() - 36, card.top() + 10, 26, 26)
    @staticmethod
    def _heart(card): return QRect(card.right() - 36, card.top() + 42, 26, 26)
    @staticmethod
    def _glyph(p, b, kind, col, filled):
        """Iconos dibujados con trazo redondeado (mismo estilo suave que el resto de la app)."""
        c = b.center(); path = QPainterPath(); pen = QPen(col, 1.9); pen.setCapStyle(Qt.PenCapStyle.RoundCap); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        if kind == "check":
            path.moveTo(c.x() - 5, c.y() + 0.5); path.lineTo(c.x() - 1.5, c.y() + 4); path.lineTo(c.x() + 5.5, c.y() - 4)
        elif kind == "plus":
            path.moveTo(c.x() - 5, c.y()); path.lineTo(c.x() + 5, c.y()); path.moveTo(c.x(), c.y() - 5); path.lineTo(c.x(), c.y() + 5)
        else:
            x, y, w = c.x(), c.y() + 5.2, 5.6
            path.moveTo(x, y); path.cubicTo(x - w * 1.9, y - 5.5, x - w * 1.1, y - 11, x, y - 6.2); path.cubicTo(x + w * 1.1, y - 11, x + w * 1.9, y - 5.5, x, y)
        p.setBrush(col if (kind == "heart" and filled) else Qt.BrushStyle.NoBrush); p.setPen(pen); p.drawPath(path)
    @staticmethod
    def _bottle(p, r):
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(BOTTLE)); cx = r.center().x()
        p.drawRoundedRect(cx - 22, r.top() + 36, 44, 70, 10, 10); p.drawRect(cx - 7, r.top() + 22, 14, 14)
        p.setBrush(QColor(BOTTLE_CAP)); p.drawRoundedRect(cx - 12, r.top() + 8, 24, 16, 4, 4)
    def paint(s, p, opt, idx):
        d = idx.data(Qt.ItemDataRole.UserRole); r = s._card(opt.rect)
        p.save(); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sel = bool(opt.state & QStyle.StateFlag.State_Selected); hov = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        p.setPen(QPen(QColor(ACCENT if (sel or hov) else BORDER), 2 if sel else 1)); p.setBrush(QColor(PANEL)); p.drawRoundedRect(r, 16, 16)
        f = QFont(opt.font); f.setPointSize(8); p.setFont(f); p.setPen(QColor(MUTED)); p.drawText(r.left() + 14, r.top() + 27, " · ".join(x for x in (str(d.get("year") or ""), f"★ {d['rating_avg']:.1f}" if d.get("rating_avg") else "") if x))
        st = d.get("status")
        for b, on, kind in (((s._badge(r), st == "owned", "check" if st == "owned" else "plus"), (s._heart(r), st == "wishlist", "heart")) if s.badges else ()):
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(ACCENT if on else SOFT)); p.drawEllipse(b)
            s._glyph(p, QRectF(b), kind, QColor("white" if on else ACCENT), on)
        ir = QRect(r.left() + 24, r.top() + 40, r.width() - 48, 110); key, url = images.src(d)
        pm = images.get_cache().get(key, url) if key else None
        if pm:
            pm = pm.scaled(ir.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(ir.x() + (ir.width() - pm.width()) // 2, ir.y() + (ir.height() - pm.height()) // 2, pm)
        else: s._bottle(p, ir)
        f = QFont(opt.font); f.setPointSize(7); f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1); p.setFont(f); p.setPen(QColor(MUTED))
        brand = p.fontMetrics().elidedText((d.get("brand") or "").upper(), Qt.TextElideMode.ElideRight, r.width() - 20)
        p.drawText(QRect(r.left() + 10, r.top() + 158, r.width() - 20, 16), Qt.AlignmentFlag.AlignCenter.value, brand)
        f = QFont(opt.font); f.setPointSize(10); f.setBold(True); p.setFont(f); p.setPen(QColor(TXT))
        p.drawText(QRect(r.left() + 10, r.top() + 176, r.width() - 20, 38), Qt.AlignmentFlag.AlignHCenter.value | Qt.AlignmentFlag.AlignTop.value | Qt.TextFlag.TextWordWrap.value, d.get("name") or "")
        if d.get("tags"):
            f = QFont(opt.font); f.setPointSize(8); p.setFont(f); p.setPen(QColor(ACCENT))
            p.drawText(QRect(r.left() + 10, r.bottom() - 22, r.width() - 20, 16), Qt.AlignmentFlag.AlignCenter.value, p.fontMetrics().elidedText(d["tags"], Qt.TextElideMode.ElideRight, r.width() - 20))
        p.restore()
    def editorEvent(s, ev, model, opt, idx):
        if s.badges and ev.type() == QEvent.Type.MouseButtonRelease and ev.button() == Qt.MouseButton.LeftButton:
            card, pos = s._card(opt.rect), ev.position().toPoint()
            if s._badge(card).adjusted(-3, -3, 3, 3).contains(pos): s.badge.emit(idx.data(Qt.ItemDataRole.UserRole)["id"]); return True
            if s._heart(card).adjusted(-3, -3, 3, 3).contains(pos): s.heart.emit(idx.data(Qt.ItemDataRole.UserRole)["id"]); return True
        return False
    def helpEvent(s, ev, view, opt, idx):
        card, pos = s._card(opt.rect), ev.pos()
        tip = (tr("tip.card.owned") if s._badge(card).contains(pos) else tr("tip.card.wish") if s._heart(card).contains(pos) else "") if s.badges else ""
        d = idx.data(Qt.ItemDataRole.UserRole)
        if not tip and isinstance(d, dict) and d.get("_why"):
            tip = tip_html(d.get("name") or "", "<b>" + html.escape(tr("buy.why.title")) + "</b><br>" + "<br>".join("• " + w for w in d["_why"]))
        if not tip: return False
        f = getattr(QApplication.instance(), "_tipf", None)
        if f is not None and f.tip is not None: f.tip.show_at(tip, ev.globalPos())
        return True

class CardList(QListView):
    def __init__(s):
        super().__init__(); s.mdl = QStandardItemModel(s); s.setModel(s.mdl); s.dg = CardDelegate(s); s.setItemDelegate(s.dg)
        s.setViewMode(QListView.ViewMode.IconMode); s.setResizeMode(QListView.ResizeMode.Adjust); s.setMovement(QListView.Movement.Static)
        s.setUniformItemSizes(True); s.setMouseTracking(True); s.setFrameShape(QFrame.Shape.NoFrame); s.setSpacing(0); s.cols = None
        s.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); s.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        s.setStyleSheet("QListView { background: transparent; border: none; }"); s.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        images.get_cache().loaded.connect(lambda *_: s.viewport().update())
    def resizeEvent(s, e):
        super().resizeEvent(e); vw = s.viewport().width()
        if vw > 50:
            w = (vw - 1) // (s.cols or max(1, vw // 178))
            if w != s.dg.W: s.dg.W = w; s.doItemsLayout()
    def set_rows(s, rows):
        s.mdl.clear()
        for p in rows:
            it = QStandardItem(); it.setData(p, Qt.ItemDataRole.UserRole); it.setEditable(False); s.mdl.appendRow(it)
    def current_id(s):
        i = s.currentIndex()
        return s.mdl.data(i, Qt.ItemDataRole.UserRole)["id"] if i.isValid() else None

class SimCard(QWidget):
    """Miniatura + nombre de un perfume parecido. Doble clic -> `opened(id)`."""
    W = 80
    opened = pyqtSignal(int)
    def __init__(s, q, score):
        super().__init__(); s.pid = q["id"]; s.key, s.url = images.src(q)
        s.setFixedWidth(s.W); s.setCursor(Qt.CursorShape.PointingHandCursor)
        v = QVBoxLayout(s); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(3)
        s.img = QLabel(); s.img.setFixedSize(s.W, 66); s.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.img.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:12px;font-size:24px;")
        s.name = QLabel(q["name"] or ""); s.name.setWordWrap(True); s.name.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        s.name.setStyleSheet(f"font-size:11px;color:{TXT};background:transparent;"); s.name.setFixedSize(s.W, 2 * s.name.fontMetrics().lineSpacing() + 2)
        v.addWidget(s.img); v.addWidget(s.name)
        label = q["name"] + (f" — {q['brand']}" if q.get("brand") else "")
        s.setToolTip(tr("tip.sim", html.escape(label), round(score * 100)))
        s.set_pix()
    def set_pix(s):
        pm = images.get_cache().get(s.key, s.url) if s.key else None
        if pm and not pm.isNull(): s.img.setPixmap(pm.scaled(QSize(s.W - 14, 58), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else: s.img.setText("🧴")
    def mouseReleaseEvent(s, e):
        if e.button() == Qt.MouseButton.LeftButton and s.rect().contains(e.position().toPoint()): s.opened.emit(s.pid)

class PairCard(QFrame):
    """Una combinación de layering: dos perfumes de tu colección, cuántas atomizaciones de cada uno y por qué encajan."""
    opened = pyqtSignal(int); fav_toggled = pyqtSignal(int, int, bool)
    def __init__(s, a, b, why, fav=False):
        super().__init__(); s.setObjectName("pair"); s.setFixedHeight(132); h = QHBoxLayout(s); h.setContentsMargins(14, 10, 16, 10); h.setSpacing(10); s.cards = []
        s.a, s.b = a, b
        for i, (q, role) in enumerate(((a, "base"), (b, "top"))):
            if i:
                plus = QLabel("＋"); plus.setStyleSheet(f"color:{ACCENT};font-size:18px;font-weight:600;background:transparent;"); h.addWidget(plus)
            col = QVBoxLayout(); col.setSpacing(2); col.setContentsMargins(0, 0, 0, 0)
            cap = QLabel(tr("layer." + role).upper()); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cap.setToolTip(tr("tip.layer." + role))
            cap.setStyleSheet(f"color:{ACCENT};font-size:10px;font-weight:700;letter-spacing:1px;background:transparent;")
            c = SimCard(q, 1.0); c.setToolTip(html.escape(rec.fmt(q))); c.opened.connect(s.opened.emit)
            col.addWidget(cap); col.addWidget(c); h.addLayout(col); s.cards.append(c)
        info = QVBoxLayout(); info.setSpacing(3); info.setContentsMargins(0, 0, 0, 0)
        for q in (a, b):
            r = QHBoxLayout(); r.setSpacing(2); r.setContentsMargins(0, 0, 0, 0)
            nm = QLabel(f"<b>{html.escape(q['name'])}</b>"); nm.setTextFormat(Qt.TextFormat.RichText); nm.setStyleSheet("background:transparent;"); nm.setMinimumWidth(210); r.addWidget(nm)
            n = rec.spray_count(q); tip = tr("layer.spray1") if n == 1 else tr("layer.sprays", n)
            for k in range(4): r.addWidget(IconMeter("spray", 1.0 if k < n else 0.0, tip_html(tip), 22))
            r.addStretch(1); info.addLayout(r)
        why_l = QLabel(html.escape("; ".join(why))); why_l.setWordWrap(True); why_l.setStyleSheet(f"color:{MUTED};background:transparent;"); info.addWidget(why_l)
        h.addLayout(info, 1)
        s.heart = IconButton("wish", 30); s.heart.set_active(fav); s.heart.setToolTip(tr("tip.fav.heart"))
        s.heart.clicked.connect(s._flip); h.addWidget(s.heart, 0, Qt.AlignmentFlag.AlignTop)
    def _flip(s):
        s.heart.set_active(not s.heart.active); s.fav_toggled.emit(s.a["id"], s.b["id"], s.heart.active)
