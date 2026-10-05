"""Mi colección > Mis gustos: gráficos sobre los perfumes en propiedad.

Los gráficos están enlazados: al pasar el ratón por un elemento (una nota, una familia, un acorde, una marca, una década, una estación, un punto…)
se calcula el grupo de perfumes que cae en esa categoría y todos los gráficos resaltan lo que ese grupo aporta; arriba se listan sus nombres.
"""
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
    MAX_NAMES = 12
    def __init__(s):
        super().__init__(); v = QVBoxLayout(s); v.setContentsMargins(0, 0, 0, 0); s.src = {}; s.targets = []; s.names = []
        s.empty = QLabel(); s.empty.setWordWrap(True); s.empty.setStyleSheet(f"color:{MUTED};background:transparent;"); v.addWidget(s.empty)
        s.cap = QLabel(); s.cap.setWordWrap(True); s.cap.setMinimumHeight(40); s.cap.setStyleSheet(f"color:{MUTED};background:transparent;"); v.addWidget(s.cap)
        s.sc = QScrollArea(); s.sc.setWidgetResizable(True); s.sc.setFrameShape(QFrame.Shape.NoFrame); v.addWidget(s.sc, 1)
        s.inner = QWidget(); s.grid = QGridLayout(s.inner); s.grid.setContentsMargins(0, 0, 8, 8); s.grid.setSpacing(12); s.sc.setWidget(s.inner)
    def _clear(s):
        s.src.clear(); s.targets.clear()
        while s.grid.count():
            w = s.grid.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
    # ---------- enlace entre gráficos
    def _link(s, chart, members, labels, fn):
        """`members[i]`: índices de los perfumes del elemento i del gráfico; `fn(S)`: lo que debe resaltar este gráfico para el grupo S."""
        s.src[chart] = (members, labels); s.targets.append((chart, fn)); chart.hovered.connect(lambda i, c=chart: s._hover(c, i))
    def _hover(s, chart, i):
        members, labels = s.src[chart]
        if i < 0 or i >= len(members):
            for c, _fn in s.targets: c.set_highlight(None)
            s.cap.setText(tr("taste.hint")); return
        S = members[i]
        for c, fn in s.targets: c.set_highlight(fn(S))
        names = sorted(s.names[j] for j in S); shown = ", ".join(names[:s.MAX_NAMES]) + (" …" if len(names) > s.MAX_NAMES else "")
        s.cap.setText(f"<b>{labels[i]}</b> · {tr('taste.cap.1' if len(S) == 1 else 'taste.cap.n', len(S))}: {shown}" if S else f"<b>{labels[i]}</b>")
    # ---------- contenido
    def reload(s):
        s._clear(); col = db.collection_rows("owned")
        s.empty.setText(tr("an.empty")); s.empty.setVisible(not col); s.cap.setVisible(bool(col)); s.cap.setText(tr("taste.hint"))
        if not col: return
        P = [db.get(r["id"]) for r in col]; n = len(P); s.names = [p["name"] for p in P]; idx = range(n)
        tags = [{i18n.tr_family_word(f_) for f_ in rec.family_tags(p)} for p in P]
        fams = Counter()
        for t in tags:
            for f_ in t: fams[f_] += 1 / len(t)
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
        top = fams.most_common(6); rest = [f for f, _c in fams.most_common()[6:]]; rest_n = sum(fams[f] for f in rest)
        data = [(f, c, charts.PALETTE[i]) for i, (f, c) in enumerate(top)] + ([(tr("taste.others"), rest_n, charts.PALETTE[7])] if rest else [])
        donut = charts.Donut(data, str(n)); c1 = charts.Card(tr("taste.families"), donut)
        def fam_sub(S):
            c = Counter()
            for i in S:
                for f_ in tags[i]: c[f_] += 1 / len(tags[i])
            return [c[f] for f, _v in top] + ([sum(c[f] for f in rest)] if rest else [])
        s._link(donut, [{i for i in idx if f in tags[i]} for f, _v in top] + ([{i for i in idx if tags[i] & set(rest)}] if rest else []), [d[0] for d in data], fam_sub)
        # notas
        nset = [rec.note_set(p) for p in P]; top_notes = [k for k, _c in notes.most_common(8)]
        hb = charts.HBars([dict(label=f"{note_emoji(k)} {i18n.tr_note(k).title()}", value=notes[k], text=f"×{notes[k]}") for k in top_notes]); c2 = charts.Card(tr("taste.notes"), hb)
        s._link(hb, [{i for i in idx if k in nset[i]} for k in top_notes], [f"{note_emoji(k)} {i18n.tr_note(k).title()}" for k in top_notes], lambda S: [sum(1 for i in S if k in nset[i]) for k in top_notes])
        # acordes
        W = [rec.parse_weights(p.get("accord_weights")) or {x.strip().lower(): 1.0 for x in re.split(r"[,|]", p.get("accords") or "") if x.strip()} for p in P]
        acc = Counter()
        for w in W:
            for k, v_ in w.items(): acc[k] += v_
        top_acc = acc.most_common(8)
        rows = [dict(label=i18n.tr_accord(k).title(), value=v_, color=ACCORD_COLORS.get(i18n.accord_key(k), ACCENT), text=f"{round(100 * v_ / n)}%") for k, v_ in top_acc]
        hb = charts.HBars(rows); c3 = charts.Card(tr("taste.accords"), hb, tr("taste.accords.sub"))
        s._link(hb, [{i for i in idx if k in W[i]} for k, _v in top_acc], [r["label"] for r in rows], lambda S: [sum(W[i].get(k, 0) for i in S) for k, _v in top_acc])
        # cuándo: pertenecen a una fila los perfumes cuyo voto está por encima de la media de la colección
        wr, wcols = [], []
        for pairs in (rec.SEASON_COLS, rec.HOURS):
            vals = [sum(float(p.get(c_) or 0) for p in P) for _k, c_ in pairs]; tot = sum(vals)
            for (k, c_), v_ in zip(pairs, vals):
                lab = i18n.tr_seasons(k).title() if pairs is rec.SEASON_COLS else ({"día": "Día", "noche": "Noche"}[k] if i18n.is_es() else i18n.tr_field(k, i18n.DAY_EN).title())
                share = v_ / tot if tot else 0; wr.append(dict(label=lab, value=share, icon=k, text=f"{round(100 * share)}%")); wcols.append((c_, tot, v_ / n))
        def when_members(c_, mean): return {i for i in idx if float(P[i].get(c_) or 0) > 0 and float(P[i].get(c_) or 0) >= mean}
        hb = charts.HBars(wr, vmax=1.0); c4 = charts.Card(tr("taste.when"), hb, tr("taste.when.sub"))
        s._link(hb, [when_members(c_, m) for c_, _t, m in wcols], [r["label"] for r in wr], lambda S: [sum(float(P[i].get(c_) or 0) for i in S) / tot if tot else 0 for c_, tot, _m in wcols])
        # perfil olfativo (radar): un eje por cada extremo de los tres ejes (los opuestos enfrentados)
        ax = list(zip(i18n.PROFILE_AXES, ("sweet_fresh", "floral_woody", "light_intense")))
        labels = [i18n.tr_axis(r_).title() for (_l, r_), _k in ax] + [i18n.tr_axis(l).title() for (l, _r), _k in ax]
        per = []
        for p in P:
            v3 = [(p[k] if p.get(k) is not None else 50) / 100 for _a, k in ax]; per.append(v3 + [1 - x for x in v3])
        radar = charts.Radar(labels, per); c5 = charts.Card(tr("taste.profile"), radar, tr("taste.profile.sub"))
        s.targets.append((radar, lambda S: set(S)))
        # duración vs estela
        pts = [((p["longevity_avg"] - 1) / 4, (p["sillage_avg"] - 1) / 3, p["name"]) for p in P if p.get("longevity_avg") and p.get("sillage_avg")]
        pt_idx = [i for i, p in enumerate(P) if p.get("longevity_avg") and p.get("sillage_avg")]
        sc = charts.Scatter(pts, tr("taste.long"), tr("taste.sill"), (tr("taste.low"), tr("taste.high"))); c6 = charts.Card(tr("taste.scatter"), sc, tr("taste.scatter.sub"))
        s._link(sc, [{i} for i in pt_idx], [pt[2] for pt in pts], lambda S: {j for j, i in enumerate(pt_idx) if i in S})
        # marcas y épocas
        br = Counter(p.get("brand") for p in P if p.get("brand")).most_common(6)
        hb = charts.HBars([dict(label=b_, value=c, text=f"×{c}") for b_, c in br]); c7 = charts.Card(tr("taste.brands"), hb)
        s._link(hb, [{i for i in idx if P[i].get("brand") == b_} for b_, _c in br], [b_ for b_, _c in br], lambda S: [sum(1 for i in S if P[i].get("brand") == b_) for b_, _c in br])
        dec = Counter((p["year"] // 10) * 10 for p in P if p.get("year")); keys = sorted(dec)[-8:]
        vb = charts.VBars([(f"{k}s", dec[k]) for k in keys]); c8 = charts.Card(tr("taste.decades"), vb, tr("taste.decades.sub"))
        dec_of = lambda i: (P[i]["year"] // 10) * 10 if P[i].get("year") else None
        s._link(vb, [{i for i in idx if dec_of(i) == k} for k in keys], [f"{k}s" for k in keys], lambda S: [sum(1 for i in S if dec_of(i) == k) for k in keys])
        for i, c in enumerate((c1, c2, c3, c4, c5, c6, c7, c8)): s.grid.addWidget(c, 1 + i // 2, i % 2)
        s.grid.setColumnStretch(0, 1); s.grid.setColumnStretch(1, 1)
