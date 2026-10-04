"""Rutas de la aplicación.

Datos del usuario (base de datos, imágenes, descargas, clave de Góngora):
  · instalada (.exe) ........ %LOCALAPPDATA%\\Perfumappte  (la carpeta de instalación puede ser de solo lectura)
  · desde el código fuente .. la raíz del proyecto
  · en cualquier caso, la variable de entorno PERFUMAPP_HOME manda (útil para pruebas).
Recursos de solo lectura (assets/): junto al código o, en un .exe de PyInstaller, dentro del paquete.
"""
import os, sys

FROZEN = getattr(sys, "frozen", False)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def app_dir():
    """Carpeta de los datos del usuario (se crea si no existe)."""
    if os.environ.get("PERFUMAPP_HOME"): d = os.environ["PERFUMAPP_HOME"]
    elif FROZEN: d = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Perfumappte")
    else: return PROJECT_ROOT
    os.makedirs(d, exist_ok=True); return d

def resource(*parts):
    """Ruta de un recurso de solo lectura (assets/...), también dentro de un .exe de PyInstaller."""
    return os.path.join(getattr(sys, "_MEIPASS", None) or PROJECT_ROOT, *parts)
