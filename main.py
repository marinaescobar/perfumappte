"""Perfúmappte: arranque de la aplicación.

    python main.py              abre la aplicación
    Perfumappte.exe --selftest  comprobación sin ventana del ejecutable (escribe selftest.log en la carpeta de datos)
"""
import os, sys, threading, time, traceback
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox
from core import db, i18n
from core.i18n import tr
from ui import images, logo, theme
from ui.mainwindow import Main, apply_tooltip_palette
from ui.widgets import install_tips


def _hook(t, v, tb):
    """Errores inesperados: se muestran, y quedan en error.log (carpeta de datos) para poder revisarlos con la app instalada."""
    text = "".join(traceback.format_exception(t, v, tb))
    if sys.stderr: sys.stderr.write(text)
    try:
        from core.paths import app_dir
        with open(os.path.join(app_dir(), "error.log"), "a", encoding="utf-8") as f: f.write(time.strftime("[%Y-%m-%d %H:%M:%S]\n") + text + "\n")
    except OSError: pass
    try: QMessageBox.critical(None, "Error inesperado", str(v))
    except Exception: pass


def selftest():
    """Comprueba que el ejecutable lleva todo lo necesario (bibliotecas, recursos, base de datos, red y Kaggle). Devuelve el código de salida."""
    import urllib.request, urllib.error
    from core import gongora, updater
    from core.paths import app_dir, resource
    lines = []
    def check(name, fn):
        try: lines.append(f"OK     {name}: {fn()}")
        except Exception as e: lines.append(f"FALLO  {name}: {type(e).__name__}: {e}")
    def database():
        db.init_db(); return f"{db.count():,} perfumes en {db.DB_PATH}"
    def assets():
        miss = [f for f in ("icon.ico", "icon.png", "logo.png", "gongora.png", "arrow_down.svg") if not os.path.exists(resource("assets", f))]
        if miss: raise FileNotFoundError(", ".join(miss))
        return "icono, logotipo, avatar y flecha"
    def qt_ssl():
        from PyQt6.QtNetwork import QSslSocket
        if not QSslSocket.supportsSsl(): raise RuntimeError("Qt sin soporte TLS (no se podrán descargar imágenes)")
        return QSslSocket.activeBackend()
    def image_formats():
        from PyQt6.QtGui import QImageReader
        have = {bytes(f).decode() for f in QImageReader.supportedImageFormats()}
        need = {"jpg", "png", "svg"}
        if not need <= have: raise RuntimeError("faltan formatos de imagen: " + ", ".join(sorted(need - have)))
        return "jpg, png y svg"
    def gemini_tls():
        try: urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models"), timeout=15)
        except urllib.error.HTTPError as e: return f"TLS correcto (HTTP {e.code} sin clave, es lo esperado)"
        return "TLS correcto"
    def kaggle_pkg():
        from kaggle.api.kaggle_api_extended import KaggleApi
        return f"{KaggleApi.__name__} presente" + (" · credenciales encontradas" if updater.has_credentials() else " · sin credenciales (la actualización es opcional)")
    check("datos del usuario", app_dir); check("recursos", assets); check("base de datos", database); check("TLS de Qt", qt_ssl); check("formatos de imagen", image_formats)
    check("TLS de Python (Gemini)", gemini_tls); check("Kaggle", kaggle_pkg)
    check("clave de Góngora", lambda: "configurada" if gongora.stored_key() else "no configurada (opcional)")
    text = "\n".join(lines) + "\n"
    try:
        with open(os.path.join(app_dir(), "selftest.log"), "w", encoding="utf-8") as f: f.write(text)
    except OSError: pass
    if sys.stdout: print(text)
    return 0 if not any(l.startswith("FALLO") for l in lines) else 1


def main():
    sys.excepthook = _hook
    try:
        import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("perfumappte.app")   # icono propio en la barra de tareas
    except Exception: pass
    app = QApplication(sys.argv); app.setStyleSheet(theme.QSS); app.setWindowIcon(logo.app_icon())
    if "--selftest" in sys.argv: sys.exit(selftest())
    install_tips(app); app.aboutToQuit.connect(images.get_cache().abort_all)
    splash = QLabel(tr("app.preparing")); splash.setWindowFlag(Qt.WindowType.FramelessWindowHint); splash.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash.setStyleSheet(f"font-family:Georgia,serif;font-size:16px;border:1px solid {theme.BORDER};"); splash.resize(380, 90); splash.show(); app.processEvents()
    db.init_db(lambda n: (splash.setText(tr("app.preparing.n", n)), app.processEvents()))
    i18n.set_lang(db.get_meta("lang") or i18n.DEFAULT)
    theme.apply(db.get_meta("theme") or theme.DEFAULT); app.setStyleSheet(theme.QSS); apply_tooltip_palette()      # tema elegido (claro por defecto)
    w = Main(); w.show(); splash.close()
    threading.Thread(target=db.warm, daemon=True).start()          # deja listo el conjunto popular para «parecido a» y el chat
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
