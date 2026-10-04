"""Góngora, el perfumista de Perfúmappte: asistente con IA (Google Gemini, capa gratuita) que conoce tu colección y puede consultar la base de datos.

La clave de la API de Gemini (Google AI Studio) se toma, por este orden, de GEMINI_API_KEY / GOOGLE_API_KEY, de la que se guarde desde el ⚙ del chat (tabla `meta`)
o del archivo gemini.key que escribe el instalador en la carpeta de datos del usuario.
El módulo no depende de Qt: `Gongora.reply()` devuelve el texto por trozos mediante callbacks, para poder ejecutarlo en un hilo.
Habla con la API REST de Gemini (`streamGenerateContent` con SSE) usando solo la biblioteca estándar.
"""
import os, json, re, time
import urllib.request, urllib.error
from core import db, i18n, recommender as rec
from core.i18n import norm
from core.paths import app_dir
from core.recommender import split_notes

# La capa gratuita tiene una cuota diaria PEQUEÑA por modelo (p. ej. 20 peticiones/día en gemini-3.8-flash); cada modelo tiene la suya.
# Se prueban en orden y, si uno agota la cuota (429) o ya no existe (404), se salta al siguiente.
MODELS = ["gemini-flash-latest", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
COOLDOWN = 30 * 60                  # segundos que se descarta un modelo tras agotar su cuota
BASE = "https://generativelanguage.googleapis.com/v1beta"
KEY_META = "gemini_api_key"
MAX_STEPS = 6                       # vueltas máximas del bucle de herramientas por pregunta


class NoKey(Exception): pass                       # falta la clave o no es válida
class RateLimited(Exception): pass                 # cuota de la capa gratuita agotada (429)
class NetError(Exception): pass                    # sin conexión
class ApiError(Exception): pass                    # cualquier otro error de la API
class ModelGone(Exception): pass                   # el modelo ya no existe para esta cuenta


# ------------------------------------------------------------------ credenciales
def _key_file(): return os.path.join(app_dir(), "gemini.key")

def stored_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or db.get_meta(KEY_META)
    if not key:
        try:
            with open(_key_file(), encoding="utf-8-sig") as f: key = f.read().strip()
        except OSError: key = ""
    return key or ""

def save_key(key):
    """Guarda la clave (o la borra si va vacía) tanto en la base de datos como, si existía, en gemini.key."""
    db.set_meta(KEY_META, (key or "").strip())
    if not (key or "").strip():
        try: os.remove(_key_file())
        except OSError: pass


# ------------------------------------------------------------------ contexto: tu colección
def _top(txt, n=6): return ", ".join(split_notes(txt)[:n])

def _seasons(p):
    v = {k: float(p.get(c) or 0) for k, c in rec.SEASON_COLS}
    m = max(v.values())
    if m > 0: return ", ".join(k for k, x in v.items() if x >= 0.6 * m)
    return p.get("season") or ""

def _daynight(p):
    d, n = float(p.get("day") or 0), float(p.get("night") or 0)
    if d + n <= 0: return ""
    return "día" if d > 1.4 * n else "noche" if n > 1.4 * d else "día y noche"

def _accords(p, n=4):
    w = rec.parse_weights(p.get("accord_weights"))
    if w: return ", ".join(k for k, _ in sorted(w.items(), key=lambda x: -x[1])[:n])
    return ", ".join([x.strip() for x in re.split(r"[,|]", p.get("accords") or "") if x.strip()][:n])

def describe(p, compact=False):
    """Una línea con lo que importa de un perfume para aconsejar."""
    head = f"{p['name']} ({p.get('brand') or '?'}{', ' + str(p['year']) if p.get('year') else ''})"
    bits = [p.get("gender") or "", f"familia {p.get('family') or '?'}"]
    if not compact:
        notes = "; ".join(x for x in (_top(p.get("top_notes")), _top(p.get("heart_notes")), _top(p.get("base_notes")), _top(p.get("flat_notes"))) if x)
        if notes: bits.append("notas: " + notes)
        if _accords(p): bits.append("acordes: " + _accords(p))
    if p.get("occasion"): bits.append("ocasiones: " + p["occasion"])
    s = _seasons(p)
    if s: bits.append("estaciones: " + s)
    if _daynight(p): bits.append("se lleva de " + _daynight(p))
    if p.get("longevity") or p.get("sillage"): bits.append(f"duración {p.get('longevity') or '?'}, estela {p.get('sillage') or '?'}")
    if p.get("rating_avg"): bits.append(f"valoración {p['rating_avg']:.1f}")
    return "- " + head + " · " + " · ".join(b for b in bits if b)

def system_prompt():
    owned = [db.get(r["id"]) for r in db.collection_rows("owned")]
    wish = [r for r in db.collection_rows("wishlist")]
    compact = len(owned) > 40
    col = "\n".join(describe(p, compact) for p in owned[:120]) or "(la colección está vacía)"
    return f"""Eres Góngora, el perfumista de la aplicación Perfúmappte. Aconsejas con criterio y cariño, como un perfumista de confianza: elegante, cercano y directo, sin florituras.

Cómo trabajas:
- Responde en el mismo idioma en que te escriben (el idioma de la app ahora es {'español' if i18n.is_es() else 'inglés'}).
- Para preguntas de «qué me pongo» (evento, outfit, plan, clima, hora) elige primero de la COLECCIÓN de la persona. Da una recomendación principal clara y, si procede, una alternativa, explicando en una frase por qué encaja (notas, familia, estación, momento del día, formalidad, estela). Ten en cuenta la ropa y el contexto que cuenten (p. ej. un vestido de noche pide algo con presencia y elegancia; calor pide frescura).
- Si piden combinar perfumes, indica cuál va de base (el más pesado) y cuál encima (el más ligero), con el número de atomizaciones de cada uno. Puedes usar la herramienta layering_for.
- Si nada de su colección encaja bien, dilo con honestidad y sugiere qué comprar usando search_database o similar_to; marca siempre qué perfumes NO tiene.
- No inventes perfumes, notas ni datos: usa solo la colección de abajo y lo que devuelvan las herramientas. Si no sabes algo, dilo.
- Sé breve: normalmente 3-6 frases. Usa **negrita** para los nombres de perfume. Solo pide una aclaración si es imprescindible; si falta algo menor, asume lo razonable y dilo.
- Cuando recomiendes una combinación concreta de dos perfumes, llama a suggest_layering (base = el más pesado, top = el más ligero); cuando recomiendes un perfume que la persona NO tiene (para probarlo o comprarlo), llama a suggest_perfume. Así podrá guardarlos con un toque en sus combinaciones favoritas o en su lista de deseados. Llama a estas herramientas siempre que hagas ese tipo de recomendación, además de escribir tu respuesta completa en texto (las herramientas no sustituyen a la respuesta). No menciones las herramientas ni repitas la respuesta tras usarlas.
- Lenguaje neutro en cuanto al género: no asumas el género de la persona (nada de «guapa», «querido», «directa»…) y evita formas marcadas al hablar de ti (di «me encanta ayudarte», nunca «encantado» o «encantada»). Usa «perfumista» para referirte a ti.
- Habla solo de perfumería y de lo que se relacione con ella; si te preguntan otra cosa, redirige con amabilidad.

Contexto de hoy: estación {rec.current_season()}.

COLECCIÓN EN PROPIEDAD ({len(owned)}):
{col}

LISTA DE DESEADOS: {', '.join(r['name'] for r in wish[:30]) or '(vacía)'}"""


# ------------------------------------------------------------------ herramientas
TOOLS = [
    {"name": "search_database", "description": "Busca perfumes en la base de datos general (138.000+), ordenados por popularidad y valoración. Útil para sugerir compras. "
     "Devuelve solo perfumes populares (más de 1.000 votos) e indica si ya están en la colección.",
     "input_schema": {"type": "object", "properties": {
         "text": {"type": "string", "description": "Nombre o marca (opcional)."},
         "families": {"type": "array", "items": {"type": "string"}, "description": "Familias olfativas en español: Cítrica, Floral, Amaderada, Oriental, Aromática, Gourmand, Fougère, Acuática, Chipre, Cuero, Especiada, Frutal."},
         "notes": {"type": "array", "items": {"type": "string"}, "description": "Notas que debe llevar (cada una exacta, p. ej. 'vainilla')."},
         "gender": {"type": "array", "items": {"type": "string", "enum": ["male", "female", "unisex"]}},
         "limit": {"type": "integer", "description": "Máximo de resultados (1-10, por defecto 6)."}}}},
    {"name": "layering_for", "description": "Combinaciones de layering de un perfume de la colección con el resto de la colección: quién va de base, quién encima, atomizaciones y por qué encajan.",
     "input_schema": {"type": "object", "properties": {"perfume": {"type": "string", "description": "Nombre del perfume de la colección."}}, "required": ["perfume"]}},
    {"name": "similar_to", "description": "Perfumes de la base de datos que NO están en la colección y se parecen a uno dado (notas y perfil olfativo).",
     "input_schema": {"type": "object", "properties": {"perfume": {"type": "string", "description": "Nombre del perfume de referencia."}}, "required": ["perfume"]}},
    {"name": "suggest_layering", "description": "Registra una combinación de layering recomendada para que la persona pueda guardarla en sus favoritas. Llámala cuando recomiendes una combinación concreta.",
     "input_schema": {"type": "object", "properties": {"base": {"type": "string", "description": "Perfume más pesado (va de base)."},
                                                         "top": {"type": "string", "description": "Perfume más ligero (va encima)."}}, "required": ["base", "top"]}},
    {"name": "suggest_perfume", "description": "Registra un perfume que NO está en la colección y que recomiendas, para que la persona pueda añadirlo a su lista de deseados.",
     "input_schema": {"type": "object", "properties": {"perfume": {"type": "string", "description": "Nombre del perfume (con la marca si ayuda a identificarlo)."}}, "required": ["perfume"]}},
]

def _brief(p):
    return {"name": p["name"], "brand": p.get("brand"), "gender": p.get("gender"), "family": p.get("family"),
            "notes": "; ".join(x for x in (_top(p.get("top_notes"), 4), _top(p.get("heart_notes"), 4), _top(p.get("base_notes"), 4)) if x),
            "rating": round(p["rating_avg"], 1) if p.get("rating_avg") else None, "votes": p.get("vote_count"),
            "in_collection": p.get("status") in ("owned", "wishlist") and p.get("status")}

def _owned_full(): return [rec.fill_axes(db.get(r["id"])) for r in db.collection_rows("owned")]

def _find(name, rows):
    n = norm(name or "")
    if not n: return None
    exact = [p for p in rows if norm(p["name"]) == n]
    if exact: return exact[0]
    part = [p for p in rows if n in norm(p["name"]) or norm(p["name"]) in n]
    return min(part, key=lambda p: len(p["name"])) if part else None

def _resolve(name, owned):
    """Busca un perfume por nombre: primero en la colección y, si no está, en toda la base de datos."""
    p = _find(name, owned)
    if p: return p
    n = norm(name or "")
    rows = db.search(name or "", "", "", None, 8, sort="pop_rating")
    if not rows: return None
    exact = [r for r in rows if norm(r["name"]) == n]
    return db.get((exact or rows)[0]["id"])

def _ref(p): return {"id": p["id"], "name": p["name"], "brand": p.get("brand")}

def run_tool(name, args):
    """Ejecuta una herramienta y devuelve un objeto serializable en JSON."""
    try:
        if name == "search_database":
            limit = max(1, min(10, int(args.get("limit") or 6)))
            rows = db.search(args.get("text") or "", list(args.get("families") or []), list(args.get("notes") or []), None, 200,
                             note_exact=True, sort="pop_rating", gender=list(args.get("gender") or []) or None)
            rows = [r for r in rows if r.get("status") != "owned" and (r.get("vote_count") or 0) >= db.MIN_VOTES][:limit]
            return {"results": [_brief(r) for r in rows]} if rows else {"results": [], "note": "Sin resultados con esos criterios."}
        owned = _owned_full()
        if name == "suggest_layering":
            a, b = _resolve(args.get("base"), owned), _resolve(args.get("top"), owned)
            if not a or not b: return {"error": "No encuentro alguno de los dos perfumes; revisa los nombres."}
            if a["id"] == b["id"]: return {"error": "Los dos perfumes son el mismo."}
            return {"ok": True, "base": _ref(a), "top": _ref(b)}
        if name == "suggest_perfume":
            p = _resolve(args.get("perfume"), owned)
            if not p: return {"error": "No encuentro ese perfume."}
            if p.get("status") == "owned": return {"error": "Ese perfume ya está en la colección."}
            return {"ok": True, "perfume": _ref(p)}
        if name == "layering_for":
            p = _find(args.get("perfume"), owned)
            if not p: return {"error": "Ese perfume no está en la colección."}
            out = []
            for _s, base, top, why in rec.layering_with(p, owned, 5):
                out.append({"base": base["name"], "top": top["name"], "base_sprays": rec.spray_count(base), "top_sprays": rec.spray_count(top), "why": why})
            return {"combinations": out} if out else {"combinations": [], "note": "No hay combinaciones claras."}
        if name == "similar_to":
            pool = db.search(args.get("perfume") or "", "", "", None, 5, sort="pop_rating")
            ref = _find(args.get("perfume"), owned) or (db.get(pool[0]["id"]) if pool else None)
            if not ref: return {"error": "No encuentro ese perfume."}
            ref = rec.fill_axes(ref)
            cands = [rec.fill_axes(c) for c in db.candidates(3000)]
            return {"reference": ref["name"], "results": [dict(_brief(c), similarity=round(s, 2)) for s, c in rec.similar_to(ref, cands, 5)]}
    except Exception as e:                                   # una herramienta rota no debe tumbar la conversación
        return {"error": f"{type(e).__name__}: {e}"}
    return {"error": f"Herramienta desconocida: {name}"}


FUNCTION_DECLARATIONS = [{"name": x["name"], "description": x["description"], "parameters": x["input_schema"]} for x in TOOLS]


# ------------------------------------------------------------------ la conversación
_bad = {}                           # modelo -> instante hasta el que se descarta (cuota agotada o inexistente)

def _stream(key, body, model):
    """Genera los objetos JSON de cada evento SSE de `streamGenerateContent`. Reintenta ante 500/503."""
    url = f"{BASE}/models/{model}:streamGenerateContent?alt=sse"
    data = json.dumps(body).encode()
    for attempt in (0, 1, 2):
        req = urllib.request.Request(url, data=data, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if line.startswith("data:"):
                        try: yield json.loads(line[5:])
                        except ValueError: continue
            return
        except urllib.error.HTTPError as e:
            msg = ""
            try: msg = json.loads(e.read().decode("utf-8", "replace")).get("error", {}).get("message", "")
            except Exception: pass
            if e.code in (401, 403) or (e.code == 400 and "API key" in msg): raise NoKey()
            if e.code == 429: raise RateLimited()
            if e.code == 404: raise ModelGone()
            if e.code in (500, 503) and attempt < 2: time.sleep(1.5 * (attempt + 1)); continue
            raise ApiError(msg or f"HTTP {e.code}")
        except urllib.error.URLError as e: raise NetError(str(e.reason))
        except (TimeoutError, ConnectionError, OSError) as e: raise NetError(str(e))


def stream_any(key, body):
    """Como `_stream`, pero recorre `MODELS` saltando los que tienen la cuota agotada. Lanza RateLimited si no queda ninguno."""
    for m in MODELS:
        if _bad.get(m, 0) > time.time(): continue
        try:
            yield from _stream(key, body, m); return
        except RateLimited: _bad[m] = time.time() + COOLDOWN
        except ModelGone: _bad[m] = time.time() + 24 * 3600
    raise RateLimited()


class Gongora:
    def __init__(self): self.history = []          # [{"role": "user"|"model", "parts": [{"text": str}]}]

    def reset(self): self.history = []

    def reply(self, user_text, on_text=lambda t: None, on_tool=lambda n: None, on_suggest=lambda s: None):
        """Contesta a `user_text` (con streaming y herramientas). Devuelve el texto completo.
        Lanza NoKey, RateLimited, NetError o ApiError."""
        key = stored_key()
        if not key: raise NoKey()
        contents = self.history + [{"role": "user", "parts": [{"text": user_text}]}]
        system = system_prompt(); said = []; seen = set()
        for _ in range(MAX_STEPS):
            body = {"system_instruction": {"parts": [{"text": system}]}, "contents": contents, "tools": [{"function_declarations": FUNCTION_DECLARATIONS}],
                    "generationConfig": {"maxOutputTokens": 2048, "thinkingConfig": {"thinkingLevel": "low"}}}
            parts, blocked = [], False
            for ev in stream_any(key, body):
                if ev.get("promptFeedback", {}).get("blockReason"): blocked = True
                for cand in ev.get("candidates") or []:
                    if cand.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST"): blocked = True
                    for p in (cand.get("content") or {}).get("parts") or []:
                        parts.append(p)
                        if p.get("text") and not p.get("thought"): said.append(p["text"]); on_text(p["text"])
            if blocked and not said:
                msg = i18n.tr("gongora.refusal"); said.append(msg); on_text(msg); break
            calls = [p for p in parts if "functionCall" in p]
            if not calls: break
            contents.append({"role": "model", "parts": parts})                    # se devuelven tal cual (con sus firmas de razonamiento)
            answers = []
            for p in calls:
                fc = p["functionCall"]; on_tool(fc["name"])
                out = run_tool(fc["name"], fc.get("args") or {})
                if out.get("ok"):                                                       # recomendación guardable: la interfaz la muestra como tarjeta
                    sig = (fc["name"], out.get("base", {}).get("id"), out.get("top", {}).get("id"), out.get("perfume", {}).get("id"))
                    if sig not in seen: seen.add(sig); on_suggest(dict(out, type="layering" if fc["name"] == "suggest_layering" else "perfume"))
                resp = {"name": fc["name"], "response": out}
                if fc.get("id"): resp["id"] = fc["id"]
                answers.append({"functionResponse": resp})
            contents.append({"role": "user", "parts": answers})
            if said and not said[-1].endswith("\n"): said.append("\n\n"); on_text("\n\n")
        text = "".join(said).strip()
        self.history += [{"role": "user", "parts": [{"text": user_text}]}, {"role": "model", "parts": [{"text": text or "…"}]}]
        self.history = self.history[-20:]                        # los últimos 10 intercambios bastan
        return text
