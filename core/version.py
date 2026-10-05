"""Nombre y versión de la aplicación (los usa también el instalador y la comprobación de actualizaciones).

Para publicar una versión nueva:  1) sube VERSION aquí,  2) crea en GitHub una Release con la etiqueta  v<VERSION>  y adjunta el instalador
(Perfumappte-Setup-<VERSION>.exe; lo genera `python -m tools.build_installer` o el flujo de GitHub Actions).
Las personas que ya tienen la app instalada verán el aviso de actualización la próxima vez que la abran.
"""
APP_NAME = "Perfúmappte"
VERSION = "1.1.0"

# Repositorio de GitHub con las Releases, en formato  usuario/repositorio.  Mientras tenga el valor de ejemplo, la app no busca actualizaciones.
GITHUB_REPO = "marinaescobar/perfumappte"
