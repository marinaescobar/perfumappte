"""Iconos vectoriales del perfil (reloj, spray, estaciones, momentos y ocasiones).

Cada icono se dibuja sobre una cuadrícula de 24x24 en dos pasadas: primero apagado (todo el icono) y luego
encendido, recortado según `frac` (0..1). El reloj se llena como una tarta; el resto, de abajo arriba.
"""
import math
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QPolygonF, QColor


def _ink(p, col, w=1.7, fill=True):
    p.setPen(QPen(col, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(col if fill else Qt.BrushStyle.NoBrush)

def _poly(p, pts): p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

def _ray(p, cx, cy, a, r0, r1):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    p.drawLine(QPointF(cx + r0 * c, cy + r0 * s), QPointF(cx + r1 * c, cy + r1 * s))


def _clock(p, col, hole):
    _ink(p, col, 1.6, False); p.drawEllipse(QPointF(12, 12), 10, 10)       # esfera
    _ink(p, col); p.drawEllipse(QPointF(12, 12), 8.6, 8.6)
    _ink(p, hole, 1.7, False); p.drawLine(QPointF(12, 12), QPointF(12, 6.2)); p.drawLine(QPointF(12, 12), QPointF(16, 14.4))

def _spray(p, col, hole):
    """Chorro de un spray: gotitas que salen de un punto y se abren en abanico, cada vez más grandes y separadas."""
    _ink(p, col, 1.0)
    p.drawEllipse(QPointF(2.2, 12), 1.5, 1.5)                                                           # boquilla
    for ang, radii in ((0, (6.5, 12, 17.5, 22.5)), (-24, (8, 13.5, 19)), (24, (8, 13.5, 19)), (-46, (10.5, 16)), (46, (10.5, 16))):
        for i, r in enumerate(radii):
            a_ = math.radians(ang); sz = 0.95 + 0.38 * i + (0.25 if ang == 0 else 0)
            p.drawEllipse(QPointF(2.2 + r * math.cos(a_), 12 + r * math.sin(a_)), sz, sz)

def _sun(p, col, hole):
    _ink(p, col); p.drawEllipse(QPointF(12, 12), 4.4, 4.4)
    for k in range(8): _ray(p, 12, 12, k * 45, 7.2, 10)

def _spring(p, col, hole):                                   # flor
    _ink(p, col, 1.0)
    for k in range(5):
        a = math.radians(k * 72 - 90); p.drawEllipse(QPointF(12 + 4.6 * math.cos(a), 12 + 4.6 * math.sin(a)), 3.5, 3.5)
    _ink(p, hole, 1.0); p.drawEllipse(QPointF(12, 12), 2.2, 2.2)

def _autumn(p, col, hole):                                   # hoja
    _ink(p, col, 1.2)
    l = QPainterPath(); l.moveTo(4.5, 19.5); l.cubicTo(3.5, 9, 11, 3, 20.5, 3.8); l.cubicTo(21.5, 13.5, 15, 20.5, 4.5, 19.5); l.closeSubpath()
    p.drawPath(l); _ink(p, hole, 1.3, False); p.drawLine(QPointF(4.5, 19.5), QPointF(14, 10))

def _winter(p, col, hole):                                   # copo de nieve
    _ink(p, col, 1.8, False)
    for k in range(6):
        a = k * 60 - 90; _ray(p, 12, 12, a, 0, 10)
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); bx, by = 12 + 6.2 * c, 12 + 6.2 * s
        for d in (-50, 50):
            c2, s2 = math.cos(math.radians(a + d)), math.sin(math.radians(a + d))
            p.drawLine(QPointF(bx, by), QPointF(bx + 3 * c2, by + 3 * s2))

def _day(p, col, hole):                                      # sol sobre el horizonte
    _ink(p, col); path = QPainterPath(); path.moveTo(6.5, 17); path.arcTo(QRectF(6.5, 11.5, 11, 11), 180, -180); path.closeSubpath(); p.drawPath(path)
    _ink(p, col, 1.8, False); p.drawLine(QPointF(2.5, 17.5), QPointF(21.5, 17.5))
    for a in range(180, 361, 45): _ray(p, 12, 17, a, 8, 11)

def _night(p, col, hole):                                    # luna creciente
    _ink(p, col, 1.0); a = QPainterPath(); a.addEllipse(QPointF(12, 12), 9, 9)
    b = QPainterPath(); b.addEllipse(QPointF(17, 8.5), 7.6, 7.6); p.drawPath(a.subtracted(b))
    p.drawEllipse(QPointF(18.5, 17.5), 1, 1)

def _casual(p, col, hole):                                   # camiseta
    _ink(p, col, 1.2)
    _poly(p, [(9, 4), (3.5, 7.5), (6, 11.5), (8, 10.2), (8, 20.5), (16, 20.5), (16, 10.2), (18, 11.5), (20.5, 7.5), (15, 4), (13.6, 5.8), (10.4, 5.8)])

def _office(p, col, hole):                                   # maletín
    _ink(p, col, 1.5, False); p.drawRoundedRect(QRectF(8.8, 4.6, 6.4, 4.4), 1.4, 1.4)
    _ink(p, col, 1.2); p.drawRoundedRect(QRectF(3.2, 8, 17.6, 12), 2.2, 2.2)
    _ink(p, hole, 1.3, False); p.drawLine(QPointF(3.6, 13.6), QPointF(20.4, 13.6))

def _date(p, col, hole):                                     # corazón
    _ink(p, col, 1.2); h = QPainterPath(); h.moveTo(12, 20.5)
    h.cubicTo(1.5, 13, 3.5, 4.5, 9, 5); h.cubicTo(11, 5.2, 12, 6.8, 12, 8)
    h.cubicTo(12, 6.8, 13, 5.2, 15, 5); h.cubicTo(20.5, 4.5, 22.5, 13, 12, 20.5); p.drawPath(h)

def _formal(p, col, hole):                                   # pajarita
    _ink(p, col, 1.2); _poly(p, [(2.5, 7), (11, 12), (2.5, 17)]); _poly(p, [(21.5, 7), (13, 12), (21.5, 17)])
    p.drawRoundedRect(QRectF(9.8, 9, 4.4, 6), 1.4, 1.4)

def _party(p, col, hole):                                    # copa
    _ink(p, col, 1.2); _poly(p, [(4, 4.5), (20, 4.5), (12, 13.5)])
    _ink(p, col, 1.8, False); p.drawLine(QPointF(12, 13.5), QPointF(12, 20)); p.drawLine(QPointF(8, 20.4), QPointF(16, 20.4))

def _sport(p, col, hole):                                    # mancuerna
    _ink(p, col, 1.0)
    for x, w, y, h in ((2.6, 3, 8, 8), (5.8, 2.8, 5.8, 12.4), (15.4, 2.8, 5.8, 12.4), (18.4, 3, 8, 8)):
        p.drawRoundedRect(QRectF(x, y, w, h), 1.2, 1.2)
    p.drawRect(QRectF(8.6, 11, 6.8, 2))


def _venus(p, col, hole):
    _ink(p, col, 1.9, False); p.drawEllipse(QPointF(12, 8.8), 5.2, 5.2)
    p.drawLine(QPointF(12, 14), QPointF(12, 21.5)); p.drawLine(QPointF(8.8, 18), QPointF(15.2, 18))

def _mars(p, col, hole):
    _ink(p, col, 1.9, False); p.drawEllipse(QPointF(10, 14), 5.2, 5.2)
    p.drawLine(QPointF(13.7, 10.3), QPointF(20, 4)); p.drawLine(QPointF(14.6, 4), QPointF(20, 4)); p.drawLine(QPointF(20, 4), QPointF(20, 9.4))

def _unisex(p, col, hole):
    _ink(p, col, 1.8, False); p.drawEllipse(QPointF(11.5, 10), 4.6, 4.6)
    p.drawLine(QPointF(11.5, 14.6), QPointF(11.5, 21.5)); p.drawLine(QPointF(8.6, 18.2), QPointF(14.4, 18.2))
    p.drawLine(QPointF(14.8, 6.7), QPointF(20, 1.9)); p.drawLine(QPointF(15.6, 1.9), QPointF(20, 1.9)); p.drawLine(QPointF(20, 1.9), QPointF(20, 6.3))

def _own(p, col, hole):                                      # «lo tengo»: sello con visto
    _ink(p, col); p.drawEllipse(QPointF(12, 12), 10, 10)
    _ink(p, hole, 2.1, False)
    path = QPainterPath(); path.moveTo(7.2, 12.4); path.lineTo(10.6, 15.8); path.lineTo(16.8, 8.6); p.drawPath(path)


def _sparkle_path(cx, cy, r):
    p = QPainterPath(); k = r * 0.3
    p.moveTo(cx, cy - r); p.quadTo(cx + k, cy - k, cx + r, cy); p.quadTo(cx + k, cy + k, cx, cy + r)
    p.quadTo(cx - k, cy + k, cx - r, cy); p.quadTo(cx - k, cy - k, cx, cy - r); return p

def _nav_col(p, col, hole):                                   # frasco con corazón (Mi colección)
    _ink(p, col, 1.8, False); p.drawRoundedRect(QRectF(9.2, 2.6, 5.6, 3.6), 1.2, 1.2); p.drawLine(QPointF(12, 6.2), QPointF(12, 8.4))
    p.drawRoundedRect(QRectF(5.2, 8.4, 13.6, 13), 4.2, 4.2)
    h = QPainterPath(); h.moveTo(12, 18.2); h.cubicTo(8.6, 15.6, 9.2, 12.4, 11, 12.6); h.cubicTo(11.6, 12.7, 12, 13.2, 12, 13.6)
    h.cubicTo(12, 13.2, 12.4, 12.7, 13, 12.6); h.cubicTo(14.8, 12.4, 15.4, 15.6, 12, 18.2); _ink(p, col, 1.5, False); p.drawPath(h)

def _nav_find(p, col, hole):                                  # lupa (Descubrimientos)
    _ink(p, col, 1.9, False); p.drawEllipse(QPointF(10.2, 10.2), 6.6, 6.6); p.drawLine(QPointF(15.2, 15.2), QPointF(21, 21))

def _nav_rec(p, col, hole):                                   # destellos (Recomendaciones)
    _ink(p, col, 1.7, False); p.drawPath(_sparkle_path(10.5, 13.5, 8)); p.drawPath(_sparkle_path(18.6, 5.4, 3.8))

def _nav_set(p, col, hole):                                   # engranaje (Configuración)
    _ink(p, col, 1.8, False); p.drawEllipse(QPointF(12, 12), 3.2, 3.2); p.drawEllipse(QPointF(12, 12), 7, 7)
    for k in range(8): _ray(p, 12, 12, k * 45, 7, 10)

ICONS = {"nav_set": _nav_set, "nav_col": _nav_col, "nav_find": _nav_find, "nav_rec": _nav_rec, "clock": _clock, "spray": _spray, "venus": _venus, "mars": _mars, "unisex": _unisex, "own": _own, "wish": _date,
         "primavera": _spring, "verano": _sun, "otoño": _autumn, "invierno": _winter,
         "día": _day, "noche": _night,
         "casual": _casual, "oficina": _office, "cita": _date, "formal": _formal, "fiesta": _party, "deporte": _sport}
OCCASION_ICON = {"noche": "fiesta"}        # la ocasión «noche» es salir de copas; la luna es el momento del día


def draw(p, kind, rect, frac, on, off, hole):
    """Pinta el icono `kind` dentro de `rect`, relleno `frac` (0..1) con el color `on` sobre el fondo apagado `off`."""
    fn = ICONS[kind]; frac = max(0.0, min(1.0, float(frac or 0)))
    p.save(); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.topLeft()); p.scale(rect.width() / 24, rect.height() / 24)
    p.save(); fn(p, QColor(off), QColor(hole)); p.restore()                    # base apagada
    if frac > 0:
        p.save()
        if frac < 1:
            clip = QPainterPath()
            if kind == "clock":                                                # tarta desde las 12 en sentido horario
                clip.moveTo(12, 12); clip.arcTo(QRectF(0, 0, 24, 24), 90, -360 * frac); clip.closeSubpath()
            else:
                clip.addRect(QRectF(0, 24 * (1 - frac), 24, 24 * frac))
            p.setClipPath(clip)
        fn(p, QColor(on), QColor(hole)); p.restore()
    p.restore()
