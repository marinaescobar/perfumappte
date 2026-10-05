"""Gráficos de «Mis gustos», dibujados con QPainter para que compartan la estética de la app (lila suave, esquinas redondas)."""
import math
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QSizePolicy
from ui import icons, theme
from ui.theme import ACCENT, ACCENT_HOVER, BAR_HOVER, BORDER, HOVER, ICON_OFF, MUTED, PALE, PALETTE, PANEL, TRACK, TXT     # se actualizan al cambiar de tema


def _font(p, px=12, bold=False):
    f = QFont(p.font()); f.setPixelSize(px); f.setBold(bold); p.setFont(f)


class Card(QFrame):
    """Tarjeta blanca redondeada con título y un widget de gráfico dentro."""
    def __init__(s, title, body, subtitle=""):
        super().__init__(); s.setObjectName("chartcard"); v = QVBoxLayout(s); v.setContentsMargins(18, 14, 18, 16); v.setSpacing(8)
        t = QLabel(title); t.setStyleSheet(f"font-weight:600;font-size:14px;color:{TXT};background:transparent;"); v.addWidget(t)
        if subtitle:
            u = QLabel(subtitle); u.setWordWrap(True); u.setStyleSheet(f"color:{MUTED};font-size:11px;background:transparent;"); v.addWidget(u)
        v.addWidget(body, 1)


class StatTile(QFrame):
    def __init__(s, value, caption):
        super().__init__(); s.setObjectName("chartcard"); v = QVBoxLayout(s); v.setContentsMargins(18, 12, 18, 12); v.setSpacing(0)
        a = QLabel(value); a.setStyleSheet(f"font-family:Georgia,serif;font-size:24px;font-weight:600;color:{ACCENT};background:transparent;")
        b = QLabel(caption); b.setStyleSheet(f"color:{MUTED};font-size:11px;background:transparent;"); b.setWordWrap(True); v.addWidget(a); v.addWidget(b)


class GenderTile(QFrame):
    """Ficha de género: iconos de trazo de icons.py (♀ ♂ ⚥ como texto cambiaban de peso según la tipografía) con su cuenta."""
    def __init__(s, items, caption):
        super().__init__(); s.setObjectName("chartcard"); s.items = items; s.caption = caption; s.setMinimumHeight(70)
    def sizeHint(s): return QSize(160, 70)
    def paintEvent(s, e):
        super().paintEvent(e); p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); x = 18
        for kind, n in s.items:
            icons.draw(p, kind, QRectF(x, 12, 28, 28), 1.0, ACCENT, ACCENT, PANEL); x += 32
            f = QFont("Georgia"); f.setPixelSize(22); f.setBold(True); p.setFont(f); p.setPen(QColor(ACCENT)); t = str(n)
            p.drawText(QPointF(x, 36), t); x += p.fontMetrics().horizontalAdvance(t) + 16
        _font(p, 11); p.setPen(QColor(MUTED)); p.drawText(QPointF(18, s.height() - 12), s.caption)


class HBars(QWidget):
    """Barras horizontales redondeadas. filas: dict(label, value, color, icon=None, text=None). Resalta la fila bajo el ratón."""
    ROW = 30
    hovered = pyqtSignal(int)                      # fila bajo el ratón (-1: ninguna)
    def __init__(s, rows, vmax=None):
        super().__init__(); s.sub = None; s.rows = rows; s.vmax = vmax or max((r["value"] for r in rows), default=1) or 1; s.hover = -1
        s.setMouseTracking(True); s.setMinimumHeight(max(1, len(rows)) * s.ROW + 4); s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    def sizeHint(s): return QSize(300, max(1, len(s.rows)) * s.ROW + 4)
    def mouseMoveEvent(s, e):
        i = int((e.position().y() - 3) // s.ROW); i = i if 0 <= i < len(s.rows) else -1
        if i != s.hover:
            s.hover = i; s.update(); s.setToolTip(f"{s.rows[i]['label']}: {s.rows[i].get('text') or s.rows[i]['value']}" if i >= 0 else ""); s.hovered.emit(i)
    def leaveEvent(s, e): s.hover = -1; s.update(); s.hovered.emit(-1)
    def set_highlight(s, sub): s.sub = sub; s.update()        # sub: parte de cada fila que aportan los perfumes resaltados (None: nada resaltado)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); _font(p, 12)
        lw = min(150, int(s.width() * 0.34)); vw = 44; x0 = lw + 8; x1 = s.width() - vw
        for i, r in enumerate(s.rows):
            y = i * s.ROW + 3; ix = 0
            if i == s.hover: p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(HOVER)); p.drawRoundedRect(QRectF(-4, y - 1, s.width() + 8, 26), 10, 10)
            if r.get("icon"):
                icons.draw(p, r["icon"], QRectF(0, y + 2, 20, 20), 1.0, ACCENT, ICON_OFF, PANEL); ix = 26
            p.setPen(QColor(TXT)); p.drawText(QRectF(ix, y, lw - ix, 24), int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                                              p.fontMetrics().elidedText(r["label"], Qt.TextElideMode.ElideRight, lw - ix))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(TRACK)); p.drawRoundedRect(QRectF(x0, y + 5, x1 - x0, 14), 7, 7)
            w = max(14.0, (x1 - x0) * r["value"] / s.vmax) if r["value"] > 0 else 0
            if w:
                p.setBrush(QColor(r.get("color") or ACCENT)); p.setOpacity(0.3 if s.sub is not None else 1.0); p.drawRoundedRect(QRectF(x0, y + 5, w, 14), 7, 7); p.setOpacity(1.0)
                if s.sub is not None and s.sub[i] > 0: p.drawRoundedRect(QRectF(x0, y + 5, min(w, max(14.0, (x1 - x0) * s.sub[i] / s.vmax)), 14), 7, 7)
            p.setPen(QColor(TXT if i == s.hover else MUTED)); p.drawText(QRectF(x1 + 6, y, vw - 6, 24), int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), r.get("text") or str(r["value"]))


class Donut(QWidget):
    """Anillo interactivo con leyenda a la derecha. datos: [(etiqueta, valor, color)].
    Al pasar el ratón por un sector (o por su fila de la leyenda) este se engrosa y el centro muestra su nombre y porcentaje."""
    LEG = 24
    hovered = pyqtSignal(int)
    def __init__(s, data, center=""):
        super().__init__(); s.sub = None; s.data = [d for d in data if d[1] > 0]; s.center = center; s.hover = -1
        s.setMouseTracking(True); s.setMinimumHeight(max(190, len(s.data) * s.LEG + 20))
    def _geom(s):
        d = min(s.height() - 24, 170, int(s.width() * 0.5)); th = d * 0.2; cx, cy = 12 + d / 2, s.height() / 2
        return d, th, QPointF(cx, cy), (d - th) / 2            # diámetro exterior, grosor, centro y radio de la línea media del anillo
    def _tot(s): return sum(v for _l, v, _c in s.data) or 1
    def _hit(s, pos):
        d, th, c, R = s._geom(); dx, dy = pos.x() - c.x(), pos.y() - c.y(); rad = math.hypot(dx, dy)
        if R - th * 0.75 <= rad <= R + th * 0.75:
            off = (math.degrees(math.atan2(-dy, dx)) * -1 + 90) % 360          # grados en sentido horario desde las 12
            acc = 0.0
            for i, (_l, v, _c) in enumerate(s.data):
                acc += 360.0 * v / s._tot()
                if off < acc: return i
        x = d + 36; y0 = (s.height() - len(s.data) * s.LEG) / 2
        if pos.x() >= x - 6 and y0 <= pos.y() < y0 + len(s.data) * s.LEG: return int((pos.y() - y0) // s.LEG)
        return -1
    def mouseMoveEvent(s, e):
        i = s._hit(e.position())
        if i != s.hover:
            s.hover = i; s.update(); s.hovered.emit(i)
            s.setToolTip(f"{s.data[i][0]}: {round(100 * s.data[i][1] / s._tot())}%" if i >= 0 else "")
    def leaveEvent(s, e): s.hover = -1; s.update(); s.hovered.emit(-1)
    def set_highlight(s, sub): s.sub = sub; s.update()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); tot = s._tot(); d, th, c, R = s._geom()
        rect = QRectF(c.x() - R, c.y() - R, 2 * R, 2 * R); a = 90.0; gap = 2.5 if len(s.data) > 1 else 0
        for i, (lab, v, col) in enumerate(s.data):
            span = 360.0 * v / tot; path = QPainterPath(); path.arcMoveTo(rect, a); path.arcTo(rect, a, -span + gap)
            on = i == s.hover; pen = QPen(QColor(col), th * (1.16 if on else 1.0)); pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); p.setOpacity(0.28 if s.sub is not None else 0.5 if (s.hover >= 0 and not on) else 1.0); p.drawPath(path)
            if s.sub is not None and s.sub[i] > 0 and span - gap > 0:        # la parte de este sector que aportan los perfumes resaltados
                part = QPainterPath(); part.arcMoveTo(rect, a); part.arcTo(rect, a, -(span - gap) * min(1.0, s.sub[i] / v))
                p.setOpacity(1.0); p.drawPath(part)
            a -= span
        p.setOpacity(1.0); inner = QRectF(c.x() - R + th * 0.7, c.y() - R + th * 0.7, 2 * (R - th * 0.7), 2 * (R - th * 0.7))
        if s.hover >= 0:
            lab, v, col = s.data[s.hover]
            p.setPen(QColor(col if col not in PALE else ACCENT)); _font(p, 22, True)
            p.drawText(QRectF(inner.left(), inner.center().y() - 22, inner.width(), 28), int(Qt.AlignmentFlag.AlignCenter), f"{round(100 * v / tot)}%")
            p.setPen(QColor(TXT)); _font(p, 11); p.drawText(QRectF(inner.left(), inner.center().y() + 6, inner.width(), 18), int(Qt.AlignmentFlag.AlignCenter),
                                                            p.fontMetrics().elidedText(lab, Qt.TextElideMode.ElideRight, int(inner.width())))
        else:
            p.setPen(QColor(TXT)); _font(p, 24, True); p.drawText(inner, int(Qt.AlignmentFlag.AlignCenter), s.center)
        _font(p, 12); x = d + 36; y = (s.height() - len(s.data) * s.LEG) / 2
        for i, (lab, v, col) in enumerate(s.data):
            on = i == s.hover
            if on: p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(HOVER)); p.drawRoundedRect(QRectF(x - 8, y, s.width() - x - 4, s.LEG), 10, 10)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(col)); p.drawEllipse(QRectF(x, y + 7, 10, 10))
            p.setPen(QColor(TXT)); t = p.fontMetrics().elidedText(lab, Qt.TextElideMode.ElideRight, max(40, int(s.width() - x - 70)))
            p.drawText(QPointF(x + 18, y + 17), t); p.setPen(QColor(TXT if on else MUTED))
            p.drawText(QRectF(s.width() - 56, y, 48, s.LEG), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), f"{round(100 * v / tot)}%")
            y += s.LEG


class ProfileStrips(QWidget):
    """Un carril por eje del perfil: un punto por perfume y un marcador grande con la media. ejes: [(izq, der, [valores], media)]."""
    ROW = 66
    def __init__(s, axes):
        super().__init__(); s.axes = axes; s.setMinimumHeight(len(axes) * s.ROW + 4)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); _font(p, 12)
        x0, x1 = 14, s.width() - 14
        for i, (l, r, vals, avg) in enumerate(s.axes):
            y = i * s.ROW + 14
            p.setPen(QColor(MUTED)); p.drawText(QPointF(x0 - 4, y), l); p.drawText(QPointF(x1 - p.fontMetrics().horizontalAdvance(r) + 4, y), r)
            cy = y + 24; pen = QPen(QColor(TRACK), 8); pen.setCapStyle(Qt.PenCapStyle.RoundCap); p.setPen(pen); p.drawLine(QPointF(x0, cy), QPointF(x1, cy))
            p.setPen(Qt.PenStyle.NoPen)
            for v in vals:
                p.setBrush(QColor(154, 111, 196, 90)); p.drawEllipse(QPointF(x0 + (x1 - x0) * v / 100, cy), 6, 6)
            cx = x0 + (x1 - x0) * avg / 100
            p.setBrush(QColor(PANEL)); p.drawEllipse(QPointF(cx, cy), 11, 11); p.setBrush(QColor(ACCENT)); p.drawEllipse(QPointF(cx, cy), 8, 8)


class Scatter(QWidget):
    """Duración (x) frente a estela (y) de cada perfume. puntos: [(x 0..1, y 0..1, nombre)]. Tooltip con el nombre al acercar el ratón."""
    hovered = pyqtSignal(int)
    def __init__(s, points, xl, yl, lo_hi):
        super().__init__(); s.sel = None; s.cur = -1; s.points, s.xl, s.yl, s.lh = points, xl, yl, lo_hi; s.setMinimumHeight(230); s.setMouseTracking(True)
    def _area(s): return QRectF(34, 8, s.width() - 46, s.height() - 44)
    def _pos(s, x, y):
        a = s._area(); return QPointF(a.left() + a.width() * (0.06 + 0.88 * x), a.bottom() - a.height() * (0.06 + 0.88 * y))
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); a = s._area(); _font(p, 11)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(HOVER)); p.drawRoundedRect(a, 14, 14)
        p.setPen(QPen(QColor(BORDER), 1, Qt.PenStyle.DashLine)); p.drawLine(QPointF(a.center().x(), a.top() + 8), QPointF(a.center().x(), a.bottom() - 8))
        p.drawLine(QPointF(a.left() + 8, a.center().y()), QPointF(a.right() - 8, a.center().y()))
        p.setPen(QColor(MUTED)); lo, hi = s.lh
        p.drawText(QRectF(a.left(), a.bottom() + 4, 60, 16), int(Qt.AlignmentFlag.AlignLeft), lo); p.drawText(QRectF(a.right() - 60, a.bottom() + 4, 60, 16), int(Qt.AlignmentFlag.AlignRight), hi)
        p.drawText(QRectF(a.left(), a.bottom() + 4, a.width(), 16), int(Qt.AlignmentFlag.AlignHCenter), s.xl)
        p.save(); p.translate(12, a.center().y() + 20); p.rotate(-90); p.drawText(QPointF(0, 0), s.yl); p.restore()
        p.setPen(QPen(QColor(PANEL), 2))
        c = QColor(ACCENT)
        for i, (x, y, _n) in enumerate(s.points):
            on = s.sel is not None and i in s.sel; c.setAlpha(170 if s.sel is None else 235 if on else 45); p.setBrush(c); p.drawEllipse(s._pos(x, y), 9 if on else 8, 9 if on else 8)
    def set_highlight(s, sel): s.sel = sel; s.update()          # sel: índices de los puntos resaltados
    def leaveEvent(s, e): s.cur = -1; s.hovered.emit(-1)
    def mouseMoveEvent(s, e):
        best, bd, bi = "", 14, -1
        for i, (x, y, n) in enumerate(s.points):
            d = math.hypot(s._pos(x, y).x() - e.position().x(), s._pos(x, y).y() - e.position().y())
            if d < bd: best, bd, bi = n, d, i
        if best != s.toolTip(): s.setToolTip(best)
        if bi != s.cur: s.cur = bi; s.hovered.emit(bi)


class VBars(QWidget):
    """Columnas redondeadas con el valor encima; resalta la columna bajo el ratón. datos: [(etiqueta, valor)]."""
    hovered = pyqtSignal(int)
    def __init__(s, data):
        super().__init__(); s.sub = None; s.data = data; s.hover = -1; s.setMouseTracking(True); s.setMinimumHeight(190)
    def _cols(s):
        n = max(1, len(s.data)); gap = 12; bw = min(54.0, (s.width() - gap * (n + 1)) / n); x = (s.width() - (n * bw + (n - 1) * gap)) / 2
        return [(x + i * (bw + gap), bw) for i in range(len(s.data))]
    def mouseMoveEvent(s, e):
        i = next((k for k, (x, bw) in enumerate(s._cols()) if x - 6 <= e.position().x() <= x + bw + 6), -1)
        if i != s.hover: s.hover = i; s.update(); s.setToolTip(f"{s.data[i][0]}: {s.data[i][1]}" if i >= 0 else ""); s.hovered.emit(i)
    def leaveEvent(s, e): s.hover = -1; s.update(); s.hovered.emit(-1)
    def set_highlight(s, sub): s.sub = sub; s.update()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); _font(p, 11)
        m = max((v for _l, v in s.data), default=1) or 1; base = s.height() - 22; top = 22
        for i, ((lab, v), (x, bw)) in enumerate(zip(s.data, s._cols())):
            h = (base - top) * v / m if v else 0; on = i == s.hover
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(BAR_HOVER if on else TRACK)); p.drawRoundedRect(QRectF(x, top, bw, base - top), 10, 10)
            if h:
                p.setBrush(QColor(ACCENT_HOVER if on else ACCENT)); p.setOpacity(0.3 if s.sub is not None else 1.0); p.drawRoundedRect(QRectF(x, base - max(h, 14), bw, max(h, 14)), 10, 10); p.setOpacity(1.0)
                if s.sub is not None and s.sub[i] > 0: hs = max(14.0, (base - top) * s.sub[i] / m); p.drawRoundedRect(QRectF(x, base - hs, bw, hs), 10, 10)
            p.setPen(QColor(TXT)); _font(p, 11, True); p.drawText(QRectF(x - 10, base - max(h, 14) - 20, bw + 20, 18), int(Qt.AlignmentFlag.AlignHCenter), str(v)); _font(p, 11)
            p.setPen(QColor(MUTED)); p.drawText(QRectF(x - 14, base + 4, bw + 28, 16), int(Qt.AlignmentFlag.AlignHCenter), lab)


class Radar(QWidget):
    """Perfil olfativo en radar: un eje por cada extremo de los tres ejes del perfil (los opuestos quedan enfrentados). Cada perfume es una forma tenue,
    la media de la colección va en sólido y, si se resalta un grupo de perfumes, su media sale con trazo grueso. perfumes: [[0..1 por polo]]."""
    def __init__(s, labels, perfumes):
        super().__init__(); s.labels, s.pf, s.sel = labels, perfumes, None; s.setMinimumHeight(300)
        s.avg = [sum(v[i] for v in perfumes) / len(perfumes) for i in range(len(labels))]
    def set_highlight(s, sel): s.sel = sel; s.update()          # sel: índices de los perfumes resaltados
    def _poly(s, vals, c, r):
        n = len(vals); poly = QPolygonF()
        for i, v in enumerate(vals):
            a = math.radians(-90 + 360 * i / n); poly.append(QPointF(c.x() + r * v * math.cos(a), c.y() + r * v * math.sin(a)))
        return poly
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing); _font(p, 11); n = len(s.labels)
        c = QPointF(s.width() / 2, s.height() / 2 + 2); r = max(40.0, min(s.width() / 2 - 78, s.height() / 2 - 30))
        p.setPen(QPen(QColor(BORDER), 1)); p.setBrush(Qt.BrushStyle.NoBrush)
        for k in (0.25, 0.5, 0.75, 1.0): p.drawPolygon(s._poly([k] * n, c, r))
        for i, lab in enumerate(s.labels):
            a = math.radians(-90 + 360 * i / n); ca, sa = math.cos(a), math.sin(a); p.setPen(QPen(QColor(BORDER), 1)); p.drawLine(c, QPointF(c.x() + r * ca, c.y() + r * sa))
            tw = p.fontMetrics().horizontalAdvance(lab); tx, ty = c.x() + (r + 10) * ca, c.y() + (r + 10) * sa
            p.setPen(QColor(TXT)); p.drawText(QPointF(tx - tw / 2 + ca * tw / 2, ty + 4 + sa * 6), lab)
        hl = s.sel is not None
        for i, vals in enumerate(s.pf):                       # una forma tenue por perfume (más marcada si está resaltado)
            on = hl and i in s.sel; col = QColor(ACCENT); col.setAlpha(70 if on else 10 if hl else 22)
            p.setPen(QPen(QColor(ACCENT), 1.2) if on else Qt.PenStyle.NoPen); p.setBrush(col); p.drawPolygon(s._poly(vals, c, r))
        fill = QColor(ACCENT); fill.setAlpha(40 if hl else 85)
        pen = QPen(QColor(ACCENT), 2); pen.setStyle(Qt.PenStyle.DashLine if hl else Qt.PenStyle.SolidLine); p.setPen(pen); p.setBrush(fill); p.drawPolygon(s._poly(s.avg, c, r))
        if hl and s.sel:
            sub = [sum(s.pf[j][i] for j in s.sel) / len(s.sel) for i in range(n)]; f2 = QColor(TXT); f2.setAlpha(60)
            p.setPen(QPen(QColor(TXT), 2.5)); p.setBrush(f2); p.drawPolygon(s._poly(sub, c, r))
