"""Mi colección > Mis gustos: gráficos sobre los perfumes en propiedad."""
import re
from collections import Counter
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from core import db, i18n, recommender as rec
from core.i18n import tr
from core.note_emoji import note_emoji
from ui import charts
from ui.accord_colors import ACCORD_COLORS
from ui.theme import ACCENT, MUTED


class Tastes(QWidget):
    """Mi colección > Mis gustos: gráficos sobre los perfumes en propiedad."""
    def __init__(s):
        super().__init__(); v = QVBoxLayout(s); v.setContentsMargins(0, 0, 0, 0)
        s.empty = QLabel(); s.empty.setWordWrap(True); s.empty.setStyleSheet(f"color:{MUTED};background:transparent;"); v.addWidget(s.empty)
        s.sc = QScrollArea(); s.sc.setWidgetResizable(True); s.sc.setFrameShape(QFrame.Shape.NoFrame); v.addWidget(s.sc, 1)
        s.inner = QWidget(); s.grid = QGridLayout(s.inner); s.grid.setContentsMargins(0, 0, 8, 8); s.grid.setSpacing(12); s.sc.setWidget(s.inner)
    def _clear(s):
        while s.grid.count():
            w = s.grid.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
    def reload(s):
        s._clear(); col = db.collection_rows("owned")
        s.empty.setText(tr("an.empty")); s.empty.setVisible(not col)
        if not col: return
        P = [db.get(r["id"]) for r in col]; n = len(P)
        fams = Counter()
        for p in P:
            tags = rec.family_tags(p)
            for f_ in tags: fams[i18n.tr_family_word(f_)] += 1 / len(tags)
        notes = rec.note_counts(P); genders = Counter(p.get("gender") for p in P if p.get("gender"))
        ratings = [p["rating_avg"] for p in P if p.get("rating_avg")]
        star = notes.most_common(1)
        gk = {"female": "venus", "male": "mars", "unisex": "unisex"}
        tiles = [(str(n), tr("taste.count.c")), (f"{sum(ratings) / len(ratings):.1f} ★" if ratings else "—", tr("taste.rating")),
                 (fams.most_common(1)[0][0] if fams else "—", tr("taste.family")),
                 ((note_emoji(star[0][0]) + " " + i18n.tr_note(star[0][0]).title()) if star else "—", tr("taste.note")),
                 None]
        row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(12)
        for tile in tiles:
            rl.addWidget(charts.StatTile(*tile) if tile else charts.GenderTile([(gk[g], c) for g, c in genders.most_common() if g in gk], tr("taste.gender")), 1)
        s.grid.addWidget(row, 0, 0, 1, 2)
        # familias
        top = fams.most_common(6); rest = sum(c for _f, c in fams.most_common()[6:])
        data = [(f, c, charts.PALETTE[i]) for i, (f, c) in enumerate(top)] + ([(tr("taste.others"), rest, charts.PALETTE[7])] if rest else [])
        c1 = charts.Card(tr("taste.families"), charts.Donut(data, str(n)))
        # notas
        c2 = charts.Card(tr("taste.notes"), charts.HBars([dict(label=f"{note_emoji(k)} {i18n.tr_note(k).title()}", value=c, text=f"×{c}") for k, c in notes.most_common(8)]))
        # acordes
        acc = Counter()
        for p in P:
            w = rec.parse_weights(p.get("accord_weights")) or {x.strip().lower(): 1.0 for x in re.split(r"[,|]", p.get("accords") or "") if x.strip()}
            for k, v_ in w.items(): acc[k] += v_
        rows = [dict(label=i18n.tr_accord(k).title(), value=v_, color=ACCORD_COLORS.get(i18n.accord_key(k), ACCENT), text=f"{round(100 * v_ / n)}%") for k, v_ in acc.most_common(8)]
        c3 = charts.Card(tr("taste.accords"), charts.HBars(rows), tr("taste.accords.sub"))
        # cuándo
        def share(pairs):
            vals = [sum(float(p.get(c_) or 0) for p in P) for _k, c_ in pairs]; tot = sum(vals)
            return [(k, v_ / tot if tot else 0) for (k, _c), v_ in zip(pairs, vals)]
        wr = [dict(label=i18n.tr_seasons(k).title(), value=v_, icon=k, text=f"{round(100 * v_)}%") for k, v_ in share(rec.SEASON_COLS)]
        wr += [dict(label=({"día": "Día", "noche": "Noche"}[k] if i18n.is_es() else i18n.tr_field(k, i18n.DAY_EN).title()), value=v_, icon=k, text=f"{round(100 * v_)}%") for k, v_ in share(rec.HOURS)]
        c4 = charts.Card(tr("taste.when"), charts.HBars(wr, vmax=1.0), tr("taste.when.sub"))
        # perfil
        axes = []
        for (l, r_), k in zip(i18n.PROFILE_AXES, ("sweet_fresh", "floral_woody", "light_intense")):
            vals = [p[k] if p.get(k) is not None else 50 for p in P]; axes.append((i18n.tr_axis(l).title(), i18n.tr_axis(r_).title(), vals, sum(vals) / len(vals)))
        c5 = charts.Card(tr("taste.profile"), charts.ProfileStrips(axes), tr("taste.profile.sub"))
        # duración vs estela
        pts = [((p["longevity_avg"] - 1) / 4, (p["sillage_avg"] - 1) / 3, p["name"]) for p in P if p.get("longevity_avg") and p.get("sillage_avg")]
        c6 = charts.Card(tr("taste.scatter"), charts.Scatter(pts, tr("taste.long"), tr("taste.sill"), (tr("taste.low"), tr("taste.high"))), tr("taste.scatter.sub"))
        # marcas y épocas
        br = Counter(p.get("brand") for p in P if p.get("brand")).most_common(6)
        c7 = charts.Card(tr("taste.brands"), charts.HBars([dict(label=b_, value=c, text=f"×{c}") for b_, c in br]))
        dec = Counter((p["year"] // 10) * 10 for p in P if p.get("year")); keys = sorted(dec)[-8:]
        c8 = charts.Card(tr("taste.decades"), charts.VBars([(f"{k}s", dec[k]) for k in keys]), tr("taste.decades.sub"))
        for i, c in enumerate((c1, c2, c3, c4, c5, c6, c7, c8)): s.grid.addWidget(c, 1 + i // 2, i % 2)
        s.grid.setColumnStretch(0, 1); s.grid.setColumnStretch(1, 1)
