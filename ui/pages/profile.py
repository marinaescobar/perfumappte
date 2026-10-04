"""Perfil del perfume: ventana emergente con sus datos, medidores, notas, acordes y perfumes parecidos."""
import html
import math
import os
from PyQt6.QtCore import QEvent, QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from core import db, i18n, recommender as rec
from core.i18n import tr
from core.note_emoji import note_emoji
from ui import icons, images
from ui.accord_colors import ACCORD_COLORS
from ui.cards import SimCard
from ui.theme import ACCENT, BORDER, ICON_OFF, MUTED, PANEL, TXT
from ui.widgets import IconButton, IconMeter, tip_html


NOTE_BAR = ACCENT

def fit_level(frac):
    return tr("reco.l3" if frac >= .75 else "reco.l2" if frac >= .4 else "reco.l1" if frac > 0 else "reco.l0")

def section_label():
    l = QLabel(); l.setStyleSheet(f"font-size:14px;font-weight:600;color:{ACCENT};background:transparent;margin-top:10px;"); return l

class SliderBar(QWidget):
    released = pyqtSignal(int)
    def __init__(s, left, right, editable=False):
        super().__init__(); s.l, s.r, s.v, s.edit = left, right, 50, editable; s.setMinimumHeight(52)
    def set_value(s, v): s.v = int(v or 50); s.update()
    def _set(s, x): s.v = int(max(0, min(100, (x - 10) / max(1, s.width() - 20) * 100))); s.update()
    def mousePressEvent(s, e):
        if s.edit: s._set(e.position().x())
    def mouseMoveEvent(s, e):
        if s.edit: s._set(e.position().x())
    def mouseReleaseEvent(s, e):
        if s.edit: s.released.emit(s.v)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        x1, y = s.width() - 10, s.height() - 16
        p.setPen(QColor(MUTED)); p.drawText(10, 14, s.l); p.drawText(x1 - p.fontMetrics().horizontalAdvance(s.r), 14, s.r)
        pen = QPen(QColor(BORDER), 4); pen.setCapStyle(Qt.PenCapStyle.RoundCap); p.setPen(pen); p.drawLine(10, y, x1, y)
        cx = int(10 + (x1 - 10) * s.v / 100); p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(ACCENT)); p.drawEllipse(cx - 8, y - 8, 16, 16)

class Bar(QWidget):
    """Barra horizontal redondeada que ocupa `frac` (0..1) del ancho disponible."""
    def __init__(s, frac, color, h=12):
        super().__init__(); s.frac, s.color = max(0.0, min(1.0, float(frac))), QColor(color)
        s.setFixedHeight(h); s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = s.rect().adjusted(0, 0, -1, -1); rad = r.height() / 2
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(BORDER)); p.drawRoundedRect(r, rad, rad)
        if s.frac > 0:
            w = max(r.height(), int(r.width() * s.frac))
            p.setPen(QPen(s.color.darker(125), 1)); p.setBrush(s.color)       # borde para que los tonos claros se vean
            p.drawRoundedRect(QRect(r.x(), r.y(), w, r.height()), rad, rad)

class BarList(QWidget):
    """Filas «emoji · nombre · barra» en el orden recibido. Cada fila: (emoji o None, etiqueta, fracción 0..1, color, tooltip)."""
    LABEL_W = 138
    def __init__(s):
        super().__init__(); s.v = QVBoxLayout(s); s.v.setContentsMargins(0, 0, 0, 0); s.v.setSpacing(7)
    def set_rows(s, rows):
        while s.v.count():
            it = s.v.takeAt(0); w = it.widget()
            if w is not None: w.setParent(None); w.deleteLater()
        fm = s.fontMetrics()
        for emoji, label, frac, color, tip in rows:
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
            if emoji:
                e = QLabel(emoji); e.setFixedWidth(26); e.setAlignment(Qt.AlignmentFlag.AlignCenter)
                e.setStyleSheet("font-size:16px;background:transparent;"); h.addWidget(e)
            n = QLabel(fm.elidedText(label, Qt.TextElideMode.ElideRight, s.LABEL_W)); n.setFixedWidth(s.LABEL_W)
            n.setStyleSheet("background:transparent;"); h.addWidget(n); h.addWidget(Bar(frac, color), 1)
            if tip: w.setToolTip(tip)
            s.v.addWidget(w)

class Stars(QWidget):
    """Puntuación 0..5 como cinco estrellas (la última, rellena sólo en parte) con la nota al lado."""
    N, SIZE, GAP = 5, 22, 4
    def __init__(s):
        super().__init__(); s.v = 0.0; s.setFixedHeight(s.SIZE + 8)
    def set_value(s, v): s.v = max(0.0, min(float(s.N), float(v or 0))); s.update()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont(s.font()); f.setPixelSize(14); f.setBold(True); p.setFont(f)
        txt = f"{s.v:.2f}"; tw = p.fontMetrics().horizontalAdvance(txt)
        sw = s.N * s.SIZE + (s.N - 1) * s.GAP
        x0 = (s.width() - sw - 8 - tw) / 2; cy = s.height() / 2; R = s.SIZE / 2
        path = QPainterPath()
        for i in range(s.N):
            cx = x0 + i * (s.SIZE + s.GAP) + R
            path.addPolygon(QPolygonF([QPointF(cx + (R if k % 2 == 0 else R * 0.42) * math.cos(math.radians(36 * k - 90)),
                                               cy + (R if k % 2 == 0 else R * 0.42) * math.sin(math.radians(36 * k - 90))) for k in range(10)]))
            path.closeSubpath()
        p.fillPath(path, QColor(BORDER).darker(110))
        full = int(s.v)
        p.save(); p.setClipRect(QRectF(x0, 0, full * (s.SIZE + s.GAP) + (s.v - full) * s.SIZE, s.height()))
        p.fillPath(path, QColor(ACCENT)); p.restore()
        p.setPen(QColor(TXT)); p.drawText(QRectF(x0 + sw + 8, 0, tw + 2, s.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, txt)

class ProfilePage(QWidget):
    """Contenido del perfil de un perfume. Vive dentro de ProfilePopup (ventana emergente)."""
    changed = pyqtSignal()
    navigate = pyqtSignal(int)          # doble clic en un perfume parecido: abrir su perfil

    def __init__(s):
        super().__init__()
        s.pid = None

        h = QHBoxLayout(s); h.setContentsMargins(28, 6, 28, 26); h.setSpacing(30)
        L = QVBoxLayout(); R = QVBoxLayout(); L.setSpacing(8); R.setSpacing(10)
        h.addLayout(L, 1); h.addLayout(R, 2)

        s.title = QLabel()
        s.title.setObjectName("h1")
        s.title.setWordWrap(True)
        s.title.setStyleSheet("font-size:27px;"); s.title.setFixedWidth(256)

        s.brandline = QLabel(); s.brandline.setWordWrap(True); s.brandline.setFixedWidth(256)
        s.brandline.setStyleSheet(f"color:{ACCENT};font-size:17px;font-weight:600;")

        s.img = QLabel()
        s.img.setFixedSize(220, 280)
        s.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.img.setStyleSheet(
            f"background:{PANEL};"
            f"border:1px solid {BORDER};"
            f"border-radius:18px;"
            f"font-size:72px;"
        )

        images.get_cache().loaded.connect(s._img_loaded)

        # columna de iconos a la izquierda de la foto: género, propiedad y deseos
        s.gender_b = IconMeter("unisex", 1.0, "", 30)
        s.own_b = IconButton("own"); s.own_b.clicked.connect(lambda: s.mark("owned"))
        s.wish_b = IconButton("wish"); s.wish_b.clicked.connect(lambda: s.mark("wishlist"))
        s.clock = IconMeter("clock", 0, "", 30); s.spray = IconMeter("spray", 0, "", 30)

        photo = QHBoxLayout(); photo.setContentsMargins(0, 0, 0, 0); photo.setSpacing(10)
        rail = QVBoxLayout(); rail.setContentsMargins(0, 0, 0, 0); rail.setSpacing(8)
        rail.setAlignment(Qt.AlignmentFlag.AlignTop)
        for b in (s.gender_b, s.own_b, s.wish_b): rail.addWidget(b)
        sep = QFrame(); sep.setFixedSize(22, 1); sep.setStyleSheet(f"background:{ICON_OFF};")
        rail.addSpacing(4); rail.addWidget(sep, 0, Qt.AlignmentFlag.AlignHCenter); rail.addSpacing(4)
        for b in (s.clock, s.spray): rail.addWidget(b)       # duración y estela, bajo los botones de propiedad y deseos
        rail.addStretch(1)
        photo.addLayout(rail)
        # bajo la foto: estrellas, nombre, marca y año, y «Recomendado para:» alineado a la izquierda
        s.stars = Stars(); s.stars.setFixedWidth(220)
        pic = QVBoxLayout(); pic.setContentsMargins(0, 0, 0, 0); pic.setSpacing(4)
        pic.addWidget(s.img); pic.addWidget(s.stars)
        pic.addSpacing(4)
        pic.addWidget(s.title, 0, Qt.AlignmentFlag.AlignLeft); pic.addWidget(s.brandline, 0, Qt.AlignmentFlag.AlignLeft)
        s.lab_reco = QLabel(); s.lab_reco.setAlignment(Qt.AlignmentFlag.AlignLeft)
        s.lab_reco.setStyleSheet(f"font-weight:bold;color:{MUTED};font-size:11px;letter-spacing:1.5px;background:transparent;margin-top:12px;")
        pic.addWidget(s.lab_reco)
        s.reco = QVBoxLayout(); s.reco.setContentsMargins(0, 0, 0, 0); s.reco.setSpacing(3)
        pic.addLayout(s.reco)
        s.lab_sim = QLabel(); s.lab_sim.setAlignment(Qt.AlignmentFlag.AlignLeft)
        s.lab_sim.setStyleSheet(s.lab_reco.styleSheet())
        pic.addWidget(s.lab_sim)
        s.sim = QGridLayout(); s.sim.setContentsMargins(0, 0, 0, 0); s.sim.setHorizontalSpacing(8); s.sim.setVerticalSpacing(4)
        pic.addLayout(s.sim)
        s.sim_cards = []; images.get_cache().loaded.connect(s._sim_loaded)
        pic.addStretch(1)
        photo.addLayout(pic, 1)
        L.addLayout(photo)
        L.addStretch(1)

        s.notes_widget = QWidget()
        s.notes_layout = QVBoxLayout(s.notes_widget)
        s.notes_layout.setContentsMargins(0, 0, 0, 0)
        s.notes_layout.setSpacing(5)

        s.keys = ["sweet_fresh", "floral_woody", "light_intense"]
        s.sb = [SliderBar("Dulce", "Fresco", True), SliderBar("Floral", "Amaderado", True), SliderBar("Ligero", "Intenso", True)]
        for k, b in zip(s.keys, s.sb):
            b.released.connect(lambda v, k=k: s.save(k, v))

        # barras de intensidad, de más a menos
        s.lab_notes, s.lab_acc = section_label(), section_label()
        s.notes_bars, s.acc_bars = BarList(), BarList()
        s.nodata = QLabel(); s.nodata.setWordWrap(True); s.nodata.setStyleSheet(f"color:{MUTED};background:transparent;margin-top:10px;")
        # pirámide de notas a la izquierda de los deslizadores y de las barras, a proporción 1:3
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(18)
        bars = QVBoxLayout(); bars.setContentsMargins(0, 0, 0, 0); bars.setSpacing(10)
        for w in (*s.sb, s.lab_notes, s.notes_bars, s.lab_acc, s.acc_bars, s.nodata): bars.addWidget(w)
        bars.addStretch(1)
        body.addWidget(s.notes_widget, 1); body.addLayout(bars, 3)
        R.addLayout(body)
        R.addStretch(1)

        s.retranslate()

    def _clear_layout(s, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None: w.setParent(None); w.deleteLater()
            else: s._clear_layout(item.layout())

    def retranslate(s):
        for b, (l, r) in zip(s.sb, i18n.PROFILE_AXES): b.l, b.r = i18n.tr_axis(l), i18n.tr_axis(r); b.update()
        s.lab_notes.setText(tr("m.notes")); s.lab_acc.setText(tr("m.accords")); s.nodata.setText(tr("profile.nodata"))
        s.lab_reco.setText(tr("reco.h").upper()); s.lab_reco.setToolTip(tr("tip.reco"))
        s.lab_sim.setText(tr("sim.h").upper()); s.lab_sim.setToolTip(tr("tip.sim.h"))
        s.lab_notes.setToolTip(tr("tip.bars.notes")); s.lab_acc.setToolTip(tr("tip.bars.accords"))
        for k, b in zip(s.keys, s.sb): b.setToolTip(tr("tip.axis." + k))

    @staticmethod
    def _label(name):
        return (i18n.tr_note(name) if i18n.is_es() else name).title()

    def save(s, k, v):
        if s.pid:
            db.update_profile(s.pid, k, v)
            s.changed.emit()

    def show_img(s, p):
        s.key, url = images.src(p)
        pm = None

        if s.key:
            images.get_cache().get(s.key, url)
            path = images.get_cache().path(s.key)
            if os.path.exists(path):
                pm = QPixmap(path)

        if pm and not pm.isNull():
            s.img.setPixmap(
                pm.scaled(
                    QSize(196, 256),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            s.img.clear()
            s.img.setText("🧴")

    def _img_loaded(s, key):
        if s.pid and getattr(s, "key", None) == key:
            p = db.get(s.pid)
            if p:
                s.show_img(p)

    def mark(s, status):
        """Icono de propiedad (owned) o de deseos (wishlist). Si ya está en ese estado, lo quita."""
        if not s.pid: return
        p = db.get(s.pid)
        if not p: return

        if p.get("status") == status: db.remove_from_collection(s.pid)
        else: db.set_collection(s.pid, status)

        s.changed.emit()
        s.refresh()

    _LON = {"Corta": .2, "Moderada": .5, "Larga": .75, "Eterna": 1.0}
    _SIL = {"Suave": .25, "Moderada": .5, "Fuerte": .75, "Enorme": 1.0}

    @staticmethod
    def _level(avg, lo, hi, raw, table, table_en):
        """Relleno 0..1 de duración/estela: de la media numérica si existe; si no, de la etiqueta (Corta, Suave…)."""
        if avg and float(avg) > 0: return max(0.08, min(1.0, (float(avg) - lo) / (hi - lo)))
        k = next(iter(i18n.canon_tokens(raw, table_en)), None) if raw else None
        return table.get(k)

    def show_meters(s, p):
        """Reloj (duración) y spray (estela) en la columna de iconos; sin texto, la explicación va en el tooltip."""
        lon = s._level(p.get("longevity_avg"), 1, 5, p.get("longevity"), s._LON, i18n.LON_EN)
        sil = s._level(p.get("sillage_avg"), 1, 4, p.get("sillage"), s._SIL, i18n.SIL_EN)
        for w, kind, frac, key, lab in (
                (s.clock, "clock", lon, "lon", i18n.tr_longevity(p.get("longevity")) or i18n.longevity_label(p.get("longevity_avg"))),
                (s.spray, "spray", sil, "sil", i18n.tr_sillage(p.get("sillage")) or i18n.sillage_label(p.get("sillage_avg")))):
            w.setVisible(frac is not None)
            if frac is not None: w.set(kind, frac, tip_html(tr("tip." + key, lab), tr("tip." + key + ".d")))

    def show_reco(s, p):
        """«Recomendado para:» estaciones | momento del día / ocasiones; más relleno = más indicado."""
        s._clear_layout(s.reco)
        toks = lambda v, table: set(i18n.canon_tokens([x.strip() for x in str(v).split(",") if x.strip()], table))
        def votes(pairs):                      # [(clave, columna)] -> fracciones relativas al más votado
            v = [float(p.get(c) or 0) for _k, c in pairs]; m = max(v)
            return [x / m for x in v] if m > 0 else None
        def group(pairs, fr, name):
            return [(k, f, tip_html(name(k), fit_level(f))) for (k, _c), f in zip(pairs, fr)] if fr else []
        seasons = [("primavera", "spring"), ("verano", "summer"), ("otoño", "autumn"), ("invierno", "winter")]
        fr = votes(seasons)
        if fr is None and p.get("season"):
            have = toks(p.get("season"), i18n.SEA_EN); fr = [1.0 if k in have else 0.0 for k, _c in seasons]
        parts = [("día", "day"), ("noche", "night")]
        occ = []
        if p.get("occasion"):
            have = toks(p.get("occasion"), i18n.OCC_EN)
            occ = [(icons.OCCASION_ICON.get(k, k), 1.0 if k in have else 0.0, tip_html(i18n.tr_occasions(k), fit_level(1.0 if k in have else 0.0)))
                   for k in i18n.OCCASIONS]
        rows = [[group(seasons, fr, i18n.tr_seasons), group(parts, votes(parts), lambda k: i18n.tr_field(k, i18n.DAY_EN))], [occ]]
        for groups in rows:
            groups = [g for g in groups if g]
            if not groups: continue
            h = QHBoxLayout(); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(3)
            for gi, g in enumerate(groups):
                if gi:
                    d = QFrame(); d.setFixedSize(1, 28); d.setStyleSheet(f"background:{ICON_OFF};"); h.addSpacing(4); h.addWidget(d); h.addSpacing(4)
                for kind, frac, tp in g: h.addWidget(IconMeter(kind, frac, tp, 34))
            h.addStretch(1); s.reco.addLayout(h)
        s.lab_reco.setVisible(any(s.reco.itemAt(i) for i in range(s.reco.count())))

    def _sim_loaded(s, key):
        for c in s.sim_cards:
            if c.key == key: c.set_pix()

    def show_sim(s, p):
        """«Parecido a:» seis perfumes de la base de datos, en dos filas de tres."""
        s._clear_layout(s.sim); s.sim_cards = []
        q = {**p, **{k: (p.get(k) if p.get(k) is not None else 50) for k in ("sweet_fresh", "floral_woody", "light_intense")}}
        try: found = rec.similar_to(q, [r for r in db.all_rows() if None not in (r["sweet_fresh"], r["floral_woody"], r["light_intense"])], 6)
        except Exception: found = []
        for i, (score, r) in enumerate(found):
            card = SimCard(r, score); card.opened.connect(s.navigate.emit)
            s.sim.addWidget(card, i // 3, i % 3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft); s.sim_cards.append(card)
        s.lab_sim.setVisible(bool(found))

    def show_id(s, pid):
        s.pid = pid
        s.refresh()

    def refresh(s):
        p = db.get(s.pid) if s.pid else None
        if not p: return

        e = html.escape

        name = p.get("name") or tr("none.f")
        brand = p.get("brand") or ""
        year = p.get("year") or "—"
        gender = i18n.tr_gender(p.get("gender")) if p.get("gender") else "—"

        s.title.setText(name)

        s.show_img(p)

        # iconos de la columna: género (sólo informativo), propiedad y deseos
        gkind = {"male": "mars", "female": "venus", "unisex": "unisex"}.get(i18n.norm(p.get("gender") or ""))
        s.gender_b.setVisible(bool(gkind))
        if gkind: s.gender_b.set(gkind, 1.0, tip_html(tr("m.gender") + ": " + gender))

        st = p.get("status")
        s.own_b.set_active(st == "owned"); s.wish_b.set_active(st == "wishlist")
        s.own_b.setToolTip(tip_html(tr("btn.remove")) if st == "owned" else tip_html(tr("btn.toowned")))
        s.wish_b.setToolTip(tip_html(tr("btn.remove")) if st == "wishlist" else tip_html(tr("btn.towishlist")))

        perfumer_names = p.get("perfumers") or ""

        rating_avg = p.get("rating_avg")
        has_rating = rating_avg is not None and float(rating_avg) > 0
        s.stars.set_value(rating_avg if has_rating else 0)
        votes = p.get("vote_count") or p.get("people") or 0
        s.stars.setToolTip(tr("tip.rating", float(rating_avg), " " + tr("m.votes", int(votes)) if votes else "") if has_rating else "")
        s.stars.setVisible(has_rating)

        s.show_meters(p)
        s.show_reco(p)
        s.show_sim(p)

        s.brandline.setText(f"{brand} · {year}" if brand else str(year))
        s.brandline.setToolTip(tip_html(tr("m.perfumer"), e(str(perfumer_names))) if perfumer_names else "")

        for k, b in zip(s.keys, s.sb):
            value = p.get(k, 0)
            if value is None: value = 0
            b.set_value(value)

        # ------------------- NOTAS: fichas por pirámide, de más a menos intensidad -------------------
        s._clear_layout(s.notes_layout)
        wmap = rec.parse_weights(p.get("note_weights"))          # {nota en minúsculas: peso 0..1}

        def tier(col):
            items = [(n.strip(), wmap.get(n.strip().lower())) for n in str(p.get(col) or "").split(",") if n.strip()]
            return sorted(items, key=lambda x: (-x[1]) if x[1] is not None else 1.0)      # sin peso, al final

        top_n, mid_n, base_n, flat_n = tier("top_notes"), tier("heart_notes"), tier("base_notes"), tier("flat_notes")

        def build_note_section(title, n_list, tip=""):
            if not n_list: return
            lbl = QLabel(title.upper()); lbl.setToolTip(tip)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-weight: bold; margin-top: 14px; color: {MUTED}; font-size: 11px; letter-spacing: 1.5px;")
            s.notes_layout.addWidget(lbl)

            grid = QGridLayout()
            grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            grid.setSpacing(6)
            row, col = 0, 0

            for name, w_ in n_list[:12]:
                w = QWidget()
                v = QVBoxLayout(w)
                v.setContentsMargins(0, 0, 0, 0)
                v.setSpacing(4)

                elbl = QLabel(note_emoji(name))
                elbl.setStyleSheet(f"font-size: 26px; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px; padding: 4px;")
                elbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

                nlbl = QLabel(s._label(name))
                nlbl.setStyleSheet(f"font-size: 10px; color: {TXT};")
                nlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                nlbl.setWordWrap(True)
                nlbl.setMaximumWidth(70)
                w.setToolTip(s._label(name) + (f" · {tr('profile.intensity', round(w_ * 100))}" if w_ is not None else ""))

                v.addWidget(elbl, 0, Qt.AlignmentFlag.AlignHCenter)
                v.addWidget(nlbl, 0, Qt.AlignmentFlag.AlignHCenter)

                grid.addWidget(w, row, col)
                col += 1
                if col > 1:                                  # columna estrecha (1:3 frente a las barras): dos fichas por fila
                    col = 0
                    row += 1

            s.notes_layout.addLayout(grid)

        build_note_section(tr("m.top"), top_n, tr("tip.top"))
        build_note_section(tr("m.heart"), mid_n, tr("tip.heart"))
        build_note_section(tr("m.base"), base_n, tr("tip.base"))
        build_note_section(tr("m.notes"), flat_n)           # perfumes sin pirámide
        s.notes_layout.addStretch(1)
        s.notes_widget.setVisible(bool(top_n or mid_n or base_n or flat_n))

        # ------------------- BARRAS «NOTAS»: todas las notas juntas, de más a menos intensidad -------------------
        best = {}                                            # una nota repetida en dos niveles cuenta con su mayor peso
        for n, w_ in top_n + mid_n + base_n + flat_n:
            if w_ is not None and (n.lower() not in best or w_ > best[n.lower()][1]): best[n.lower()] = (n, w_)
        ranked = sorted(best.values(), key=lambda x: -x[1])[:12]
        mx = (ranked[0][1] or 1.0) if ranked else 1.0        # la más intensa ocupa toda la barra
        s.notes_bars.set_rows([(note_emoji(n), s._label(n), w_ / mx, NOTE_BAR, tr("profile.intensity", round(w_ * 100))) for n, w_ in ranked])

        # ------------------- BARRAS «ACORDES»: de más a menos (p. ej. más Floral que Fresco) -------------------
        aw = rec.parse_weights(p.get("accord_weights"))
        if aw:
            items = sorted(aw.items(), key=lambda x: -x[1])[:10]
            tip = lambda w_: f"{round(w_ * 100)}%"
        else:
            # base importada antes de guardar la fuerza de los acordes: Fragrantica los lista de mayor a menor,
            # así que se respeta el orden y la longitud es aproximada hasta volver a importar
            names = [a.strip() for a in str(p.get("accords") or "").split(",") if a.strip()][:10]
            items = [(n, max(0.3, 1.0 - 0.07 * i)) for i, n in enumerate(names)]
            tip = lambda w_: ""
        mx = (items[0][1] or 1.0) if items else 1.0
        s.acc_bars.set_rows([(None, i18n.tr_accord(n).title(), w_ / mx, ACCORD_COLORS.get(i18n.accord_key(n), ACCENT), tip(w_)) for n, w_ in items])

        s.lab_notes.setVisible(bool(ranked)); s.notes_bars.setVisible(bool(ranked))
        s.lab_acc.setVisible(bool(items)); s.acc_bars.setVisible(bool(items))
        s.nodata.setVisible(not ranked and not items)

class ProfilePopup(QWidget):
    """Ventana emergente del perfil: una capa dentro de la propia ventana sobre un fondo atenuado.
    Se cierra con la ✕, con Esc o haciendo clic fuera de la tarjeta."""
    closed = pyqtSignal()        # solo si dentro cambió algo (colección, sliders), para refrescar la lista de detrás

    def __init__(s, parent):
        super().__init__(parent)
        s.setObjectName("overlay"); s.setFocusPolicy(Qt.FocusPolicy.StrongFocus); s.dirty = False
        s.card = QFrame(s); s.card.setObjectName("pcard")
        cv = QVBoxLayout(s.card); cv.setContentsMargins(6, 0, 6, 12); cv.setSpacing(0)
        top = QHBoxLayout(); top.setContentsMargins(0, 12, 12, 0); top.addStretch(1)
        s.x = QPushButton("✕"); s.x.setObjectName("pclose"); s.x.setFixedSize(34, 34); s.x.setCursor(Qt.CursorShape.PointingHandCursor)
        s.x.clicked.connect(lambda _=False: s.close_popup()); top.addWidget(s.x); cv.addLayout(top)
        s.page = ProfilePage(); s.page.changed.connect(s._mark_dirty); s.page.navigate.connect(s.go)
        s.scroll = QScrollArea(); s.scroll.setWidgetResizable(True); s.scroll.setFrameShape(QFrame.Shape.NoFrame)
        s.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); s.scroll.setWidget(s.page); cv.addWidget(s.scroll, 1)
        parent.installEventFilter(s)         # para recolocarse cuando cambia el tamaño de la ventana
        s.hide(); s.retranslate()

    def _mark_dirty(s): s.dirty = True

    def retranslate(s):
        s.x.setToolTip(tr("profile.close")); s.page.retranslate()
        if s.isVisible(): s.page.refresh()

    def place(s):
        p = s.parentWidget()
        if p is None: return
        s.setGeometry(0, 0, p.width(), p.height())
        w = max(640, min(1080, p.width() - 90)); h = max(440, min(880, p.height() - 40))
        s.card.setGeometry((p.width() - w) // 2, (p.height() - h) // 2, w, h)

    def open(s, pid):
        s.dirty = False; s.page.show_id(pid); s.scroll.verticalScrollBar().setValue(0)
        s.place(); s.show(); s.raise_(); s.setFocus()

    def go(s, pid):
        """Salta al perfil de otro perfume sin cerrar la ventana (conserva si algo cambió dentro)."""
        s.page.show_id(pid); s.scroll.verticalScrollBar().setValue(0)

    def close_popup(s):
        if not s.isVisible(): return
        s.hide()
        if s.dirty: s.dirty = False; s.closed.emit()

    def eventFilter(s, o, e):
        if o is s.parentWidget() and e.type() == QEvent.Type.Resize and s.isVisible(): s.place()
        return False

    def paintEvent(s, e):
        QPainter(s).fillRect(s.rect(), QColor(53, 36, 71, 150))      # #352447 atenuado

    def mousePressEvent(s, e):
        if not s.card.geometry().contains(e.position().toPoint()): s.close_popup()
        e.accept()

    def keyPressEvent(s, e):
        if e.key() == Qt.Key.Key_Escape: s.close_popup()
        else: super().keyPressEvent(e)
