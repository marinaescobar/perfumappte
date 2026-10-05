"""Colores, temas (claro / oscuro) y hoja de estilos (QSS) de toda la aplicación.

Los colores viven en dos paletas (LIGHT y DARK). `apply(mode)` copia la elegida a las variables de este módulo y de los demás módulos
de `ui` que pintan a mano (los que hacen `from ui.theme import ACCENT…` tienen su propia copia, que se actualiza igual), y
`restyle(app)` repinta lo que ya está en pantalla: hoja de estilos global, hojas de estilo propias de cada widget y repintado.
"""
import re, sys
from core.paths import resource

LIGHT = dict(
    BG="#F1EFF5", PANEL="#FFFFFF", TXT="#352447", ACCENT="#9a6fc4", MUTED="#8B8499", BORDER="#E7E2EE", SOFT="#F1EAF8",
    ICON_OFF="#D6CDE2", ICON_OFF_HOVER="#BBA6D6", ACCENT_HOVER="#7f55a6", TRACK="#F1EAF8", HOVER="#FBF8FE", BAR_HOVER="#E8DFF3",
    GOLD="#9a6fc4", GOLD_HOVER="#7f55a6", GOLD_DIS="#cdbfe0", SEARCH="#E9E5F0", GRID="#EFEAF4", POP="#E3D3F3", BOT="#F4EEFA",
    SCROLL="#D6CDE2", GDIS_TXT="#cfc8da", TT_BG="#FBF8FE", TIP_BORDER="#E3D3F3", TIP_TITLE="#6b4a8f", TIP_BODY="#4a3b5c",
    TIP_TOP="#FFFFFF", TIP_BOT="#F7F0FC", INK="#352447", BOTTLE="#E4D8F1", BOTTLE_CAP="#CDBBE3", SHADOW=(110, 70, 160), ERR="#b04a4a",
    PALETTE=["#9a6fc4", "#c9b3e0", "#6b4a8f", "#b99ad6", "#352447", "#ddd0ec", "#8B8499", "#5a3d78", "#a98bd0", "#e8dff3"],
    PALE=("#ddd0ec", "#e8dff3", "#c9b3e0"))
DARK = dict(
    BG="#16121d", PANEL="#211b2c", TXT="#ece5f4", ACCENT="#b78fe3", MUTED="#a095b2", BORDER="#372e4a", SOFT="#32283f",
    ICON_OFF="#4c4163", ICON_OFF_HOVER="#6d5e8a", ACCENT_HOVER="#cfaef2", TRACK="#2f2640", HOVER="#2b2339", BAR_HOVER="#3c3150",
    GOLD="#8a5cb8", GOLD_HOVER="#9d70cb", GOLD_DIS="#43385a", SEARCH="#2a2336", GRID="#2d2539", POP="#4a3b66", BOT="#2e2540",
    SCROLL="#4c4163", GDIS_TXT="#5d5173", TT_BG="#2b2339", TIP_BORDER="#4a3b66", TIP_TITLE="#d3b9f0", TIP_BODY="#ddd4e8",
    TIP_TOP="#2f2640", TIP_BOT="#251e32", INK="#ece5f4", BOTTLE="#3a3050", BOTTLE_CAP="#4b3f66", SHADOW=(0, 0, 0), ERR="#e07a7a",
    PALETTE=["#b78fe3", "#6b4a8f", "#d3b9f0", "#8a5cb8", "#ece5f4", "#4c4163", "#a095b2", "#a98bd0", "#5a3d78", "#3c3150"],
    PALE=("#ece5f4", "#d3b9f0"))
MODES = ("light", "dark")
DEFAULT = "light"
MODE = DEFAULT
ARROW = resource("assets", "arrow_down.svg").replace("\\", "/")

# familia olfativa -> icono (Descubrimientos)
FAMILY_ICONS = {"Cítrica": "🍊", "Floral": "🌸", "Amaderada": "🌲", "Oriental": "✨", "Aromática": "🌿", "Gourmand": "🧁",
                "Fougère": "🍃", "Acuática": "💧", "Chipre": "🍂", "Cuero": "🧥", "Especiada": "🌶", "Frutal": "🍎"}

# colores que las hojas de estilo propias de cada widget llevan escritos a mano (se cambian de una paleta a otra en `restyle`)
_INLINE = ("TXT", "ACCENT", "MUTED", "PANEL", "BORDER", "ICON_OFF", "SOFT", "BG", "ERR")
_SKIP = {"ui.theme", "ui.avatar", "ui.logo", "ui.icons", "ui.accord_colors"}      # avatar y logo tienen sus propios colores de ilustración

QSS = ""

def palette(): return DARK if MODE == "dark" else LIGHT

def build_qss():
    return f"""

* {{ font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-size: 13px; color: {TXT}; }}
QMainWindow, QWidget {{ background: {BG}; }}
#side {{ background: {PANEL}; border-right: 1px solid {BORDER}; }}
#topbar {{ background: {BG}; }}
#logo {{ padding: 18px 20px; background: {PANEL}; }}
#logo[compact="true"] {{ padding: 18px 0; }}
QPushButton#nav[compact="true"] {{ padding: 12px 0; text-align: center; }}
QPushButton#verlink {{ border: none; background: transparent; color: {MUTED}; font-size: 11px; text-align: left; padding: 0 20px 14px 20px; }}
QPushButton#verlink:hover {{ color: {ACCENT}; }}
QPushButton#verlink[new="true"] {{ color: {ACCENT}; font-weight: 600; }}
QPushButton#verlink[compact="true"] {{ text-align: center; padding: 0 0 14px 0; }}
QPushButton#sidetoggle {{ border-radius: 17px; padding: 0; color: {MUTED}; font-size: 16px; background: {PANEL}; }}
QPushButton#sidetoggle:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
#chartcard {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 18px; }}
#h1 {{ font-family: 'Segoe UI Semibold', 'Helvetica Neue', sans-serif; font-size: 28px; font-weight: 600; }}
QPushButton {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; padding: 8px 16px; }}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#nav {{ text-align: left; border: none; border-radius: 0; padding: 12px 22px; background: {PANEL}; color: {MUTED}; }}
QPushButton#nav:hover {{ color: {TXT}; }}
QPushButton#nav:checked {{ color: {ACCENT}; border-left: 3px solid {ACCENT}; font-weight: 600; }}
QPushButton#gold {{ background: {GOLD}; color: white; border: none; font-weight: 600; }}
QPushButton#gold:hover {{ background: {GOLD_HOVER}; color: white; }}
QPushButton#gold:disabled {{ background: {GOLD_DIS}; color: white; }}
QPushButton#chip {{ padding: 4px; font-size: 13px; border-radius: 16px; background: {PANEL}; border: 1px solid {BORDER}; }}
QPushButton#chip:hover {{ border-color: {ACCENT}; }}
QPushButton#chip:checked {{ border: 2px solid {ACCENT}; background: {SOFT}; color: {ACCENT}; }}
QLineEdit, QComboBox, QTextEdit, QTextBrowser, QTableWidget, QListWidget, QSpinBox {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit#search {{ background: {SEARCH}; border: 1px solid {SEARCH}; border-radius: 19px; padding: 9px 18px; }}
QLineEdit#search:focus {{ background: {PANEL}; border: 1px solid {ACCENT}; }}
QScrollArea {{ border: none; }}
QTableWidget {{ gridline-color: {GRID}; selection-background-color: {SOFT}; selection-color: {TXT}; }}
QListWidget::item {{ padding: 8px; }} QListWidget::item:selected {{ background: {SOFT}; color: {TXT}; }}
QHeaderView::section {{ background: {BG}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 600; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ padding: 10px 24px; margin-right: 8px; border-radius: 21px; background: transparent; color: {MUTED}; }}
QTabBar::tab:selected {{ background: {GOLD}; color: white; }}
QTabBar::tab:hover:!selected {{ color: {ACCENT}; }}
QComboBox {{ padding: 7px 12px; border-radius: 12px; }}
QComboBox::drop-down {{ border: none; background: transparent; width: 26px; }}
QComboBox::down-arrow {{ image: url({ARROW}); width: 12px; height: 8px; }}
QComboBox QAbstractItemView {{ background: {PANEL}; selection-background-color: {SOFT}; selection-color: {TXT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px; outline: 0; }}
QComboBox QAbstractItemView::item {{ padding: 7px 12px; min-height: 22px; border-radius: 8px; }}
QComboBox QAbstractItemView::item:hover {{ background: {SOFT}; color: {ACCENT}; }}
QPushButton#ms {{ text-align: left; padding: 8px 14px; border-radius: 12px; }}
#mspopw {{ background: transparent; }}
#mspop {{ background: {PANEL}; border: 1px solid {POP}; border-radius: 14px; }}
QPushButton#tgl {{ padding: 8px 18px; border-radius: 16px; font-weight: 600; }}
QPushButton#tgl:checked {{ background: {SOFT}; border: 1px solid {ACCENT}; color: {ACCENT}; font-weight: 600; }}
#pair {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; }}
QPushButton#opt {{ text-align: left; border: none; border-radius: 9px; padding: 8px 12px; background: transparent; }}
QPushButton#opt:hover {{ background: {SOFT}; color: {ACCENT}; }}
QPushButton#opt:checked {{ background: {SOFT}; color: {ACCENT}; font-weight: 600; }}
#chat {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 22px; }}
#chat QLabel {{ background: transparent; }}
QLabel#gbot {{ background: {BOT}; color: {TXT}; border-radius: 16px; border-bottom-left-radius: 5px; padding: 10px 14px; }}
QLabel#guser {{ background: {GOLD}; color: white; border-radius: 16px; border-bottom-right-radius: 5px; padding: 10px 14px; }}
#gcard {{ background: {PANEL}; border: 1px solid {POP}; border-radius: 14px; }}
QPushButton#gclear {{ border-radius: 11px; padding: 3px 12px; font-size: 11px; color: {MUTED}; }}
QPushButton#gclear:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
QPushButton#gclear:disabled {{ color: {GDIS_TXT}; }}
QPushButton#gtool {{ border: none; background: transparent; padding: 0; border-radius: 15px; }}
QPushButton#gtool:hover {{ background: {BOT}; }}
QLabel#gnote {{ color: {MUTED}; font-size: 11px; background: transparent; }}
QWidget#gscroll {{ background: transparent; }}
#chat QScrollArea {{ background: transparent; }}
#overlay {{ background: transparent; }}
#pcard {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 20px; }}
QPushButton#pclose {{ border-radius: 17px; padding: 0; font-size: 14px; color: {MUTED}; }}
QPushButton#pclose:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {SCROLL}; border-radius: 3px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: {SCROLL}; border-radius: 3px; min-width: 36px; }}
QScrollBar::handle:horizontal:hover {{ background: {ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QToolTip {{ background-color: {TT_BG}; color: {TIP_BODY}; border: 1px solid {POP}; padding: 7px 10px; font-size: 12px; }}
"""

def apply(mode):
    """Activa el tema `mode` («light» o «dark»): actualiza las variables de colores y reconstruye `QSS`. Devuelve el modo activo."""
    global MODE, QSS
    MODE = mode if mode in MODES else DEFAULT
    c = palette(); g = globals()
    for k, v in c.items(): g[k] = v
    QSS = build_qss()
    for name, m in list(sys.modules.items()):                          # los módulos que importaron los colores con `from ui.theme import …`
        if name.startswith("ui.") and name not in _SKIP and m is not None:
            for k, v in c.items():
                if k in m.__dict__: setattr(m, k, v)
    return MODE

def _swap_table(old, new):
    return {old[k].lower(): new[k] for k in _INLINE if old[k].lower() != new[k].lower()}

def restyle(app, old):
    """Repinta lo que ya está en pantalla tras `apply`: hoja global, hojas de estilo de cada widget (cambiando los colores de la paleta
    anterior `old` por los de la actual) y repintado de los widgets que dibujan a mano."""
    app.setStyleSheet(QSS)
    table = _swap_table(old, palette()); pat = re.compile("|".join(re.escape(k) for k in table), re.I) if table else None
    for w in app.allWidgets():
        ss = w.styleSheet()
        if pat and ss:
            new = pat.sub(lambda m: table[m.group(0).lower()], ss)
            if new != ss: w.setStyleSheet(new)
        w.update()

apply(DEFAULT)
