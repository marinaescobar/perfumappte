"""Colores y hoja de estilos (QSS) de toda la aplicación."""
from core.paths import resource

BG, PANEL, TXT, ACCENT, MUTED, BORDER = "#F1EFF5", "#FFFFFF", "#352447", "#9a6fc4", "#8B8499", "#E7E2EE"
SOFT = "#F1EAF8"
ICON_OFF = "#D6CDE2"        # icono «vacío» (la parte rellena usa ACCENT)
ARROW = resource("assets", "arrow_down.svg").replace("\\", "/")

# familia olfativa -> icono (Descubrimientos)
FAMILY_ICONS = {"Cítrica": "🍊", "Floral": "🌸", "Amaderada": "🌲", "Oriental": "✨", "Aromática": "🌿", "Gourmand": "🧁",
                "Fougère": "🍃", "Acuática": "💧", "Chipre": "🍂", "Cuero": "🧥", "Especiada": "🌶", "Frutal": "🍎"}

QSS = f"""
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
QPushButton#gold {{ background: {ACCENT}; color: white; border: none; font-weight: 600; }}
QPushButton#gold:hover {{ background: #7f55a6; color: white; }}
QPushButton#gold:disabled {{ background: #cdbfe0; color: white; }}
QPushButton#chip {{ padding: 4px; font-size: 13px; border-radius: 16px; background: {PANEL}; border: 1px solid {BORDER}; }}
QPushButton#chip:hover {{ border-color: {ACCENT}; }}
QPushButton#chip:checked {{ border: 2px solid {ACCENT}; background: {SOFT}; color: {ACCENT}; }}
QLineEdit, QComboBox, QTextEdit, QTextBrowser, QTableWidget, QListWidget, QSpinBox {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit#search {{ background: #E9E5F0; border: 1px solid #E9E5F0; border-radius: 19px; padding: 9px 18px; }}
QLineEdit#search:focus {{ background: {PANEL}; border: 1px solid {ACCENT}; }}
QScrollArea {{ border: none; }}
QTableWidget {{ gridline-color: #EFEAF4; selection-background-color: {SOFT}; selection-color: {TXT}; }}
QListWidget::item {{ padding: 8px; }} QListWidget::item:selected {{ background: {SOFT}; color: {TXT}; }}
QHeaderView::section {{ background: {BG}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 600; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ padding: 10px 24px; margin-right: 8px; border-radius: 21px; background: transparent; color: {MUTED}; }}
QTabBar::tab:selected {{ background: {ACCENT}; color: white; }}
QTabBar::tab:hover:!selected {{ color: {ACCENT}; }}
QComboBox {{ padding: 7px 12px; border-radius: 12px; }}
QComboBox::drop-down {{ border: none; background: transparent; width: 26px; }}
QComboBox::down-arrow {{ image: url({ARROW}); width: 12px; height: 8px; }}
QComboBox QAbstractItemView {{ background: {PANEL}; selection-background-color: {SOFT}; selection-color: {TXT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px; outline: 0; }}
QComboBox QAbstractItemView::item {{ padding: 7px 12px; min-height: 22px; border-radius: 8px; }}
QComboBox QAbstractItemView::item:hover {{ background: {SOFT}; color: {ACCENT}; }}
QPushButton#ms {{ text-align: left; padding: 8px 14px; border-radius: 12px; }}
#mspopw {{ background: transparent; }}
#mspop {{ background: {PANEL}; border: 1px solid #E3D3F3; border-radius: 14px; }}
QPushButton#tgl {{ padding: 8px 18px; border-radius: 16px; font-weight: 600; }}
QPushButton#tgl:checked {{ background: {SOFT}; border: 1px solid {ACCENT}; color: {ACCENT}; font-weight: 600; }}
#pair {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; }}
QPushButton#opt {{ text-align: left; border: none; border-radius: 9px; padding: 8px 12px; background: transparent; }}
QPushButton#opt:hover {{ background: {SOFT}; color: {ACCENT}; }}
QPushButton#opt:checked {{ background: {SOFT}; color: {ACCENT}; font-weight: 600; }}
#chat {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 22px; }}
#chat QLabel {{ background: transparent; }}
QLabel#gbot {{ background: #F4EEFA; color: {TXT}; border-radius: 16px; border-bottom-left-radius: 5px; padding: 10px 14px; }}
QLabel#guser {{ background: {ACCENT}; color: white; border-radius: 16px; border-bottom-right-radius: 5px; padding: 10px 14px; }}
#gcard {{ background: {PANEL}; border: 1px solid #E3D3F3; border-radius: 14px; }}
QPushButton#gclear {{ border-radius: 11px; padding: 3px 12px; font-size: 11px; color: {MUTED}; }}
QPushButton#gclear:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
QPushButton#gclear:disabled {{ color: #cfc8da; }}
QPushButton#gtool {{ border: none; background: transparent; padding: 0; border-radius: 15px; }}
QPushButton#gtool:hover {{ background: #F4EEFA; }}
QLabel#gnote {{ color: {MUTED}; font-size: 11px; background: transparent; }}
QWidget#gscroll {{ background: transparent; }}
#chat QScrollArea {{ background: transparent; }}
#overlay {{ background: transparent; }}
#pcard {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 20px; }}
QPushButton#pclose {{ border-radius: 17px; padding: 0; font-size: 14px; color: {MUTED}; }}
QPushButton#pclose:hover {{ color: {ACCENT}; border-color: {ACCENT}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #D6CDE2; border-radius: 3px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: #D6CDE2; border-radius: 3px; min-width: 36px; }}
QScrollBar::handle:horizontal:hover {{ background: {ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QToolTip {{ background-color: #FBF8FE; color: #4a3b5c; border: 1px solid #E3D3F3; padding: 7px 10px; font-size: 12px; }}
"""
