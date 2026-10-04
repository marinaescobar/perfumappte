"""Recomendaciones: filtros por ocasión, hora y estación (y un perfume concreto) con layering y opciones de compra."""
import html
from collections import Counter
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from core import db, i18n, recommender as rec
from core.i18n import tr
from ui import images
from ui.cards import CardList, PairCard
from ui.theme import MUTED
from ui.widgets import MultiSelect


class RecsPage(QWidget):
    """Recomendaciones: filtros por ocasión, hora, estación (y un perfume concreto) sobre Mi colección, con layering y opciones de compra."""
    BUY_N = 12
    open_profile = pyqtSignal(int)
    def __init__(s):
        super().__init__(); v = QVBoxLayout(s); v.setContentsMargins(26, 22, 26, 16); v.setSpacing(8)
        s.h = QLabel(); s.h.setObjectName("h1"); v.addWidget(s.h)
        row = QHBoxLayout(); v.addLayout(row)
        s.m_occ, s.m_hour, s.m_sea = MultiSelect(), MultiSelect(), MultiSelect(); s.m_pick = MultiSelect(single=True)
        for m in (s.m_occ, s.m_hour, s.m_sea): m.setMinimumWidth(190); m.changed.connect(s.refresh); row.addWidget(m)
        s.m_pick.setMinimumWidth(240); s.m_pick.changed.connect(s.refresh); row.addWidget(s.m_pick); row.addStretch(1)
        row2 = QHBoxLayout(); v.addLayout(row2)
        s.layer, s.buy = QPushButton(), QPushButton()
        for b in (s.layer, s.buy): b.setObjectName("tgl"); b.setCheckable(True); b.setCursor(Qt.CursorShape.PointingHandCursor); b.toggled.connect(s.refresh); row2.addWidget(b)
        s.want = QLabel(); s.want.setStyleSheet(f"color:{MUTED};background:transparent;")
        s.mode_comp, s.mode_sim = QPushButton(), QPushButton(); s.modegrp = QButtonGroup(s)
        row2.addSpacing(8); row2.addWidget(s.want)
        for b in (s.mode_comp, s.mode_sim): b.setObjectName("tgl"); b.setCheckable(True); b.setCursor(Qt.CursorShape.PointingHandCursor); s.modegrp.addButton(b); row2.addWidget(b)
        s.mode_comp.setChecked(True); s.mode_comp.toggled.connect(s.refresh)
        s.rclr = QPushButton(); s.rclr.clicked.connect(s.clear_reco); row2.addWidget(s.rclr); row2.addStretch(1)
        s.rinfo = QLabel(); s.rinfo.setStyleSheet(f"color:{MUTED}"); v.addWidget(s.rinfo)
        s.rlv = CardList(); s.rlv.dg.badges = False
        s.rlv.doubleClicked.connect(lambda i: s.open_profile.emit(s.rlv.mdl.data(i, Qt.ItemDataRole.UserRole)["id"]))
        v.addWidget(s.rlv, 1)
        # layering
        s.lay_box = QWidget(); lb = QVBoxLayout(s.lay_box); lb.setContentsMargins(0, 0, 0, 0); lb.setSpacing(6)
        s.lay_h = QLabel(); s.lay_h.setStyleSheet("font-weight:600;background:transparent;"); lb.addWidget(s.lay_h)
        s.lay_scroll = QScrollArea(); s.lay_scroll.setWidgetResizable(True); s.lay_scroll.setFrameShape(QFrame.Shape.NoFrame)
        s.lay_in = QWidget(); s.lay_l = QVBoxLayout(s.lay_in); s.lay_l.setContentsMargins(0, 0, 8, 0); s.lay_l.setSpacing(8); s.lay_l.addStretch(1)
        s.lay_scroll.setWidget(s.lay_in); lb.addWidget(s.lay_scroll, 1); v.addWidget(s.lay_box, 1); s.lay_box.hide()
        # compras
        s.buy_box = QWidget(); bb = QVBoxLayout(s.buy_box); bb.setContentsMargins(0, 0, 0, 0); bb.setSpacing(6)
        s.buy_h = QLabel(); s.buy_h.setStyleSheet("font-weight:600;background:transparent;"); bb.addWidget(s.buy_h)
        s.blv = CardList(); bb.addWidget(s.blv, 1); v.addWidget(s.buy_box, 1); s.buy_box.hide()
        s.blv.doubleClicked.connect(lambda i: s.open_profile.emit(s.blv.mdl.data(i, Qt.ItemDataRole.UserRole)["id"]))
        s.blv.dg.badge.connect(lambda pid: s._mark(pid, "owned")); s.blv.dg.heart.connect(lambda pid: s._mark(pid, "wishlist"))
        s.pairs = []
        images.get_cache().loaded.connect(s._img_loaded)
        s.retranslate()
    def _mark(s, pid, status):
        if status == "wishlist" and db.get(pid)["status"] == "wishlist": db.remove_from_collection(pid)
        else: db.set_collection(pid, status)
        s.refresh()
    def _img_loaded(s, key, *_):
        for pc in s.pairs:
            for c in pc.cards:
                if c.key == key: c.set_pix()
    def clear_reco(s):
        for b in (s.layer, s.buy): b.blockSignals(True); b.setChecked(False); b.blockSignals(False)
        for m in (s.m_occ, s.m_hour, s.m_sea, s.m_pick): m.clear()
        s.refresh()
    def retranslate(s):
        s.h.setText(tr("rec.h"))
        s.m_occ.set_items([(k, i18n.tr_occasions(k)) for k in rec.OCCASIONS], tr("rec.occ"))
        s.m_hour.set_items([(k, i18n.tr_field(k, i18n.DAY_EN)) for k, _c in rec.HOURS], tr("rec.hour"))
        s.m_sea.set_items([(k, i18n.tr_seasons(k)) for k in rec.SEASONS], tr("rec.sea"))
        s.m_pick.title = tr("rec.pick")
        for m, k in ((s.m_occ, "occ"), (s.m_hour, "hour"), (s.m_sea, "sea"), (s.m_pick, "pick")): m.setToolTip(tr("tip.rec." + k))
        s.layer.setToolTip(tr("tip.rec.layer")); s.buy.setToolTip(tr("tip.rec.buy")); s.buy_h.setText(tr("rec.buy.h"))
        s.want.setText(tr("rec.want")); s.mode_comp.setText(tr("rec.mode.comp")); s.mode_sim.setText(tr("rec.mode.sim"))
        s.mode_comp.setToolTip(tr("tip.rec.mode.comp")); s.mode_sim.setToolTip(tr("tip.rec.mode.sim"))
        s.rclr.setText(tr("browser.filter.clear")); s.rclr.setToolTip(tr("tip.clear"))
        s.refresh()
    def _fit(s, p, occ, hours, seas):
        """Puntuación 0..1 de un perfume para lo elegido (None si no encaja). Entre grupos se exige todo; dentro de un grupo, cualquiera."""
        toks = lambda v, table: set(i18n.canon_tokens([x.strip() for x in str(v).split(",") if x.strip()], table)) if v else set()
        def votes(pairs):
            v = {k: float(p.get(c) or 0) for k, c in pairs}; m = max(v.values())
            return {k: x / m for k, x in v.items()} if m > 0 else None
        scores = []
        if occ:
            have = toks(p.get("occasion"), i18n.OCC_EN); hit = sum(k in have for k in occ)
            if not hit: return None
            scores.append(hit / len(occ))
        for chosen, pairs, col, table in ((seas, rec.SEASON_COLS, "season", i18n.SEA_EN), (hours, rec.HOURS, None, None)):
            if not chosen: continue
            fr = votes(pairs)
            if fr is None and col and p.get(col): have = toks(p.get(col), table); fr = {k: 1.0 if k in have else 0.0 for k, _c in pairs}
            sc = max((fr.get(k, 0) for k in chosen), default=0) if fr else 0
            if sc < 0.5: return None
            scores.append(sc)
        return sum(scores) / len(scores) if scores else 1.0
    def _set_pairs(s, found):
        while s.lay_l.count() > 1:
            w = s.lay_l.takeAt(0).widget()
            if w: w.hide(); w.deleteLater()
        s.pairs = []
        if not found:
            n = QLabel(tr("rec.layer.none")); n.setStyleSheet(f"color:{MUTED};background:transparent;"); s.lay_l.insertWidget(0, n); return
        for i, (_sc, a, b, why) in enumerate(found):
            pc = PairCard(a, b, why, db.fav_has(a["id"], b["id"])); pc.opened.connect(s.open_profile.emit)
            pc.fav_toggled.connect(lambda x, y, on: db.fav_set(x, y, on)); s.lay_l.insertWidget(i, pc); s.pairs.append(pc)
    def _suggest(s, owned, occ, hours, seas, anchor=None, similar=False):
        """Perfumes de la base que no están en propiedad y muy populares.
        Complementarios: lo que le falta a la colección (o encaja en layering con el perfume elegido).
        Similares: los que más se parecen al perfume elegido o, sin elegir, a lo que ya tienes.
        El reparto por género sigue el de la colección (p. ej. femenino y unisex en su proporción)."""
        mix = Counter(p.get("gender") for p in owned if p.get("gender"))
        if anchor is not None and similar and anchor.get("gender"):
            mix = Counter({anchor["gender"]: 3, "unisex": 1}) if anchor["gender"] != "unisex" else Counter()
        gp = rec.gaps(owned); gapfam = set(gp["families"]); filt = bool(occ or hours or seas)
        refs = [anchor] if anchor is not None else owned
        pre = []
        for c in db.candidates(4000, list(mix) or None):
            f = s._fit(c, occ, hours, seas) if filt else 1.0
            if f is None: continue
            rec.fill_axes(c); base = 0.25 * (c["score"] or 0) / 5 + (0.15 * f if filt else 0.0)
            if similar:
                sims = sorted((rec.similarity(c, o) for o in refs), reverse=True)
                top = sims[:1] if anchor is not None else sims[:3]
                base += 0.6 * (sum(top) / len(top) if top else 0)
            else:
                fam = rec.family_tags(c); base += 0.35 * (len(fam & gapfam) / len(fam) if fam else 0.0)
            pre.append([base, c])
        pre.sort(key=lambda x: -x[0])
        if not similar:                                                      # complementarios: compatibilidad de layering con lo que ya tienes
            pre = pre[:600]
            for item in pre: item[0] += 0.25 * min(1.0, max((rec.layer_points(item[1], o) for o in refs), default=0) / 3)
            pre.sort(key=lambda x: -x[0])
        if not mix: out = [c for _s, c in pre[:s.BUY_N]]
        else:
            tot = sum(mix.values()); quota = {g: max(1, round(s.BUY_N * n / tot)) for g, n in mix.items()}
            while sum(quota.values()) > s.BUY_N: quota[max(quota, key=quota.get)] -= 1
            while sum(quota.values()) < s.BUY_N: quota[max(mix, key=mix.get)] += 1
            out, used = [], set()
            for g, q in quota.items():
                for _s, c in [x for x in pre if x[1].get("gender") == g][:q]: out.append(c); used.add(c["id"])
            for _s, c in pre:                                                # si un género se queda corto, se completa con el resto
                if len(out) >= s.BUY_N: break
                if c["id"] not in used: out.append(c); used.add(c["id"])
            rank = {c["id"]: i for i, (_s, c) in enumerate(pre)}
            out.sort(key=lambda c: rank[c["id"]])
        chosen = []
        if occ: chosen += [i18n.tr_occasions(k) for k in occ]
        if seas: chosen += [i18n.tr_seasons(k) for k in seas]
        if hours: chosen += [i18n.tr_field(k, i18n.DAY_EN) for k in hours]
        for c in out: c["_why"] = s._why(c, refs, gapfam, mix, chosen, similar)
        return out
    @staticmethod
    def _why(c, refs, gapfam, mix, chosen, similar):
        """Motivos (ya traducidos y escapados) por los que `c` encaja."""
        e = html.escape; why = []
        if chosen: why.append(tr("buy.why.filt", e(", ".join(chosen))))
        if similar:
            best = max(((rec.similarity(c, o), o) for o in refs), key=lambda x: x[0], default=None)
            if best:
                why.append(tr("buy.why.sim", e(best[1]["name"]), round(best[0] * 100)))
                sh = sorted(rec.note_set(c) & rec.note_set(best[1]))[:4]
                if sh: why.append(tr("buy.why.notes", e(", ".join(i18n.tr_note(n) for n in sh))))
        else:
            new = [f for f in rec.family_tags(c) if f in gapfam]
            if new: why.append(tr("buy.why.fam", e(", ".join(i18n.tr_family_word(f) for f in new))))
            best = max(((rec.layer_score(c, o), o) for o in refs), key=lambda x: x[0][0], default=None)
            if best and best[0][1]: why.append(tr("buy.why.layer", e(best[1]["name"]), e("; ".join(best[0][1]))))
        if c.get("rating_avg") and c.get("vote_count"): why.append(tr("buy.why.rating", f"{c['rating_avg']:.1f}", f"{c['vote_count']:,}"))
        if len(mix) > 1 and c.get("gender"): why.append(tr("buy.why.gender", e(i18n.tr_gender(c["gender"]))))
        return why
    def refresh(s, *_):
        occ, hours, seas = s.m_occ.values(), s.m_hour.values(), s.m_sea.values()
        filt, lay, buy = bool(occ or hours or seas), s.layer.isChecked(), s.buy.isChecked()
        s.layer.setText(("✓  " if lay else "") + tr("rec.layer")); s.buy.setText(("✓  " if buy else "") + tr("rec.buy"))
        for w in (s.want, s.mode_comp, s.mode_sim): w.setVisible(buy)
        col = db.collection_rows("owned")
        s.m_pick.set_items([(r["id"], f"{r['name']} — {r['brand'] or ''}") for r in col])
        pick = s.m_pick.values(); aid = pick[0] if pick else None
        s.lay_box.setVisible(lay); s.buy_box.setVisible(buy); s.rlv.setVisible(filt or aid is not None or not (lay or buy))
        if not (filt or lay or buy or aid is not None): s.rlv.set_rows([]); s.rinfo.setText(tr("rec.hint")); return
        if not col:
            s.rlv.set_rows([]); s.blv.set_rows([]); s._set_pairs([]); s.rinfo.setText(tr("rec.empty")); s.lay_box.hide(); s.buy_box.hide(); return
        fulls = {r["id"]: rec.fill_axes(db.get(r["id"])) for r in col}; anchor = fulls.get(aid)
        if filt:
            scored = []
            for r in col:
                f = s._fit(fulls[r["id"]], occ, hours, seas)
                if f is not None: scored.append((f, r.get("rating_avg") or 0, r))
            scored.sort(key=lambda x: (-x[0], -x[1]))
            s.rlv.set_rows([r for _f, _g, r in scored]); s.rinfo.setText(tr("rec.found", len(scored), len(col)) if scored else tr("rec.none"))
            matched = [fulls[r["id"]] for _f, _g, r in scored]
        elif anchor is not None:
            s.rlv.set_rows([r for r in col if r["id"] == aid]); s.rinfo.setText(""); matched = list(fulls.values())
        else:
            s.rlv.set_rows([]); s.rinfo.setText(""); matched = list(fulls.values())
        if lay:
            n = 10 if filt else None                                          # sin filtros: TODAS las combinaciones posibles
            found = rec.layering_with(anchor, matched, n) if anchor is not None else rec.layering(matched, n)
            s._set_pairs(found)
            s.lay_h.setText((tr("rec.layer.with", anchor["name"]) if anchor is not None else tr("rec.layer.h")) + (f"  ·  {len(found)}" if found else ""))
        if buy:
            sim = s.mode_sim.isChecked()
            sug = s._suggest(list(fulls.values()), occ, hours, seas, anchor, sim)
            head = tr("rec.buy.sa", anchor["name"]) if (sim and anchor is not None) else tr("rec.buy.s") if sim else tr("rec.buy.f" if filt else "rec.buy.c")
            s.blv.set_rows(sug); s.buy_h.setText(head + (f"  ·  {len(sug)}" if sug else "  ·  " + tr("rec.buy.none")))
