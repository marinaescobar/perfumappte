"""Regenera las imágenes de assets/ (icono, logotipo y avatar de Góngora). Uso, desde la raíz del proyecto:  python -m tools.make_assets"""
import os
from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from core.paths import resource
from ui import avatar, logo


def main():
    app = QGuiApplication([])                        # hace falta para pintar y escribir imágenes con Qt
    folder = resource("assets"); os.makedirs(folder, exist_ok=True)
    logo.mark_pixmap(512, True, dpr=1).save(os.path.join(folder, "icon.png"))
    big = QImage(256, 256, QImage.Format.Format_ARGB32); big.fill(0)
    q = QPainter(big); logo.draw_mark(q, QRectF(0, 0, 256, 256)); q.end(); big.save(os.path.join(folder, "icon.ico"))
    logo.wordmark_pixmap(160, 2).save(os.path.join(folder, "logo.png"))
    try:
        from PyQt6.QtSvg import QSvgGenerator
        g = QSvgGenerator(); g.setFileName(os.path.join(folder, "icon.svg")); g.setSize(QSize(256, 256)); g.setViewBox(QRectF(0, 0, 256, 256))
        q = QPainter(g); logo.draw_mark(q, QRectF(0, 0, 256, 256)); q.end()
    except ImportError: pass
    avatar.pixmap(512, True, dpr=1).save(os.path.join(folder, "gongora.png"))
    print("Imágenes escritas en", folder); del app


if __name__ == "__main__":
    main()
