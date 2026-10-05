"""Widgets pequeños y reutilizables: tooltip propio, iconos, desplegable multiselección y selector de idioma."""
import html
import math
import re
from PyQt6 import sip
from PyQt6.QtCore import QEvent, QObject, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QGuiApplication, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QTextDocument
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QFrame, QGraphicsDropShadowEffect, QLabel, QPushButton,
                             QScrollArea, QTabBar, QVBoxLayout, QWidget)
from core import i18n
from core.i18n import tr
from ui import icons, theme
from ui.theme import (ACCENT, ACCENT_HOVER, ICON_OFF, ICON_OFF_HOVER, PANEL, SHADOW, TIP_BODY, TIP_BORDER, TIP_BOT, TIP_TITLE, TIP_TOP)

def _tip_markup(text):
    """Texto del tooltip -> HTML: primera línea como título lila con una chispa, el resto como cuerpo."""
    if not Qt.mightBeRichText(text): text = html.escape(text).replace("\n", "<br>")
    head, sep, rest = text.partition("<br>")
    if not sep:
        if re.fullmatch(r"\s*<b>.*</b>\s*", head, re.S): rest = ""
        else: head, rest = "", head
    head = re.sub(r"</?b>", "", head)
    out = f"<span style='color:{ACCENT}'>✦</span>&nbsp;<span style='color:{TIP_TITLE};font-weight:600'>{head}</span>" if head else ""
    if rest: out += ("<br>" if head else "") + f"<span style='color:{TIP_BODY}'>{rest}</span>"
    return out

class Tip(QWidget):
    """Tooltip propio: tarjeta lila muy clara de esquinas redondas, sombra suave y aparición con fundido."""
    M = 12                                                   # margen transparente donde se pinta la sombra
    def __init__(s):
        super().__init__(None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        s.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); s.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        s.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        s.lab = QLabel(s); s.lab.setTextFormat(Qt.TextFormat.RichText); s.lab.setWordWrap(True); s.lab.setStyleSheet("background:transparent;font-size:12px;")
        v = QVBoxLayout(s); v.setContentsMargins(s.M + 14, s.M + 9, s.M + 14, s.M + 10); v.addWidget(s.lab)
        s.fade = QPropertyAnimation(s, b"windowOpacity", s); s.fade.setDuration(150)
        s.poll = QTimer(s); s.poll.setInterval(250); s.poll.timeout.connect(s._check); s.origin = QPoint()
    def show_at(s, text, gpos):
        html_ = _tip_markup(text); doc = QTextDocument(); f = QFont(s.lab.font()); f.setPixelSize(12); doc.setDefaultFont(f); doc.setHtml(html_)
        s.lab.setText(html_); s.lab.setFixedWidth(min(270, int(doc.idealWidth()) + 4)); s.adjustSize()
        scr = QGuiApplication.screenAt(gpos) or QGuiApplication.primaryScreen(); g = scr.availableGeometry()
        x = min(gpos.x() + 12 - s.M, g.right() - s.width()); y = gpos.y() + 20 - s.M
        if y + s.height() > g.bottom(): y = gpos.y() - s.height() + s.M - 8
        s.move(max(g.left(), x), max(g.top(), y)); s.origin = gpos
        if not s.isVisible():
            s.setWindowOpacity(0.0); s.show(); s.fade.stop(); s.fade.setStartValue(0.0); s.fade.setEndValue(1.0); s.fade.start()
        s.poll.start()
    def hide_(s):
        try:
            s.poll.stop()
            if s.isVisible(): s.hide()
        except RuntimeError: pass                            # el QTimer/ventana ya se destruyó (cierre de la app)
    def _check(s):
        if (QCursor.pos() - s.origin).manhattanLength() > 45: s.hide_()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setPen(Qt.PenStyle.NoPen)
        r = QRectF(s.rect()).adjusted(s.M, s.M, -s.M, -s.M)
        for i in range(s.M, 0, -1):                          # sombra violeta difuminada
            p.setBrush(QColor(*SHADOW, 3)); p.drawRoundedRect(r.adjusted(-i, -i + 3, i, i + 3), 14 + i, 14 + i)
        g = QLinearGradient(r.topLeft(), r.bottomLeft()); g.setColorAt(0, QColor(TIP_TOP)); g.setColorAt(1, QColor(TIP_BOT))
        p.setPen(QPen(QColor(TIP_BORDER), 1)); p.setBrush(g); p.drawRoundedRect(r, 14, 14)

class TipFilter(QObject):
    """Sustituye los tooltips de toda la aplicación por `Tip`."""
    HIDE = (QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick, QEvent.Type.KeyPress,
            QEvent.Type.Wheel, QEvent.Type.WindowDeactivate, QEvent.Type.FocusOut)
    def __init__(s, parent=None): super().__init__(parent); s.tip = Tip()
    def shutdown(s):
        """Al cerrar: la ventana del tooltip no puede sobrevivir a la QApplication."""
        app = QApplication.instance()
        if app is not None: app.removeEventFilter(s)         # sin filtro de Python vivo mientras Qt destruye sus objetos
        if s.tip is not None: s.tip.hide_(); sip.delete(s.tip); s.tip = None
    def eventFilter(s, o, e):
        if s.tip is None: return False
        t = e.type()
        if t == QEvent.Type.ToolTip and isinstance(o, QWidget):
            text = o.toolTip()
            if isinstance(o, QTabBar): i = o.tabAt(e.pos()); text = o.tabToolTip(i) if i >= 0 else ""
            if not text: s.tip.hide_(); return False
            s.tip.show_at(text, e.globalPos()); return True
        if t in s.HIDE: s.tip.hide_()
        return False

def install_tips(app):
    f = app._tipf = TipFilter(app); app.installEventFilter(f); app.aboutToQuit.connect(f.shutdown)

class IconMeter(QWidget):
    """Icono (de icons.py) relleno `frac` (0..1) con su explicación en el tooltip."""
    def __init__(s, kind, frac, tip, size=26):
        super().__init__(); s.kind, s.frac, s.size = kind, frac, size
        s.setFixedSize(size + 4, size + 4); s.setToolTip(tip)
    def set(s, kind, frac, tip=""): s.kind, s.frac = kind, frac; s.setToolTip(tip); s.update()
    def paintEvent(s, e):
        p = QPainter(s); icons.draw(p, s.kind, QRectF(2, 2, s.size, s.size), s.frac, ACCENT, ICON_OFF, PANEL)

class IconButton(QAbstractButton):
    """Botón de icono sin marco, del mismo estilo que los relojes: apagado en lila, encendido en el acento."""
    def __init__(s, kind, size=30):
        super().__init__(); s.kind, s.size, s.active, s.hover = kind, size, False, False
        s.setFixedSize(size + 4, size + 4); s.setCursor(Qt.CursorShape.PointingHandCursor)
    def set_active(s, on): s.active = bool(on); s.update()
    def enterEvent(s, e): s.hover = True; s.update()
    def leaveEvent(s, e): s.hover = False; s.update()
    def paintEvent(s, e):
        p = QPainter(s)
        on = ACCENT_HOVER if s.hover else ACCENT; off = ICON_OFF_HOVER if s.hover else ICON_OFF
        icons.draw(p, s.kind, QRectF(2, 2, s.size, s.size), 1.0 if s.active else 0.0, on, off, PANEL)

def tip_html(title, body=""):
    return f"<b>{html.escape(title)}</b>" + (f"<br>{body}" if body else "")

class MultiSelect(QPushButton):
    """Desplegable de selección múltiple (o simple con `single=True`): botón con el resumen y una tarjeta lila con casillas."""
    changed = pyqtSignal()
    def __init__(s, title="", single=False):
        super().__init__(); s.setObjectName("ms"); s.title, s.items, s.sel, s.pop, s.single = title, [], [], None, single
        s.setCursor(Qt.CursorShape.PointingHandCursor); s.setMinimumWidth(150); s.clicked.connect(s.open_)
    def set_items(s, items, title=None):
        s.items = [(v, l[:1].upper() + l[1:]) for v, l in items]; s.title = s.title if title is None else title
        known = {v for v, _ in s.items}; s.sel = [v for v in s.sel if v in known]; s._text()
    def values(s): return list(s.sel)
    def clear(s): s.sel = []; s._text()
    def _text(s):
        names = ", ".join(l for v, l in s.items if v in s.sel)
        s.setText(s.fontMetrics().elidedText(f"{s.title}: {names}", Qt.TextElideMode.ElideRight, max(120, s.width() - 44)) + "  ▾" if names else f"{s.title}  ▾")
    def _toggle(s, v, on, b, label):
        if s.single:
            if on:
                s.sel = [v]
                for ob in s.btns:
                    if ob is not b and ob.isChecked(): ob.blockSignals(True); ob.setChecked(False); ob.blockSignals(False)
            else: s.sel = []
            s._text(); s.changed.emit()
            if on and s.pop: s.pop.close()
            return
        if on and v not in s.sel: s.sel.append(v)
        if not on and v in s.sel: s.sel.remove(v)
        b.setText(("✓   " if on else "      ") + label); s._text(); s.changed.emit()
    def open_(s):
        pop = QWidget(s, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        pop.setObjectName("mspopw"); pop.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        lay = QVBoxLayout(pop); lay.setContentsMargins(12, 4, 12, 18)
        card = QFrame(); card.setObjectName("mspop"); sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(24); sh.setOffset(0, 4); sh.setColor(QColor(*SHADOW, 80)); card.setGraphicsEffect(sh)
        cl = QVBoxLayout(card); cl.setContentsMargins(8, 8, 8, 8); cl.setSpacing(2); s.btns = []
        inner = QWidget(); inner.setStyleSheet("background:transparent;"); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 0, 0); il.setSpacing(2)
        for v, l in s.items:
            on = v in s.sel; b = QPushButton((("✓   " if on else "      ") if not s.single else "") + l); b.setObjectName("opt"); b.setCheckable(True); b.setChecked(on)
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.toggled.connect(lambda on, v=v, b=b, l=l: s._toggle(v, on, b, l)); il.addWidget(b); s.btns.append(b)
        if len(s.items) > 9:
            sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame); sc.setFixedHeight(340); sc.setWidget(inner)
            sc.setStyleSheet("QScrollArea{background:transparent;}"); sc.viewport().setStyleSheet("background:transparent;"); cl.addWidget(sc)
        else: cl.addWidget(inner)
        lay.addWidget(card); pop.setMinimumWidth(max(s.width() + 24, 200)); pop.adjustSize()
        pop.move(s.mapToGlobal(QPoint(-12, s.height() - 4))); s.pop = pop; pop.show()

def flag_icon(code, w=30, h=20):
    """Bandera dibujada a mano (Windows no pinta los emojis de banderas): es -> España, en -> Reino Unido."""
    pm = QPixmap(w * 2, h * 2); pm.fill(Qt.GlobalColor.transparent); p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    W, H = w * 2, h * 2; clip = QPainterPath(); clip.addRoundedRect(QRectF(0, 0, W, H), 8, 8); p.setClipPath(clip)
    if code == "es":
        p.fillRect(0, 0, W, H, QColor("#AA151B")); p.fillRect(0, H // 4, W, H // 2, QColor("#F1BF00"))
    else:
        p.fillRect(0, 0, W, H, QColor("#012169"))
        for wd, col in ((9, "#FFFFFF"), (4, "#C8102E")): p.setPen(QPen(QColor(col), wd)); p.drawLine(0, 0, W, H); p.drawLine(0, H, W, 0)
        p.setPen(QPen(QColor("#FFFFFF"), 14)); p.drawLine(W // 2, 0, W // 2, H); p.drawLine(0, H // 2, W, H // 2)
        p.setPen(QPen(QColor("#C8102E"), 8)); p.drawLine(W // 2, 0, W // 2, H); p.drawLine(0, H // 2, W, H // 2)
    p.setClipping(False); p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(QColor(0, 0, 0, 40), 1.5)); p.drawRoundedRect(QRectF(.75, .75, W - 1.5, H - 1.5), 8, 8); p.end()
    return QIcon(pm)

class ThemeToggle(QWidget):
    """Interruptor claro / oscuro con dos mitades (sol y luna): la del tema activo se rellena con el acento."""
    picked = pyqtSignal(str)
    W, H = 76, 36
    def __init__(s):
        super().__init__(); s.mode = "light"; s.setFixedSize(s.W, s.H); s.setCursor(Qt.CursorShape.PointingHandCursor); s.setMouseTracking(True)
    def set_mode(s, mode): s.mode = mode; s.update()
    def _half(s, x): return "light" if x < s.W / 2 else "dark"
    def mouseMoveEvent(s, e):
        tip = tr("tip.theme." + s._half(e.position().x()))
        if tip != s.toolTip(): s.setToolTip(tip)
    def mousePressEvent(s, e):
        m = s._half(e.position().x())
        if m != s.mode: s.picked.emit(m)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); r = QRectF(s.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(QPen(QColor(theme.BORDER), 1)); p.setBrush(QColor(theme.PANEL)); p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        hw = r.width() / 2; dark = s.mode == "dark"
        knob = QRectF(r.left() + 3 + (hw if dark else 0), r.top() + 3, hw - 6, r.height() - 6)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(theme.GOLD)); p.drawRoundedRect(knob, knob.height() / 2, knob.height() / 2)
        for i, kind in enumerate(("sun", "moon")):
            c = QPointF(r.left() + hw * i + hw / 2, r.center().y()); on = (kind == "moon") == dark
            s._icon(p, kind, c, QColor("white") if on else QColor(theme.MUTED))
    @staticmethod
    def _icon(p, kind, c, col):
        pen = QPen(col, 1.7); pen.setCapStyle(Qt.PenCapStyle.RoundCap); p.setPen(pen)
        if kind == "sun":
            p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(c, 3.6, 3.6)
            for k in range(8):
                a = math.radians(k * 45); p.drawLine(QPointF(c.x() + 6 * math.cos(a), c.y() + 6 * math.sin(a)), QPointF(c.x() + 8 * math.cos(a), c.y() + 8 * math.sin(a)))
        else:
            moon = QPainterPath(); moon.addEllipse(c, 7, 7); cut = QPainterPath(); cut.addEllipse(QPointF(c.x() + 4.2, c.y() - 3.2), 6, 6)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(col); p.drawPath(moon.subtracted(cut))

class LangPicker(QPushButton):
    """Selector de idioma: muestra la bandera del idioma activo y al pulsarlo despliega las banderas disponibles."""
    picked = pyqtSignal(str)
    NAMES = {"es": "Español", "en": "English"}
    def __init__(s):
        super().__init__(); s.setObjectName("ms"); s.code = "es"; s.pop = None
        s.setIconSize(QSize(30, 20)); s.setCursor(Qt.CursorShape.PointingHandCursor); s.setFixedSize(66, 36); s.clicked.connect(s.open_)
    def set_code(s, code): s.code = code; s.setIcon(flag_icon(code)); s.setText("  ▾")
    def open_(s):
        pop = QWidget(s, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        pop.setObjectName("mspopw"); pop.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        lay = QVBoxLayout(pop); lay.setContentsMargins(12, 4, 12, 18)
        card = QFrame(); card.setObjectName("mspop"); sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(24); sh.setOffset(0, 4); sh.setColor(QColor(*SHADOW, 80)); card.setGraphicsEffect(sh)
        cl = QVBoxLayout(card); cl.setContentsMargins(8, 8, 8, 8); cl.setSpacing(2)
        for code in i18n.LANGS:
            b = QPushButton("  " + s.NAMES.get(code, code)); b.setObjectName("opt"); b.setCheckable(True); b.setChecked(code == s.code)
            b.setIcon(flag_icon(code)); b.setIconSize(QSize(30, 20)); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, c=code: (pop.close(), s.picked.emit(c)))
            cl.addWidget(b)
        lay.addWidget(card); pop.setMinimumWidth(max(s.width() + 24, 170)); pop.adjustSize()
        pop.move(s.mapToGlobal(QPoint(s.width() + 12 - pop.width(), s.height() - 4))); s.pop = pop; pop.show()
