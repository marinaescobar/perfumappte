"""Imagen propia de Góngora: un frasquito atomizador simpático con carita (sin género), plano y en los colores de la app.

Se dibuja con QPainter sobre una cuadrícula de 256x256; `pixmap()` lo entrega a cualquier tamaño y `tools/make_assets.py` lo guarda en `assets/gongora.png`.
"""
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QPen

SOFT, LILAC, DEEP, PLUM, MIST, BLUSH = "#EBDFF6", "#9a6fc4", "#6b4a8f", "#352447", "#c9b3e0", "#E8B7D4"


def _sparkle(cx, cy, r):
    p = QPainterPath(); k = r * 0.3
    p.moveTo(cx, cy - r); p.quadTo(cx + k, cy - k, cx + r, cy); p.quadTo(cx + k, cy + k, cx, cy + r)
    p.quadTo(cx - k, cy + k, cx - r, cy); p.quadTo(cx - k, cy - k, cx, cy - r); return p


def draw(p, rect, background=True):
    p.save(); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.topLeft()); p.scale(rect.width() / 256, rect.height() / 256); p.setPen(Qt.PenStyle.NoPen)
    if background: p.setBrush(QColor(SOFT)); p.drawEllipse(QRectF(0, 0, 256, 256))
    # destellos de perfume alrededor
    p.setBrush(QColor(MIST))
    for x, y, r in ((200, 74, 6), (218, 60, 4.5), (214, 88, 4), (228, 76, 3.5)): p.drawEllipse(QPointF(x, y), r, r)
    # tapón, collarín y cuerpo del frasco
    p.setBrush(QColor(PLUM)); p.drawRoundedRect(QRectF(102, 36, 52, 44), 13, 13)
    p.setBrush(QColor(DEEP)); p.drawRoundedRect(QRectF(92, 76, 72, 20), 8, 8)
    p.setBrush(QColor(LILAC)); p.drawRoundedRect(QRectF(58, 92, 140, 126), 36, 36)
    # brillo
    pen = QPen(QColor(255, 255, 255, 120), 7); pen.setCapStyle(Qt.PenCapStyle.RoundCap); p.setPen(pen); p.drawLine(QPointF(80, 126), QPointF(80, 160)); p.setPen(Qt.PenStyle.NoPen)
    # cara
    p.setBrush(QColor(PLUM)); p.drawEllipse(QPointF(110, 158), 7.5, 9.5); p.drawEllipse(QPointF(146, 158), 7.5, 9.5)
    p.setBrush(QColor(255, 255, 255)); p.drawEllipse(QPointF(112.5, 154.5), 2.6, 2.6); p.drawEllipse(QPointF(148.5, 154.5), 2.6, 2.6)
    p.setBrush(QColor(BLUSH)); p.setOpacity(0.85); p.drawEllipse(QPointF(92, 180), 11, 7); p.drawEllipse(QPointF(164, 180), 11, 7); p.setOpacity(1)
    smile = QPainterPath(); smile.moveTo(118, 180); smile.quadTo(128, 194, 138, 180)
    pen = QPen(QColor(PLUM), 6); pen.setCapStyle(Qt.PenCapStyle.RoundCap); p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(smile)
    # chispita
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(LILAC)); p.drawPath(_sparkle(58, 70, 13))
    p.restore()


def pixmap(size, background=True, dpr=2):
    pm = QPixmap(int(size * dpr), int(size * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.GlobalColor.transparent)
    q = QPainter(pm); draw(q, QRectF(0, 0, size, size), background); q.end(); return pm
