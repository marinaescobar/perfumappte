import re, random, itertools, heapq
from collections import Counter
from datetime import date
from core import i18n
from core.i18n import norm, tr

OCCASIONS = i18n.OCCASIONS            # valores canónicos (español); se traducen al mostrar
SEASONS = i18n.SEASONS
FAMILIES = i18n.FAMILIES_ES_EN        # nombre -> fragmentos sin acentos (ES/EN)
COMP = {("Cítrica","Amaderada"),("Floral","Amaderada"),("Gourmand","Acuática"),("Gourmand","Cítrica"),
        ("Oriental","Floral"),("Oriental","Cítrica"),("Aromática","Gourmand"),("Cuero","Floral"),
        ("Especiada","Cítrica"),("Chipre","Cítrica"),("Fougère","Oriental"),("Frutal","Amaderada")}
FRESH = "citr limon lima bergamot mandarin tangerine naranja pomelo menta mint marin acuat tea verde green pepino cucumber manzana apple lavand albahaca basil aromat lemon orange grapefruit ozon fresh".split()
SWEET = "vainilla vanilla caramel miel honey tonka praline chocolate cacao cocoa azucar sugar almendra almond coco canela cinnamon cafe coffee frambuesa raspberry fresa strawberry sweet candy".split()
FLORAL = "rosa rose jazmin jasmine iris peon lirio lily violet flor flower blossom azahar ylang tuberos magnolia neroli gardenia freesia orquidea orchid honeysuckle floral".split()
WOODY = "cedro cedar sandalo sandal vetiver pachuli patchouli madera wood oud cuero leather incienso incense musgo moss abedul birch guayacan papiro".split()

def split_notes(s):
    return [n.strip().lower() for n in re.split(r"[,;]", s or "") if n.strip()]

def all_notes(p):
    return (split_notes(p.get("top_notes")) + split_notes(p.get("heart_notes")) + split_notes(p.get("base_notes")) + split_notes(p.get("flat_notes")))

def estimate_profile(d):
    txt = norm(" ".join(str(d.get(k) or "") for k in ("family", "accords", "top_notes", "heart_notes", "base_notes", "flat_notes")))
    cnt = lambda ws: sum(txt.count(w) for w in ws)
    sf = max(0, min(100, 50 + 12 * (cnt(FRESH) - cnt(SWEET))))
    fw = max(0, min(100, 50 + 12 * (cnt(WOODY) - cnt(FLORAL))))
    la, sa = d.get("longevity_avg"), d.get("sillage_avg")
    if la and sa: return sf, fw, int(max(0, min(100, ((la - 1) / 4 + (sa - 1) / 3) / 2 * 100)))
    li = {"edc": 20, "colonia": 20, "edt": 40, "edp": 62, "parfum": 80, "extrait": 85}.get(norm(d.get("concentration")), 50)
    li += {"corta": -10, "larga": 8, "eterna": 14}.get(norm(d.get("longevity")), 0)
    li += {"suave": -10, "fuerte": 8, "enorme": 14}.get(norm(d.get("sillage")), 0)
    return sf, fw, max(0, min(100, li))

def family_tags(p):
    if "_ft" not in p:
        t = norm(p.get("family")); p["_ft"] = {k for k, toks in FAMILIES.items() if any(x in t for x in toks)}
    return p["_ft"]

def note_set(p):
    if "_ns" not in p: p["_ns"] = set(all_notes(p))
    return p["_ns"]

def parse_weights(raw):
    """«nombre:0.87|otro:0.5» -> {nombre en minúsculas: 0.87}. Ignora trozos vacíos o mal formados."""
    out = {}
    for part in str(raw or "").split("|"):
        n, sep, v = part.strip().rpartition(":")
        if not sep: continue
        try: out[n.strip().lower()] = float(v)
        except ValueError: pass
    return out

# estaciones (clave canónica, columna de votos) y momentos del día: se usan en recomendaciones, gráficos y en Góngora
SEASON_COLS = [("primavera", "spring"), ("verano", "summer"), ("otoño", "autumn"), ("invierno", "winter")]
HOURS = [("día", "day"), ("noche", "night")]

def fill_axes(p):
    """Rellena con 50 los ejes del perfil olfativo que falten, para poder comparar perfumes."""
    for k in ("sweet_fresh", "floral_woody", "light_intense"):
        if p.get(k) is None: p[k] = 50
    return p

def similarity(a, b):
    na, nb = note_set(a), note_set(b)
    j = len(na & nb) / len(na | nb) if na | nb else 0
    dist = sum(abs(a[k] - b[k]) for k in ("sweet_fresh", "floral_woody", "light_intense")) / 300
    return 0.6 * j + 0.2 * bool(family_tags(a) & family_tags(b)) + 0.2 * (1 - dist)

def similar_to(p, pool, n=8):
    return heapq.nlargest(n, ((similarity(p, q), q) for q in pool if q["id"] != p["id"]), key=lambda x: x[0])

_FIELD_TABLE = {"season": i18n.SEA_EN, "occasion": i18n.OCC_EN}
def by_field(rows, field, val):
    """El valor se acepta en español o en inglés: «oficina» y «office» filtran lo mismo."""
    vals = i18n.canon_tokens(val, _FIELD_TABLE.get(field, {}))
    toks = [norm(v) for v in vals if norm(v)]
    return [p for p in rows if any(t in norm(p.get(field)) for t in toks)]

def accord_set(p):
    if "_as" not in p:
        wts = parse_weights(p.get("accord_weights"))
        p["_as"] = {norm(k) for k, v in wts.items() if v >= 0.5} if wts else {norm(x) for x in re.split(r"[,|]", p.get("accords") or "") if x.strip()}
    return p["_as"]

def _layer_parts(a, b):
    """Piezas de la compatibilidad de layering: (parejas de familias que se complementan, notas compartidas, acordes compartidos, puntuación)."""
    fams = [(x, y) for x, y in itertools.product(family_tags(a), family_tags(b)) if (x, y) in COMP or (y, x) in COMP]
    sh, ac = note_set(a) & note_set(b), accord_set(a) & accord_set(b)
    s = 2 * len(fams) + (1.5 if 1 <= len(sh) <= 2 else -1 if len(sh) >= 4 else 0) + (1 if 1 <= len(ac) <= 2 else 0)
    return fams, sh, ac, s + abs(a["sweet_fresh"] - b["sweet_fresh"]) / 100

def layer_points(a, b):
    """Solo la puntuación de compatibilidad (rápida: no traduce ni arma textos)."""
    return _layer_parts(a, b)[3]

def layer_score(a, b):
    """(puntuación, motivos ya traducidos) de combinar los perfumes `a` y `b`."""
    fams, sh, ac, s = _layer_parts(a, b); why = [tr("why.layer", i18n.tr_family_word(x), i18n.tr_family_word(y)) for x, y in fams]
    if 1 <= len(sh) <= 2: why.append(tr("why.bridge") + ", ".join(i18n.tr_note(n) for n in sorted(sh)))
    elif len(sh) >= 4: why.append(tr("why.same"))
    if 1 <= len(ac) <= 2: why.append(tr("why.accord") + ", ".join(i18n.tr_accord(n).lower() for n in sorted(ac)))
    return s, why

def layer_weight(p):
    """Cuánto «pesa» un perfume: intensidad del perfil más duración y estela. El más pesado va de base."""
    return ((p.get("light_intense") if p.get("light_intense") is not None else 50) + 6 * ((p.get("longevity_avg") or 3) - 3)
            + 6 * ((p.get("sillage_avg") or 2.5) - 2.5))

def spray_count(p):
    """Atomizaciones recomendadas (1-4): cuanto más dura y más proyecta el perfume, menos hace falta."""
    s = estimate_profile(p)[2] / 100
    return max(1, min(4, round(4.4 - 3 * s)))

def layering(owned, n=8):
    """(puntuación, base, encima, motivos): el perfume más pesado de la pareja es la base y el más ligero va encima."""
    out = []
    for a, b in itertools.combinations(owned, 2):
        s, why = layer_score(a, b)
        if why:
            base, top = (a, b) if layer_weight(a) >= layer_weight(b) else (b, a)
            out.append((s, base, top, why))
    out.sort(key=lambda x: -x[0])
    return out if n is None else out[:n]

def layering_with(anchor, others, n=8):
    """Combinaciones de un perfume concreto con el resto: (puntuación, base, encima, motivos)."""
    out = []
    for b in others:
        if b["id"] == anchor["id"]: continue
        s, why = layer_score(anchor, b)
        if why:
            base, top = (anchor, b) if layer_weight(anchor) >= layer_weight(b) else (b, anchor)
            out.append((s, base, top, why))
    out.sort(key=lambda x: -x[0])
    return out if n is None else out[:n]

def gaps(owned):
    fams = set().union(*(family_tags(p) for p in owned)) if owned else set()
    g = {"families": [f for f in FAMILIES if f not in fams],
         "seasons": [s for s in SEASONS if not by_field(owned, "season", s)],
         "occasions": [o for o in OCCASIONS if not by_field(owned, "occasion", o)], "profile": []}
    for k, lo, hi in (("sweet_fresh", "dulce", "fresco"), ("floral_woody", "floral", "amaderado"), ("light_intense", "ligero", "intenso")):
        if not any(p[k] < 35 for p in owned): g["profile"].append(lo)
        if not any(p[k] > 65 for p in owned): g["profile"].append(hi)
    return g

def suggest_for_gaps(g, pool, owned_ids, n=6):
    def score(p):
        if "_sn" not in p: p["_sn"], p["_on"] = norm(p.get("season")), norm(p.get("occasion"))
        return (2 * len(family_tags(p) & set(g["families"])) + sum(s in p["_sn"] for s in g["seasons"])
                + sum(o in p["_on"] for o in g["occasions"]))
    return heapq.nlargest(n, [p for p in pool if p["id"] not in owned_ids], key=score)

def note_counts(rows):
    return Counter(n for p in rows for n in set(all_notes(p)))

def fmt(p): return f"{p['name']} ({p['brand']})"

def current_season():
    return SEASONS[{3:0,4:0,5:0,6:1,7:1,8:1,9:2,10:2,11:2}.get(date.today().month, 3)]

def find_named(t, rows):
    best = None
    for p in rows:
        n = p.setdefault("_nn", norm(p["name"]))
        if len(n) > 2 and re.search(r"\b" + re.escape(n) + r"\b", t) and (not best or len(n) > len(norm(best["name"]))):
            best = p
    return best

K_COMBINE = i18n.chat_keywords("combin,mezcl,capa,mezcla,capas,parej,unir", "combin,layer,blend,mix,pair")
K_GAPS = i18n.chat_keywords("falta,hueco,complet", "missing,gap,complete,lacking")
K_SIM = i18n.chat_keywords("similar,parecid,alternativ,clon,parejo", "similar,alike,alternative,clone")
K_TODAY = i18n.chat_keywords("hoy,pongo,ponga,llevar,elegir,recomiend", "today,wear,choose,pick,suggest,recommend")

def chat_answer(text, owned, pool):
    """El asistente entiende preguntas en español y en inglés."""
    t = norm(text)
    if not owned: return tr("chat.empty")
    named = find_named(t, owned) or find_named(t, pool)
    if re.search(K_COMBINE, t):
        if named:
            c = sorted(((layer_score(named, q)[0], q, layer_score(named, q)[1]) for q in owned if q["id"] != named["id"]), key=lambda x: -x[0])[:3]
            if not c: return tr("chat.combine.need")
            return tr("chat.combine.for", fmt(named)) + "<br>".join(f"• {fmt(q)} — {'; '.join(w) or tr('why.contrast')}" for _, q, w in c) + "<br>" + tr("chat.combine.tip")
        l = layering(owned, 3)
        return (tr("chat.combine.best") + "<br>".join(f"• {fmt(a)} + {fmt(b)} — {'; '.join(w)}" for _, a, b, w in l)) if l else tr("chat.combine.none")
    if re.search(K_GAPS, t):
        g = gaps(owned); sug = suggest_for_gaps(g, pool, {p["id"] for p in owned}, 4)
        lst = lambda xs, f: ", ".join(f(x) for x in xs) or "—"
        return tr("chat.gaps", lst(g["families"], i18n.tr_family_word) or tr("none.f"),
                  lst(g["seasons"], i18n.tr_seasons) or tr("none.f"),
                  lst(g["occasions"], i18n.tr_occasions) or tr("none.f"),
                  lst(g["profile"], i18n.tr_axis) or tr("none.m"),
                  ", ".join(fmt(p) for p in sug) or "—")
    if re.search(K_SIM, t):
        if not named: return tr("chat.similar.need")
        return tr("chat.similar.for", fmt(named)) + "<br>".join(f"• {fmt(q)} ({int(s*100)}%)" for s, q in similar_to(named, pool, 5))
    occ = next((o for o in OCCASIONS if norm(o) in t or norm(i18n.OCC_EN[o]) in t), None)
    sea = next((s for s in SEASONS if norm(s) in t or norm(i18n.SEA_EN[s]) in t), None)
    if re.search(K_TODAY, t) or occ or sea:
        sea_c = sea or current_season()
        sc = sorted(owned, key=lambda p: -(2 * (sea_c in norm(p.get("season"))) + 2 * bool(occ and occ in norm(p.get("occasion"))) + random.random()))[:3]
        when = i18n.tr_occasions(occ) if occ else tr("chat.today.word")
        return tr("chat.today", when, i18n.tr_seasons(sea_c)) + \
            "<br>".join(f"• {fmt(p)} — {i18n.tr_text(p['family'])}" for p in sc)
    return tr("chat.help")
