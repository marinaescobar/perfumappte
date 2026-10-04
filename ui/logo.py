"""Logo de Perfúmappte: un frasco de perfume minimalista (la versión sin cara del frasco de Góngora) y el nombre en letra normal.

Plano y sin degradados: lila (#9a6fc4), ciruela (#352447) y blanco. Todo se dibuja con QPainterPath sobre una cuadrícula de 256x256,
así que sirve igual para el icono de la ventana, la barra lateral y los ficheros de `assets/` (ver `tools/make_assets.py`).
"""
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPixmap, QIcon, QFont, QFontMetricsF, QPen

LILAC, PLUM, DEEP, PALE, MIST = "#9a6fc4", "#352447", "#6b4a8f", "#F1EAF8", "#c9b3e0"


def _rr(x, y, w, h, r):
    p = QPainterPath(); p.addRoundedRect(QRectF(x, y, w, h), r, r); return p


def sparkle(cx, cy, r):
    p = QPainterPath(); k = r * 0.3
    p.moveTo(cx, cy - r); p.quadTo(cx + k, cy - k, cx + r, cy); p.quadTo(cx + k, cy + k, cx, cy + r)
    p.quadTo(cx - k, cy + k, cx - r, cy); p.quadTo(cx - k, cy - k, cx, cy - r); return p


def draw_mark(p, rect, tile=True):
    """Pinta el frasco dentro de `rect`. Con `tile` va en blanco sobre un cuadrado lila de esquinas redondeadas (icono de la app);
    sin él, en lila sobre fondo transparente (junto al nombre)."""
    p.save(); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(rect.topLeft()); p.scale(rect.width() / 256, rect.height() / 256); p.setPen(Qt.PenStyle.NoPen)
    if tile: p.setBrush(QColor(LILAC)); p.drawRoundedRect(QRectF(0, 0, 256, 256), 58, 58)
    body, collar, spark = (QColor("#FFFFFF"), QColor(PALE), QColor("#FFFFFF")) if tile else (QColor(LILAC), QColor(DEEP), QColor(MIST))
    p.setBrush(body); p.drawPath(_rr(62, 98, 132, 128, 40))                      # cuerpo
    p.setBrush(collar); p.drawPath(_rr(98, 80, 60, 24, 8))                       # collarín
    p.setBrush(QColor(PLUM)); p.drawPath(_rr(106, 38, 44, 48, 12))               # tapón
    if rect.width() >= 28:                                                       # brillo y chispa: a tamaños diminutos solo estorban
        pen = QPen(QColor(154, 111, 196, 90) if tile else QColor(255, 255, 255, 140), 8); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.drawLine(QPointF(86, 134), QPointF(86, 172)); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(spark); p.drawPath(sparkle(214, 70, 18))
    p.restore()


def mark_pixmap(size, tile=True, dpr=2):
    pm = QPixmap(int(size * dpr), int(size * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm); draw_mark(p, QRectF(0, 0, size, size), tile); p.end(); return pm


def app_icon():
    ic = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256): ic.addPixmap(mark_pixmap(s, True, dpr=1))
    return ic


def wordmark_pixmap(height=48, dpr=2):
    """Logotipo horizontal: el frasco y «Perfúmappte» en letra normal."""
    f = QFont("Segoe UI"); f.setPixelSize(int(height * 0.5)); fm = QFontMetricsF(f)
    gap = height * 0.12; text_w = fm.horizontalAdvance("Perfúmappte"); w = height * 0.82 + gap + text_w + height * 0.1
    pm = QPixmap(int(w * dpr), int(height * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    draw_mark(p, QRectF(-height * 0.1, -height * 0.02, height * 1.02, height * 1.02), tile=False)
    p.setFont(f); p.setPen(QColor(PLUM)); p.drawText(QPointF(height * 0.82 + gap, height * 0.5 + fm.ascent() / 2 - fm.descent() / 2 + height * 0.03), "Perfúmappte")
    p.end(); return pm
