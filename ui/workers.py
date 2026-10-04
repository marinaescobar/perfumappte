"""Hilos de trabajo: actualización de la base de datos y preguntas a Góngora (para no bloquear la interfaz)."""
from PyQt6.QtCore import QThread, pyqtSignal
from core import selfupdate, gongora, updater
from core.i18n import tr


class UpdateWorker(QThread):
    status = pyqtSignal(str); done = pyqtSignal(int, int); failed = pyqtSignal(str)
    def run(s):
        try:
            n, u = updater.update(progress=lambda k: s.status.emit(tr("up.prog", k)), log=s.status.emit); s.done.emit(n, u)
        except Exception as e: s.failed.emit(str(e))

class GongoraWorker(QThread):
    """Ejecuta una pregunta a Góngora fuera del hilo de la interfaz."""
    chunk = pyqtSignal(str); tool = pyqtSignal(str); suggest = pyqtSignal(dict); done = pyqtSignal(str); failed = pyqtSignal(str, str)
    def __init__(s, g, text): super().__init__(); s.g, s.text = g, text
    def run(s):
        try: s.done.emit(s.g.reply(s.text, s.chunk.emit, s.tool.emit, s.suggest.emit))
        except gongora.NoKey: s.failed.emit("nokey", "")
        except gongora.RateLimited: s.failed.emit("rate", "")
        except gongora.NetError: s.failed.emit("net", "")
        except gongora.ApiError as e: s.failed.emit("api", str(e))
        except Exception as e: s.failed.emit("api", f"{type(e).__name__}: {e}")


class ReleasesWorker(QThread):
    """Consulta las Releases de GitHub sin bloquear la interfaz."""
    done = pyqtSignal(list); failed = pyqtSignal(str)
    def run(s):
        try: s.done.emit(selfupdate.releases())
        except selfupdate.UpdateError as e: s.failed.emit(str(e))
        except Exception as e: s.failed.emit(f"{type(e).__name__}")


class DownloadWorker(QThread):
    """Descarga el instalador de una Release."""
    progress = pyqtSignal(int, int); done = pyqtSignal(str); failed = pyqtSignal(str)
    def __init__(s, rel): super().__init__(); s.rel = rel
    def run(s):
        try: s.done.emit(selfupdate.download(s.rel, s.progress.emit))
        except selfupdate.UpdateError as e: s.failed.emit(str(e))
        except Exception as e: s.failed.emit(f"{type(e).__name__}")
