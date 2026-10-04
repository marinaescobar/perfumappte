import sqlite3, csv, os, sys, re, json
from collections import Counter
from core import i18n
from core.paths import app_dir
from core.i18n import norm
from core.recommender import split_notes, estimate_profile, FAMILIES

DB_PATH = os.path.join(app_dir(), "perfumappte.db")

# ---- columnas -------------------------------------------------------------
BASE_COLS = ["name", "brand", "year", "concentration", "family", "top_notes", "heart_notes", "base_notes",
             "longevity", "sillage", "occasion", "season", "description"]
CORE = BASE_COLS + ["sweet_fresh", "floral_woody", "light_intense"]          
NORM_X = ["sn", "fam_n", "notes_n"]      
TEXT_X = ["slug", "line", "gender", "url", "accords", "flat_notes", "note_weights", "perfumers", "last_comment_at", "scraped_at", "image_url",
          "accord_weights"]   # "acorde:0.87|acorde:0.5" (0..1); columna nueva, init_db la añade sola a las bases existentes
INT_X = (["ext_id", "vote_count"] + [f"rating_b{i}" for i in range(1, 6)] + [f"longevity_b{i}" for i in range(1, 6)]
         + [f"sillage_b{i}" for i in range(1, 5)] + [f"price_value_b{i}" for i in range(1, 6)]
         + ["have", "had", "want", "perceived_female", "perceived_female_leaning", "perceived_unisex", "perceived_male_leaning",
            "perceived_male", "winter", "spring", "summer", "autumn", "day", "night", "people"])
REAL_X = ["rating_avg", "longevity_avg", "sillage_avg", "price_value_avg", "magnitude", "compound_magnitude", "recent_magnitude", "score"]
PRIOR_N, PRIOR_R = 100, 3.7      

def _score(r, v):
    return None if not r or not v else round((v * r + PRIOR_N * PRIOR_R) / (v + PRIOR_N), 4)
ALL_COLS = CORE + NORM_X + TEXT_X + INT_X + REAL_X
LIGHT = ("p.id,p.ext_id,p.image_url,p.name,p.brand,p.year,p.concentration,p.family,p.top_notes,p.heart_notes,p.base_notes,p.flat_notes,p.longevity,p.sillage,"
         "p.occasion,p.season,p.gender,p.rating_avg,p.vote_count,p.sweet_fresh,p.floral_woody,p.light_intense,c.status,c.tags")

def _ddl(name):
    cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT", "name TEXT NOT NULL", "brand TEXT", "year INTEGER", "concentration TEXT", "family TEXT",
            "top_notes TEXT", "heart_notes TEXT", "base_notes TEXT", "longevity TEXT", "sillage TEXT", "occasion TEXT", "season TEXT",
            "description TEXT", "sweet_fresh INTEGER DEFAULT 50", "floral_woody INTEGER DEFAULT 50", "light_intense INTEGER DEFAULT 50"]
    cols += [f"{k} TEXT" for k in NORM_X + TEXT_X] + [f"{k} INTEGER" for k in INT_X] + [f"{k} REAL" for k in REAL_X]
    return f"CREATE TABLE {name}({','.join(cols)})"

def conn():
    c = sqlite3.connect(DB_PATH, timeout=30); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); c.create_function("norm", 1, norm)
    return c

def _norms(d):
    notes = [norm(n) for k in ("top_notes", "heart_notes", "base_notes", "flat_notes") for n in split_notes(d.get(k))]
    return (norm(f"{d.get('name') or ''} {d.get('brand') or ''}"), norm(d.get("family")), "|" + "|".join(dict.fromkeys(notes)) + "|")

def _backfill(progress=None):
    done = 0
    while True:
        with conn() as c:
            rows = c.execute("SELECT id,name,brand,family,top_notes,heart_notes,base_notes,flat_notes FROM perfumes WHERE sn IS NULL LIMIT 5000").fetchall()
            if not rows: break
            c.executemany("UPDATE perfumes SET sn=?,fam_n=?,notes_n=? WHERE id=?", [(*_norms(dict(r)), r["id"]) for r in rows])
        done += len(rows)
        if progress: progress(done)

def rebuild_note_stats():
    cnt, lab, memo = Counter(), {}, {}
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS note_stats(note TEXT PRIMARY KEY, label TEXT, n INTEGER)")
        for r in c.execute("SELECT top_notes,heart_notes,base_notes,flat_notes FROM perfumes"):
            seen = set()
            for col in r:
                for raw in re.split(r"[,;]", col or ""):
                    raw = raw.strip()
                    if not raw: continue
                    k = memo.get(raw) or memo.setdefault(raw, norm(raw))
                    if k not in seen: seen.add(k); cnt[k] += 1; lab.setdefault(k, raw)
        c.execute("DELETE FROM note_stats")
        c.executemany("INSERT INTO note_stats VALUES(?,?,?)", [(k, lab[k], n) for k, n in cnt.items()])

def note_chips(q="", limit=72):
    vs = i18n.en_variants(norm(q)) or [""]
    with conn() as c:
        rows = c.execute("SELECT label,note,n FROM note_stats WHERE (" + " OR ".join("note LIKE ?" for _ in vs) +
                         ") ORDER BY n DESC LIMIT ?", [f"%{v}%" for v in vs] + [limit]).fetchall()
    return [(r["label"], r["note"], r["n"]) for r in rows]

def get_meta(k, default=None):
    with conn() as c:
        r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r[0] if r else default

def set_meta(k, v):
    with conn() as c: c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, str(v)))

def _open_raw():
    """Abre la base; si un cierre brusco dejó -wal/-shm huérfanos («disk I/O error») y no hay ningún proceso usándolos, los retira y reintenta."""
    for attempt in (0, 1):
        raw = sqlite3.connect(DB_PATH, timeout=30)
        try: raw.execute("PRAGMA table_info(perfumes)").fetchall(); return raw
        except sqlite3.OperationalError:
            raw.close()
            if attempt: raise
            for ext in ("-wal", "-shm"):
                f = DB_PATH + ext
                try:
                    if os.path.exists(f) and (ext == "-shm" or os.path.getsize(f) == 0): os.remove(f)
                except OSError: pass

def init_db(progress=None):
    raw = _open_raw(); raw.execute("PRAGMA foreign_keys=OFF")
    have = [r[1] for r in raw.execute("PRAGMA table_info(perfumes)")]
    if not have: raw.execute(_ddl("perfumes"))
    elif "slug" not in have:          
        raw.execute(_ddl("perfumes_new")); k = ",".join(CORE)
        raw.execute(f"INSERT INTO perfumes_new(id,{k}) SELECT id,{k} FROM perfumes")
        raw.execute("DROP TABLE perfumes"); raw.execute("ALTER TABLE perfumes_new RENAME TO perfumes")
    else:                             
        for k in ALL_COLS:
            if k not in have: raw.execute(f"ALTER TABLE perfumes ADD COLUMN {k} {'INTEGER' if k in INT_X else 'REAL' if k in REAL_X else 'TEXT'}")
    
    raw.executescript("""CREATE UNIQUE INDEX IF NOT EXISTS ux_slug ON perfumes(slug);
      DROP INDEX IF EXISTS ix_votes;
      CREATE INDEX IF NOT EXISTS ix_pop ON perfumes(vote_count DESC, rating_avg DESC, name);
      CREATE INDEX IF NOT EXISTS ix_brand_name ON perfumes(brand,name);
      CREATE INDEX IF NOT EXISTS ix_score ON perfumes(score);
      CREATE TABLE IF NOT EXISTS collection(perfume_id INTEGER PRIMARY KEY REFERENCES perfumes(id) ON DELETE CASCADE,
      status TEXT DEFAULT 'owned', tags TEXT DEFAULT '', notes TEXT DEFAULT '');
      CREATE TABLE IF NOT EXISTS note_stats(note TEXT PRIMARY KEY, label TEXT, n INTEGER);
      CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
      CREATE TABLE IF NOT EXISTS fav_combos(a INTEGER NOT NULL REFERENCES perfumes(id) ON DELETE CASCADE,
      b INTEGER NOT NULL REFERENCES perfumes(id) ON DELETE CASCADE, PRIMARY KEY(a,b));""")
      
    raw.execute(f"UPDATE perfumes SET score=(vote_count*rating_avg+{PRIOR_N}*{PRIOR_R})/(vote_count+{PRIOR_N}.0) "
                "WHERE score IS NULL AND rating_avg IS NOT NULL AND vote_count>0")
                
    raw.commit(); raw.execute("PRAGMA journal_mode=WAL"); raw.close()
    _backfill(progress)
    with conn() as c: need = c.execute("SELECT COUNT(*) FROM note_stats").fetchone()[0] == 0
    if need: rebuild_note_stats()

# ---- caché del conjunto popular ----------------------------------------------------
_pool, _cands = None, {}
def _invalidate():
    global _pool; _pool = None; _cands.clear()

def warm():
    """Precarga el conjunto popular («parecido a» y chat) y los candidatos de compra, sin bloquear la interfaz: se llama desde un hilo."""
    all_rows()
    candidates(4000, {r["gender"] for r in collection_rows("owned") if r.get("gender")})

def update_profile(pid, field, v):
    assert field in ("sweet_fresh", "floral_woody", "light_intense")
    with conn() as c: c.execute(f"UPDATE perfumes SET {field}=? WHERE id=?", (v, pid))

def get(pid):
    with conn() as c:
        r = c.execute("SELECT p.*,c.status,c.tags FROM perfumes p LEFT JOIN collection c ON c.perfume_id=p.id WHERE p.id=?", (pid,)).fetchone()
        return dict(r) if r else None

def search(q="", family="", note="", status=None, limit=500, note_exact=False, sort=None, gender=None):
    sql = f"SELECT {LIGHT} FROM perfumes p LEFT JOIN collection c ON c.perfume_id=p.id WHERE 1=1"; a = []
    if gender: sql += " AND p.gender IN (" + ",".join("?" * len(gender)) + ")"; a += list(gender)
    if status in ("owned", "wishlist"): sql += " AND c.status=?"; a.append(status)
    elif status == "any": sql += " AND c.perfume_id IS NOT NULL"
    elif status == "none": sql += " AND c.perfume_id IS NULL"
    for w in norm(q).split():
        vs = i18n.en_variants(w)
        sql += " AND (" + " OR ".join("(p.sn LIKE ? OR (c.tags IS NOT NULL AND norm(c.tags) LIKE ?))" for _ in vs) + ")"
        a += [x for v in vs for x in (f"%{v}%", f"%{v}%")]
    fams = [family] if isinstance(family, str) and family else list(family or [])
    if fams:
        toks = [t for f in fams for t in FAMILIES.get(f, [norm(f)])]
        sql += " AND (" + " OR ".join("p.fam_n LIKE ?" for _ in toks) + ")"; a += [f"%{t}%" for t in toks]
    for n in ([note] if isinstance(note, str) and note else list(note or [])):
        vs = i18n.en_variants(norm(n))
        sql += " AND (" + " OR ".join("p.notes_n LIKE ?" for _ in vs) + ")"
        a += [f"%|{v}|%" if note_exact else f"%{v}%" for v in vs]
    order = {"pop_rating": "p.vote_count DESC,p.rating_avg DESC,p.name",      # más votados primero y, a igualdad, mejor valorados (usa el índice ix_pop)
             "votes": "p.vote_count DESC,p.name"}.get(sort, "p.brand,p.name")
    sql += f" ORDER BY {order} LIMIT ?"; a.append(limit)
    with conn() as c: return [dict(r) for r in c.execute(sql, a)]

MIN_VOTES = 1000          # popularidad mínima para sugerir una compra
NOVELTY_BRANDS = ("sponge", "disney", "hello kitty", "marvel", "barbie", "pokemon", "paw patrol", "peppa", "frozen", "star wars",
                  "dora", "minnie", "mickey", "looney", "nickelodeon", "cartoon", "lol surprise", "air-val", "naruto", "minion")

def candidates(limit=4000, genders=None):
    """Perfumes de la base que NO están en propiedad (los deseados sí valen), los mejor valorados primero, con todas sus columnas."""
    genders = sorted(genders or ()); cache_key = (limit, tuple(genders))
    if cache_key in _cands: return [dict(r) for r in _cands[cache_key]]
    sql = ("SELECT p.*, c.status AS status, c.tags AS tags FROM perfumes p LEFT JOIN collection c ON c.perfume_id=p.id "
           "WHERE (c.status IS NULL OR c.status!='owned') AND p.score IS NOT NULL AND p.vote_count>=?"); a = [MIN_VOTES]
    for b in NOVELTY_BRANDS: sql += " AND IFNULL(p.brand,'') NOT LIKE ?"; a.append(f"%{b}%")
    if genders: sql += " AND p.gender IN (" + ",".join("?" * len(genders)) + ")"; a += list(genders)
    sql += " ORDER BY p.score DESC LIMIT ?"; a.append(limit)
    with conn() as c: rows = [dict(r) for r in c.execute(sql, a)]
    _cands[cache_key] = rows
    return [dict(r) for r in rows]

# ---- combinaciones favoritas (pareja sin orden: se guarda con el id menor primero) -------------
def _pair(a, b): return (a, b) if a <= b else (b, a)
def fav_has(a, b):
    with conn() as c: return c.execute("SELECT 1 FROM fav_combos WHERE a=? AND b=?", _pair(a, b)).fetchone() is not None
def fav_set(a, b, on):
    with conn() as c:
        if on: c.execute("INSERT OR IGNORE INTO fav_combos(a,b) VALUES(?,?)", _pair(a, b))
        else: c.execute("DELETE FROM fav_combos WHERE a=? AND b=?", _pair(a, b))
def fav_list():
    with conn() as c: return [(r["a"], r["b"]) for r in c.execute("SELECT a,b FROM fav_combos ORDER BY rowid DESC")]

def collection_rows(status="owned"): return search(status=status, limit=100000)
def all_rows(limit=10000):
    global _pool
    if _pool is None: _pool = search(limit=limit, sort="votes")
    return _pool
def count():
    with conn() as c: return c.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]

def set_collection(pid, status="owned", tags=None):
    _cands.clear()                                  # los candidatos de compra dependen de lo que tengas en propiedad
    with conn() as c:
        old = c.execute("SELECT tags FROM collection WHERE perfume_id=?", (pid,)).fetchone()
        t = tags if tags is not None else (old["tags"] if old else "")
        c.execute("INSERT OR REPLACE INTO collection(perfume_id,status,tags) VALUES(?,?,?)", (pid, status, t))

def remove_from_collection(pid):
    _cands.clear()
    with conn() as c: c.execute("DELETE FROM collection WHERE perfume_id=?", (pid,))

# ---- importación JSON Fragrantica -------------------------------------------
def _f(x):
    try: return float(x) if x not in (None, "") else None
    except ValueError: return None
def _i(x):
    v = _f(x); return None if v is None else int(v)

def _extract_names(val):
    if not val: return ""
    if isinstance(val, str): return val
    if isinstance(val, list):
        res = []
        for x in val:
            if isinstance(x, dict):
                nm = x.get("name") or x.get("label") or x.get("note") or ""
                w = x.get("weight") or x.get("strength") or x.get("value")
                if nm:
                    res.append(f"{nm}:{w}" if w is not None else str(nm))
            elif isinstance(x, str):
                res.append(x)
        return "|".join(res)
    return str(val)

def _notes(s):
    names, w = [], {}
    if not s: return names, w
    for part in str(s).split("|"):
        part = part.strip()
        if not part: continue
        n, sep, v = part.rpartition(":")
        if not sep or _f(v) is None: n, v = part, None
        names.append(n.strip().title())
        if v is not None: w[n.strip().lower()] = round(_f(v) / 100, 2)
    return names, w

CONC = [(r"eau de parfum|\bedp\b", "EDP"), (r"eau de toilette|\bedt\b", "EDT"), (r"eau de cologne|\bcologne\b|\bedc\b", "EDC"),
        (r"extrait", "Extrait"), (r"\bparfum\b|\bperfume\b", "Parfum")]
def infer_conc(name):
    n = norm(name)
    return next((lab for rx, lab in CONC if re.search(rx, n)), "")

def _lon(v): return None if v is None else "Corta" if v < 2.5 else "Moderada" if v < 3.5 else "Larga" if v < 4.2 else "Eterna"
def _sil(v): return None if v is None else "Suave" if v < 1.75 else "Moderada" if v < 2.5 else "Fuerte" if v < 3.25 else "Enorme"

def _season(d):
    v = {"invierno": d.get("winter"), "primavera": d.get("spring"), "verano": d.get("summer"), "otoño": d.get("autumn")}
    m = max((x or 0) for x in v.values())
    return ",".join(k for k, x in v.items() if m and (x or 0) >= 0.6 * m)

def _occasion(d):
    dy, nt = d.get("day") or 0, d.get("night") or 0; m = max(dy, nt); out = []
    if m and dy >= .6 * m: out += ["casual", "oficina", "deporte"]
    if m and nt >= .6 * m: out += ["noche", "cita"]
    return ",".join(out)

def _row_to_d(r):
    pick = lambda *ks: next((r[k] for k in ks if r.get(k) not in (None, "")), None)
    d = {k: None for k in ALL_COLS}
    d["name"], d["brand"] = pick("name", "perfume", "nombre"), pick("brand", "marca", "designer")
    for k in ("name", "brand"):
        if d[k] and " " not in d[k] and "-" in d[k]: d[k] = d[k].replace("-", " ").title()
    d["year"] = _i(pick("year", "año", "ano")); d["ext_id"] = _i(r.get("id"))
    d["line"], d["gender"], d["url"] = pick("collection"), pick("gender"), pick("url")
    d["image_url"] = pick("image_url", "picture", "thumbnail")
    for k in TEXT_X[7:] + ["description"]: d[k] = r.get(k) or None
    for k in INT_X[1:]: d[k] = _i(r.get(k))
    for k in REAL_X: d[k] = _f(r.get(k))

    d["vote_count"] = _i(pick("people", "vote_count", "votes"))
    d["rating_avg"] = _f(pick("rating_avg"))
    d["score"] = _score(d["rating_avg"], d["vote_count"])

    # Accords
    acc_raw = pick("accords", "main_accords")
    names, acc_w = _notes(str(acc_raw) if acc_raw else "")
    d["accords"] = ", ".join(names) if names else (str(acc_raw) if isinstance(acc_raw, str) else None)
    d["accord_weights"] = "|".join(f"{k}:{v}" for k, v in acc_w.items()) or None

    # Perfumers
    perf_raw = pick("perfumers", "nose")
    names, _ = _notes(str(perf_raw) if perf_raw else "")
    d["perfumers"] = ", ".join(names) if names else (str(perf_raw) if isinstance(perf_raw, str) else None)

    # Family
    acc_list = [a.strip().title() for a in (d["accords"] or "").split(",") if a.strip()][:3]
    d["family"] = ", ".join(acc_list) or pick("family", "familia") or None

    # Notes
    w = {}
    for col, srcs in (("top_notes", ("notes_top", "top", "top_notes", "salida")),
                      ("heart_notes", ("notes_middle", "middle", "heart", "heart_notes", "corazon")),
                      ("base_notes", ("notes_base", "base", "base_notes", "fondo")),
                      ("flat_notes", ("notes_flat", "flat"))):
        val = pick(*srcs)
        names, ww = _notes(str(val) if val else "")
        d[col] = ", ".join(names) if names else None
        w.update(ww)

    d["note_weights"] = "|".join(f"{k}:{v}" for k, v in w.items()) or None
    d["longevity_avg"] = _f(r.get("longevity_avg"))
    d["longevity"] = _lon(d["longevity_avg"]) or pick("longevity", "duracion")
    d["sillage_avg"] = _f(r.get("sillage_avg"))
    d["sillage"] = _sil(d["sillage_avg"]) or pick("sillage", "estela")
    d["concentration"] = pick("concentration", "concentracion") or infer_conc(d["name"])

    d["season"] = _season(d) or pick("season", "estacion")
    d["occasion"] = _occasion(d) or pick("occasion", "ocasion")

    d["slug"] = pick("slug") or f"{d['brand'] or ''}/{d['name']}-{d['year'] or ''}".lower().replace(" ", "-")
    d["sweet_fresh"], d["floral_woody"], d["light_intense"] = estimate_profile(d)
    d["sn"], d["fam_n"], d["notes_n"] = _norms(d)
    return d

def _json_row(o):
    lo = {str(k).lower(): v for k, v in o.items()}
    r = {}
    for k in ("name", "brand", "year", "gender", "url", "description", "slug", "people"):
        if k in lo: r[k] = lo[k]
    
    r["vote_count"] = lo.get("people") or lo.get("vote_count")
    
    # Imagen
    for img_k in ("picture", "thumbnail", "image_url", "image", "images", "img", "photo"):
        if lo.get(img_k):
            v = lo[img_k]
            r["image_url"] = v[0] if isinstance(v, list) and v else str(v)
            break

    # Perfumistas
    perf = lo.get("perfumers") or lo.get("nose") or lo.get("noses")
    if isinstance(perf, list):
        r["perfumers"] = "|".join(x.get("name") for x in perf if isinstance(x, dict) and x.get("name"))
    elif isinstance(perf, str):
        r["perfumers"] = perf

    # Acordes
    acc = lo.get("accords") or lo.get("main_accords") or lo.get("mainaccords")
    if isinstance(acc, list):
        r["accords"] = "|".join(f"{x.get('name')}:{x.get('strength', '')}" if isinstance(x, dict) else str(x) for x in acc)
    elif isinstance(acc, str):
        r["accords"] = acc

    # Notas (tiered / flat)
    notes = lo.get("notes") or lo.get("pyramid")
    if isinstance(notes, dict):
        tiered = notes.get("tiered") if isinstance(notes.get("tiered"), dict) else notes
        if "top" in tiered: r["notes_top"] = _extract_names(tiered["top"])
        if "middle" in tiered or "heart" in tiered: r["notes_middle"] = _extract_names(tiered.get("middle") or tiered.get("heart"))
        if "base" in tiered: r["notes_base"] = _extract_names(tiered.get("base"))
        if "flat" in notes and notes["flat"]: r["notes_flat"] = _extract_names(notes["flat"])
    elif isinstance(notes, list):
        r["notes_flat"] = _extract_names(notes)

    # Valoraciones
    rat = lo.get("rating")
    if isinstance(rat, dict): r["rating_avg"] = rat.get("average")
    elif isinstance(rat, (int, float)): r["rating_avg"] = float(rat)

    long = lo.get("longevity")
    if isinstance(long, dict): r["longevity_avg"] = long.get("average")
    elif isinstance(long, (int, float)): r["longevity_avg"] = float(long)

    sil = lo.get("sillage")
    if isinstance(sil, dict): r["sillage_avg"] = sil.get("average")
    elif isinstance(sil, (int, float)): r["sillage_avg"] = float(sil)

    # Estaciones y momentos
    seasons = lo.get("seasons")
    if isinstance(seasons, dict):
        for k, v in seasons.items(): r[k] = v
    daypart = lo.get("daypart")
    if isinstance(daypart, dict):
        for k, v in daypart.items(): r[k] = v

    return r

def _iter_rows(path):
    csv.field_size_limit(2 ** 31 - 1)
    if os.path.splitext(path)[1].lower() in (".jsonl", ".json", ".ndjson"):
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            arr = f.read(1) == "["; f.seek(0)
            if arr:
                for o in json.load(f):
                    if isinstance(o, dict): yield _json_row(o)
            else:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try: o = json.loads(line)
                    except ValueError: continue
                    if isinstance(o, dict): yield _json_row(o)
    else:
        with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
            head = f.readline(); f.seek(0)
            for row in csv.DictReader(f, delimiter=max([",", ";", "\t"], key=head.count)):
                yield {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}

def import_file(path, progress=None):
    upd = ",".join(f"{k}=excluded.{k}" for k in ALL_COLS if k != "slug")
    sql = f"INSERT INTO perfumes({','.join(ALL_COLS)}) VALUES({','.join('?' * len(ALL_COLS))}) ON CONFLICT(slug) DO UPDATE SET {upd}"
    _invalidate(); total, batch = 0, []
    with conn() as c:
        c.execute("PRAGMA synchronous=OFF")
        before = c.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]
        for r in _iter_rows(path):
            if not (r.get("name") or r.get("perfume") or r.get("nombre")): continue
            d = _row_to_d(r); batch.append([d[k] for k in ALL_COLS]); total += 1
            if len(batch) >= 2000:
                c.executemany(sql, batch); c.commit(); batch = []      
                if progress: progress(total)
        if batch: c.executemany(sql, batch); c.commit()
        after = c.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]
    rebuild_note_stats(); _invalidate()
    return after - before, total - (after - before)

def inspect_file(path, n=1):
    for i, r in enumerate(_iter_rows(path)):
        if i >= n: break
        print(i18n.tr("db.keys"), sorted(r))
        d = _row_to_d(r) if (r.get("name") or r.get("perfume")) else {}
        print(i18n.tr("db.mapped"), {k: v for k, v in d.items() if v not in (None, "")})

if __name__ == "__main__":
    # python -m core.db [--lang en] [archivo.jsonl|.json|.csv]   importa a mano un archivo
    # python -m core.db --inspect archivo.jsonl                 muestra sus claves y cómo se leen
    if "--lang" in sys.argv: i18n.set_lang(sys.argv[sys.argv.index("--lang") + 1])
    files = [a for a in sys.argv[1:] if a.endswith((".jsonl", ".json", ".csv", ".txt", ".ndjson"))]
    if "--inspect" in sys.argv and files: inspect_file(files[0]); sys.exit()
    init_db(lambda n: print(i18n.tr("db.preparing", n)))
    if files: print(i18n.tr("db.res") % import_file(files[0], lambda n: print(f"{n:,}")))
    print(i18n.tr("db.total"), count())
