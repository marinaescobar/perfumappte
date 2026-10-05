"""Traducciones ES/EN de la interfaz y del contenido de la base de datos.

La base de datos guarda los valores canónicos tal como llegan de Fragrantica (inglés:
"citrus:100|fresh spicy:47", "Woody, Aromatic", notas en inglés…). Aquí se traducen al
mostrar, sin tocar los datos, de modo que la búsqueda, los filtros y las comparaciones
siguen funcionando igual en los dos idiomas: «vainilla» encuentra «Vanilla» y
«amaderada» encuentra «Woody».

    from core import i18n
    i18n.set_lang("en")          # cambia el idioma (las vistas ya creadas se re-traducen con retranslate())
    i18n.tr("nav.collection")      # "My collection"
    i18n.tr_note("White Musk")     # "Almizcle blanco"
    i18n.to_en("amaderada")        # "woody"
"""
import re, unicodedata
from functools import lru_cache

LANGS = ("es", "en")
DEFAULT = "es"
LANG = DEFAULT

# ------------------------------------------------------------------ utilidades
@lru_cache(maxsize=65536)
def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def norm(s):
    """Minúsculas sin acentos (mismo criterio que el buscador de la base de datos). Con caché: se llama cientos de miles de veces."""
    return _norm(s if isinstance(s, str) else str(s or ""))

def lang(): return LANG
def is_es(): return LANG == "es"

def set_lang(code):
    global LANG
    LANG = code if code in LANGS else DEFAULT

# ------------------------------------------------------------------ interfaz
# clave: (español, inglés)
UI = {
    # --- app ---
    "app.preparing": ("Preparando la base de datos…", "Preparing the database…"),
    "app.preparing.n": ("Preparando la base de datos… {0:,}", "Preparing the database… {0:,}"),

    # --- menú lateral ---
    "nav.collection": ("Mi colección", "My collection"),
    "nav.finder": ("Descubrimientos", "Discoveries"),
    "nav.recs": ("Recomendaciones", "Recommendations"),

    # --- navegador ---
    "browser.search.ph": ("🔍  Buscar por nombre, marca o etiqueta…", "🔍  Search by name, brand or tag…"),
    "browser.filter.all": ("Todos", "All"),
    "browser.filter.owned": ("En propiedad", "Owned"),
    "browser.filter.wishlist": ("Lista de deseos", "Wishlist"),
    "browser.filter.incol": ("En mi colección", "In my collection"),
    "browser.filter.none": ("Sin añadir", "Not added"),
    "browser.filter.clear": ("Limpiar filtros", "Clear filters"),
    "browser.filter.families": ("Familia olfativa", "Olfactive family"),
    "browser.filter.family.all": ("Todas las familias", "All families"),
    "browser.filter.notes": ("Notas", "Notes"),
    "browser.filter.notes.ph": ("🔍  Filtrar notas…", "🔍  Filter notes…"),
    "btn.remove": ("Quitar de colección", "Remove from collection"),
    "btn.toowned": ("Pasar a propiedad", "Mark as owned"),
    "btn.towishlist": ("Pasar a deseos", "Mark as wishlist"),
     "browser.gender": ("Género", "Gender"),
     "browser.more": ("Ver más…", "See more…"),
     "notes.all.title": ("Todas las notas", "All notes"),
     "tip.gender": ("Filtra por género. Puedes marcar varios.", "Filter by gender. You can pick several."),
     "tip.more": ("Ver el listado completo de notas.", "See the full list of notes."),
     "tip.card.owned": ("Añadir a mi colección (o quitarlo).", "Add to my collection (or remove it)."),
     "tip.card.wish": ("Añadir a deseados (o quitarlo).", "Add to wishlist (or remove it)."),
    "btn.update": ("Actualizar perfumes", "Update perfumes"),
    "ctx.add": ("＋ Añadir a colección", "＋ Add to collection"),
    "ctx.wish": ("♡ Lista de deseos", "♡ Wishlist"),
    "ctx.remove": ("Quitar de colección", "Remove from collection"),
    "ctx.profile": ("Ver perfil", "View profile"),
    "info.empty": ("La base de datos está vacía: pulsa «Actualizar perfumes» (Kaggle).",
                   "The database is empty: press “Update perfumes” (Kaggle)."),
    "info.found": ("{0} mostrados · {1:,} perfumes · ordenados por valoración y popularidad · familias: cualquiera · notas: todas",
                   "{0} shown · {1:,} perfumes · sorted by rating and popularity · families: any · notes: all"),
    "info.col": ("{0} mostrados · {1:,} perfumes en la base de datos", "{0} shown · {1:,} perfumes in the database"),
    "info.max": (" · máx. 500 (afina la búsqueda)", " · max. 500 (narrow your search)"),

    # --- importar ---

    # --- ficha de perfume ---
    "dlg.ok": ("Guardar", "Save"), "dlg.cancel": ("Cancelar", "Cancel"),
    "m.gender": ("Género", "Gender"),
    "m.perfumer": ("Perfumista", "Perfumer"),
    "m.notes": ("Intensidad de las notas", "Notes intensity"),
    "m.accords": ("Acordes", "Accords"),
    "m.top": ("Salida", "Top"),
    "m.heart": ("Corazón", "Heart"),
    "m.base": ("Fondo", "Base"),
    "m.votes": ("({0:,} valoraciones)", "({0:,} ratings)"),
    # --- perfil: iconos y ayudas ---
    "reco.h": ("Recomendado para:", "Recommended for:"),
    "sim.h": ("Parecido a:", "Similar to:"),
    "tip.sim.h": ("Perfumes con notas, familia y carácter parecidos.<br>Doble clic en uno para abrir su perfil.",
                  "Perfumes with similar notes, family and character.<br>Double-click one to open its profile."),
    "tip.sim": ("{0}<br>{1}% de parecido.<br>Clic para abrir su perfil.", "{0}<br>{1}% similar.<br>Click to open its profile."),
    "reco.l3": ("muy recomendado", "highly recommended"),
    "reco.l2": ("recomendado", "recommended"),
    "reco.l1": ("poco indicado", "less suitable"),
    "reco.l0": ("no recomendado", "not recommended"),
    "tip.reco": ("Cuándo lucirlo mejor, según las valoraciones de otros usuarios.<br>Cuanto más relleno el icono, más indicado.",
                 "When it shines the most, based on other users' ratings.<br>The fuller the icon, the better the fit."),
    "tip.rating": ("Valoración media: {0:.2f} de 5{1}", "Average rating: {0:.2f} out of 5{1}"),
    "tip.lon": ("Duración: {0}", "Longevity: {0}"),
    "tip.lon.d": ("Cuánto tiempo se mantiene sobre la piel.<br>Cuanto más lleno el reloj, más dura.",
                  "How long it lasts on skin.<br>The fuller the clock, the longer it lasts."),
    "tip.sil": ("Estela: {0}", "Sillage: {0}"),
    "tip.sil.d": ("El rastro que deja al pasar: hasta dónde se huele.<br>Cuanto más lleno el spray, más estela.",
                  "The trail it leaves behind: how far it can be smelled.<br>The fuller the spray, the stronger the trail."),
    "tip.axis.sweet_fresh": ("Dulce ↔ Fresco<br>Arrastra para indicar cómo lo percibes tú. Se guarda en tu perfil del perfume.",
                             "Sweet ↔ Fresh<br>Drag to say how you perceive it. Saved to your perfume profile."),
    "tip.axis.floral_woody": ("Floral ↔ Amaderado<br>Arrastra para indicar cómo lo percibes tú. Se guarda en tu perfil del perfume.",
                              "Floral ↔ Woody<br>Drag to say how you perceive it. Saved to your perfume profile."),
    "tip.axis.light_intense": ("Ligero ↔ Intenso<br>Arrastra para indicar cómo lo percibes tú. Se guarda en tu perfil del perfume.",
                               "Light ↔ Intense<br>Drag to say how you perceive it. Saved to your perfume profile."),
    "tip.top": ("Notas de salida<br>Lo primero que hueles al aplicarlo; se evaporan en pocos minutos.",
                "Top notes<br>What you smell first; they fade within minutes."),
    "tip.heart": ("Notas de corazón<br>El carácter del perfume; aparecen tras la salida y duran horas.",
                  "Heart notes<br>The character of the perfume; they appear after the top and last for hours."),
    "tip.base": ("Notas de fondo<br>La huella final; son las que más tardan en irse de la piel.",
                 "Base notes<br>The final trail; they linger longest on skin."),
    "tip.bars.notes": ("Cuánto pesa cada nota en el perfume.<br>La más intensa ocupa toda la barra.",
                       "How much each note weighs in the perfume.<br>The strongest fills the whole bar."),
    "tip.bars.accords": ("Los acordes son las «familias» de aromas que lo definen.<br>Cuanto más larga la barra, más presente está.",
                         "Accords are the aroma «families» that define it.<br>The longer the bar, the more present it is."),
    # --- ayudas de la interfaz ---
    "tip.search": ("Busca por nombre, marca o etiqueta. Entiende español e inglés.", "Search by name, brand or tag. Works in Spanish and English."),
    "tip.status": ("Filtra por el estado del perfume en tu colección.", "Filter by the perfume's status in your collection."),
    "tip.family": ("Filtra por familia olfativa.", "Filter by olfactive family."),
    "tip.fchip": ("Familia {0}<br>Pulsa para filtrar; puedes marcar varias.", "{0} family<br>Click to filter; you can pick several."),
    "tip.notechip": ("{0}<br>Pulsa para filtrar los perfumes que la llevan.", "{0}<br>Click to filter perfumes that contain it."),
    "tip.btn.remove": ("Quitar el perfume seleccionado de tu colección (no se borra de la base de datos).",
                       "Remove the selected perfume from your collection (it stays in the database)."),
    "tip.btn.toowned": ("Marcar el perfume seleccionado como que ya lo tienes.", "Mark the selected perfume as one you own."),
    "tip.btn.towishlist": ("Marcar el perfume seleccionado como deseado.", "Mark the selected perfume as wished."),
    "tip.btn.update": ("Descargar la última versión de la base de datos. No toca tu colección.",
                       "Download the latest version of the database. Your collection is untouched."),
    "tip.clear": ("Quitar todos los filtros y la búsqueda.", "Clear all filters and the search."),
    "tip.nav.collection": ("Los perfumes que tienes o deseas.", "The perfumes you own or wish for."),
    "tip.nav.finder": ("Explora toda la base de datos por familias y notas.", "Explore the whole database by families and notes."),
    "tip.nav.recs": ("Qué ponerte de tu colección según ocasión, hora y estación, cómo combinarlos y qué comprar.", "What to wear from your collection by occasion, time of day and season, how to layer them and what to buy."),
    "tip.rec.lay": ("Parejas de perfumes que se complementan al combinarlos (capas).", "Pairs of perfumes that complement each other when layered."),
    "tip.rec.sim": ("Perfumes de la base de datos parecidos a uno de los tuyos.", "Perfumes in the database similar to one of yours."),
    "tip.rec.gap": ("Qué le falta a tu colección y qué perfumes lo cubrirían.", "What your collection lacks and which perfumes would fill it."),
    "tip.lang": ("Idioma de la aplicación.", "Application language."),
    "tip.theme.light": ("Tema claro.", "Light theme."),
    "tip.theme.dark": ("Tema oscuro.", "Dark theme."),
    "gongora.sub": ("Tu perfumista con IA", "Your AI perfumer"),
     "gongora.hello": ("Hola, soy **Góngora**, tu perfumista. Cuéntame a dónde vas, qué te pones o qué ambiente buscas y te digo qué perfume de tu colección te pega.",
                       "Hi, I am **Góngora**, your perfumer. Tell me where you are going, what you are wearing or what mood you want, and I will tell you which perfume in your collection suits you."),
     "gongora.s1": ("🌙  Tengo un evento de noche formal", "🌙  I have a formal evening event"),
     "gongora.s1.q": ("Voy a un evento de noche formal, ¿qué perfume me pega?", "I am going to a formal evening event. Which perfume suits me?"),
     "gongora.s2": ("☀️  ¿Qué me pongo hoy?", "☀️  What should I wear today?"),
     "gongora.s2.q": ("¿Qué me pongo hoy?", "What should I wear today?"),
     "gongora.s3": ("🛍️  ¿Qué me falta en la colección?", "🛍️  What is my collection missing?"),
     "gongora.s3.q": ("¿Qué le falta a mi colección y qué me recomiendas comprar?", "What is my collection missing, and what would you recommend I buy?"),
     "gongora.thinking": ("Góngora está pensando…", "Góngora is thinking…"),
     "gongora.t.search_database": ("Consultando la base de datos…", "Searching the database…"),
     "gongora.t.layering_for": ("Probando combinaciones…", "Trying combinations…"),
     "gongora.t.suggest_layering": ("Preparando la combinación…", "Preparing the combination…"),
     "gongora.t.suggest_perfume": ("Preparando la sugerencia…", "Preparing the suggestion…"),
     "gongora.t.similar_to": ("Buscando perfumes parecidos…", "Looking for similar perfumes…"),
     "gongora.card.layer": ("Combinación sugerida", "Suggested combination"),
     "gongora.card.perfume": ("Perfume sugerido", "Suggested perfume"),
     "gongora.card.base": ("base", "base"), "gongora.card.top": ("encima", "on top"),
     "gongora.card.open": ("Abrir el perfil", "Open the profile"),
     "tip.gongora.fav": ("Guardar en Combinaciones favoritas (o quitarla)", "Save to Favorite combinations (or remove it)"),
     "tip.gongora.wish": ("Añadir a deseados (o quitarlo)", "Add to wishlist (or remove it)"),
     "gongora.clear": ("Limpiar chat", "Clear chat"),
     "gongora.clear.tip": ("Borra la conversación y empieza de nuevo.", "Delete the conversation and start over."),
     "gongora.send": ("Enviar", "Send"),
     "gongora.cfg": ("Configurar la IA de Góngora (clave de Gemini)", "Set up Góngora's AI (Gemini key)"),
     "gongora.key.title": ("IA de Góngora", "Góngora's AI"),
     "gongora.key.label": ("Pega tu clave de la API de Gemini (se crea gratis en Google AI Studio). Se guarda solo en este equipo, en la base de datos de la app. Déjala vacía para borrarla.",
                           "Paste your Gemini API key (free from Google AI Studio). It is stored only on this computer, in the app's database. Leave it empty to delete it."),
     "gongora.key.saved": ("Clave guardada. Ya puedes preguntarme.", "Key saved. You can ask me now."),
     "gongora.key.cleared": ("Clave borrada.", "Key deleted."),
     "gongora.nokey": ("Góngora no tiene clave de IA (se introduce al instalar la app). Mientras tanto te contesto con mis reglas básicas; si ya tienes una clave, puedes ponerla en el ⚙.",
                       "Góngora has no AI key (it is entered when installing the app). Meanwhile I will answer with my basic rules; if you already have a key, you can set it with the ⚙."),
     "gongora.err.rate": ("He agotado la cuota gratuita de la IA por ahora. Prueba de nuevo en un minuto (o mañana si es la cuota diaria).", "I have used up the free AI quota for now. Try again in a minute (or tomorrow if it is the daily quota)."),
     "gongora.err.net": ("No consigo conectar. Comprueba tu conexión a internet.", "I cannot connect. Check your internet connection."),
     "gongora.err.api": ("La IA devolvió un error: {0}", "The AI returned an error: {0}"),
     "gongora.refusal": ("Con eso no puedo ayudarte, pero con perfumes sí: cuéntame qué buscas.", "I cannot help with that, but with perfumes I can: tell me what you are after."),
     "tip.chat": ("Habla con Góngora, tu perfumista: qué ponerte según el plan o el outfit, cómo combinar o qué comprar.", "Talk to Góngora, your perfumer: what to wear for your plans or outfit, how to layer or what to buy."),
    "tip.chatinp": ("Escribe tu pregunta y pulsa Enter.", "Type your question and press Enter."),
    "tip.close": ("Cerrar", "Close"),
    "profile.close": ("Cerrar", "Close"),
    "profile.nodata": ("Sin datos de intensidad para este perfume", "No intensity data for this perfume"),
    "profile.intensity": ("Intensidad: {0}/100", "Intensity: {0}/100"),

    # --- mis gustos ---
    "taste.hint": ("Pasa el ratón por una nota, familia, acorde, marca, década o punto y verás en todos los gráficos qué perfumes lo forman.", "Hover a note, family, accord, brand, decade or dot to see which perfumes make it up in every chart."),
    "taste.cap.1": ("{0} perfume", "{0} perfume"),
    "taste.cap.n": ("{0} perfumes", "{0} perfumes"),
    "an.empty": ("Añade perfumes a tu colección para ver el análisis.", "Add perfumes to your collection to see the analysis."),
    "none.f": ("ninguna", "none"),
    "none.m": ("ninguno", "none"),

    # --- recomendaciones ---
    "rec.h": ("Recomendaciones", "Recommendations"),
     "buy.why.fam": ("Aporta {0}, una familia que aún no tienes", "Adds {0}, a family you do not have yet"),
     "buy.why.layer": ("Combina en layering con {0}: {1}", "Layers well with {0}: {1}"),
     "buy.why.filt": ("Encaja con lo que buscas: {0}", "Fits what you are looking for: {0}"),
     "buy.why.rating": ("Muy bien valorado: ★ {0} con {1} votos", "Highly rated: ★ {0} from {1} votes"),
     "buy.why.gender": ("Mantiene el equilibrio de género de tu colección ({0})", "Keeps your collection's gender balance ({0})"),
     "buy.why.title": ("Por qué lo sugiero", "Why I suggest it"),
     "fav.nowhy": ("Combinación guardada", "Saved combination"),
     "rec.pick": ("Elegir perfume", "Choose perfume"),
     "tip.rec.pick": ("Elige un perfume de tu colección para ver combinaciones (layering) y sugerencias en torno a él.", "Pick a perfume from your collection to see layering combinations and suggestions around it."),
     "rec.want": ("¿Qué buscas?", "What are you after?"),
     "rec.mode.comp": ("Complementarios", "Complementary"),
     "rec.mode.sim": ("Similares", "Similar"),
     "tip.rec.mode.comp": ("Lo que le falta a tu colección (o a este perfume).", "What your collection (or this perfume) is missing."),
     "tip.rec.mode.sim": ("Perfumes que creo que te gustarán según lo que ya tienes (o parecidos al elegido).", "Perfumes I think you will like based on what you own (or similar to the chosen one)."),
     "rec.buy.s": ("Perfumes que aún no tienes y se parecen a lo que te gusta", "Perfumes you do not own yet that resemble what you like"),
     "rec.buy.sa": ("Perfumes que aún no tienes y se parecen a {0}", "Perfumes you do not own yet that resemble {0}"),
     "rec.layer.with": ("Layering con {0}", "Layering with {0}"),
     "buy.why.sim": ("Se parece a {0} ({1}% de parecido)", "Resembles {0} ({1}% similar)"),
     "buy.why.notes": ("Comparte notas: {0}", "Shares notes: {0}"),
     "ver.title": ("Versiones", "Versions"),
    "ver.current": ("Versión instalada: {0}", "Installed version: {0}"),
    "ver.footer": ("Versión {0}", "Version {0}"),
    "ver.footer.new": ("⬆ Nueva versión {0}", "⬆ New version {0}"),
    "ver.checking": ("Buscando actualizaciones…", "Checking for updates…"),
    "ver.available": ("Hay una versión nueva: {0}", "A new version is available: {0}"),
    "ver.uptodate": ("Tienes la última versión.", "You have the latest version."),
    "ver.none": ("Todavía no hay versiones publicadas.", "No versions have been published yet."),
    "ver.update": ("Actualizar a v{0}", "Update to v{0}"),
    "ver.check": ("Buscar actualizaciones", "Check for updates"),
    "ver.skip": ("Omitir esta versión", "Skip this version"),
    "ver.github": ("Ver en GitHub", "View on GitHub"),
    "ver.close": ("Cerrar", "Close"),
    "ver.downloading": ("Descargando la actualización…", "Downloading the update…"),
    "ver.installing": ("Instalando… la aplicación se cerrará y volverá a abrirse sola.", "Installing… the application will close and reopen by itself."),
    "ver.nonotes": ("(Sin notas de esta versión.)", "(No notes for this version.)"),
    "ver.tag.installed": ("· instalada", "· installed"),
    "ver.tag.new": ("· nueva", "· new"),
    "ver.source": ("Estás ejecutando la app desde el código fuente: actualízala con «git pull» o descarga el instalador desde GitHub.", "You are running the app from source: update it with “git pull” or download the installer from GitHub."),
    "ver.err.notconfigured": ("Las actualizaciones no están configuradas: falta indicar el repositorio de GitHub en core/version.py.", "Updates are not set up: the GitHub repository is missing in core/version.py."),
    "ver.err.net": ("No hay conexión con GitHub. Comprueba tu conexión a internet.", "Cannot reach GitHub. Check your internet connection."),
    "ver.err.notfound": ("No encuentro el repositorio o aún no tiene versiones publicadas.", "I cannot find the repository or it has no published versions yet."),
    "ver.err.ratelimit": ("GitHub limita las consultas por ahora. Prueba de nuevo más tarde.", "GitHub is limiting requests for now. Try again later."),
    "ver.err.asset": ("Esa versión no incluye el instalador (.exe). Descárgala desde GitHub.", "That version does not include the installer (.exe). Download it from GitHub."),
    "ver.err.hash": ("La descarga no coincide con la huella (SHA-256) que publica GitHub; se ha cancelado por seguridad.", "The download does not match the SHA-256 fingerprint published by GitHub; it was cancelled for safety."),
    "ver.err.size": ("La descarga está incompleta. Inténtalo de nuevo.", "The download is incomplete. Try again."),
    "ver.err.untrusted": ("El instalador no viene de GitHub; no se descarga.", "The installer does not come from GitHub; it will not be downloaded."),
    "ver.err.platform": ("La actualización automática solo funciona en Windows.", "Automatic update only works on Windows."),
    "ver.err.badjson": ("GitHub devolvió una respuesta que no entiendo.", "GitHub returned a response I cannot understand."),
    "ver.err.other": ("No se pudo completar la operación ({0}).", "The operation could not be completed ({0})."),
    "ver.prompt": ("Hay una versión nueva de Perfúmappte ({0}). Puedes actualizarla ahora sin descargar nada a mano.", "There is a new version of Perfúmappte ({0}). You can update it now without downloading anything by hand."),
    "tip.ver": ("Versiones de Perfúmappte y novedades. Aquí puedes buscar e instalar actualizaciones.", "Perfúmappte versions and release notes. You can check for and install updates here."),
    "nav.settings": ("Configuración", "Settings"),
    "tip.nav.settings": ("Actualizaciones de la aplicación y ajustes.", "Application updates and settings."),
    "set.title": ("Configuración", "Settings"),
    "set.updates": ("Actualizaciones", "Updates"),
    "set.auto": ("Buscar actualizaciones automáticamente una vez al día", "Check for updates automatically once a day"),
    "set.auto.tip": ("Si la desactivas, solo se busca cuando pulses el botón de abajo.", "If you turn it off, updates are only checked when you press the button below."),
    "set.images": ("Imágenes", "Images"),
    "set.nobg": ("Quitar el fondo blanco de las fotos de los perfumes", "Remove the white background from perfume photos"),
    "set.nobg.tip": ("Las fotos de frascos blancos o de cristal muy claro se dejan como están.", "Photos of white or very pale glass bottles are left as they are."),
    "set.check": ("Buscar actualizaciones ahora…", "Check for updates now…"),
    "tip.fold.close": ("Contraer la barra lateral", "Collapse the sidebar"),
     "tip.fold.open": ("Ampliar la barra lateral", "Expand the sidebar"),
     "col.tab.taste": ("Mis gustos", "My tastes"),
     "tip.col.tab.taste": ("Gráficos sobre los perfumes que tienes.", "Charts about the perfumes you own."),
     "taste.count": ("Perfumes", "Perfumes"), "taste.count.c": ("en tu colección", "in your collection"),
     "taste.rating": ("Valoración media", "Average rating"), "taste.family": ("Familia favorita", "Favorite family"),
     "taste.note": ("Nota estrella", "Star note"), "taste.gender": ("Género", "Gender"),
     "taste.families": ("Familias olfativas", "Olfactive families"), "taste.notes": ("Notas más repetidas", "Most repeated notes"),
     "taste.accords": ("Acordes dominantes", "Dominant accords"), "taste.accords.sub": ("Peso medio de cada acorde en tu colección.", "Average weight of each accord in your collection."),
     "taste.when": ("Cuándo los usas", "When you wear them"), "taste.when.sub": ("Según los votos de estaciones y de día o noche.", "Based on season and day or night votes."),
     "taste.profile": ("Tu perfil olfativo", "Your olfactive profile"), "taste.profile.sub": ("Cada forma tenue es un perfume; la sólida es tu media. Sus extremos son los de cada eje del perfil.", "Each faint shape is a perfume; the solid one is your average. Its spokes are the ends of each profile axis."),
     "taste.scatter": ("Duración y estela", "Longevity and sillage"), "taste.scatter.sub": ("Pasa el ratón por un punto para ver qué perfume es.", "Hover a dot to see which perfume it is."),
     "taste.brands": ("Marcas favoritas", "Favorite brands"), "taste.decades": ("Épocas", "Eras"), "taste.decades.sub": ("Año de lanzamiento de tus perfumes.", "Release year of your perfumes."),
     "taste.low": ("Baja", "Low"), "taste.high": ("Alta", "High"), "taste.others": ("Otras", "Others"),
     "taste.long": ("Duración", "Longevity"), "taste.sill": ("Estela", "Sillage"),
     "col.tab.perf": ("Perfumes", "Perfumes"),
     "col.tab.fav": ("Combinaciones favoritas", "Favorite combinations"),
     "tip.col.tab.perf": ("Tus perfumes.", "Your perfumes."),
     "tip.col.tab.fav": ("Combinaciones de layering que has marcado con el corazón en Recomendaciones.", "Layering combinations you hearted in Recommendations."),
     "fav.empty": ("Aún no tienes combinaciones favoritas. Marca el corazón de una combinación en Recomendaciones.", "No favorite combinations yet. Tap the heart on a combination in Recommendations."),
     "tip.fav.heart": ("Guardar en Combinaciones favoritas (o quitarla).", "Save to Favorite combinations (or remove it)."),
     "rec.buy": ("Añadir opciones de compra", "Add buying options"),
     "rec.buy.h": ("Opciones de compra", "Buying options"),
     "rec.buy.f": ("Perfumes que aún no tienes y encajan con tus filtros", "Perfumes you do not own yet that fit your filters"),
     "rec.buy.c": ("Perfumes que aún no tienes y complementan tu colección", "Perfumes you do not own yet that complement your collection"),
     "rec.buy.none": ("No he encontrado perfumes que sumar con estos filtros.", "I found no perfumes to add with these filters."),
     "tip.rec.buy": ("Sugiere perfumes de la base de datos que no tienes en propiedad (los deseados valen).", "Suggest perfumes from the database you do not own (wishlist ones count)."),
     "layer.spray1": ("1 atomización", "1 spray"),
     "layer.sprays": ("{0} atomizaciones", "{0} sprays"),
     "layer.base": ("Base", "Base"),
     "layer.top": ("Encima", "On top"),
     "tip.layer.base": ("El más pesado: se aplica primero.", "The heavier one: apply it first."),
     "tip.layer.top": ("El más ligero: se aplica después, encima.", "The lighter one: apply it second, on top."),
     "rec.layer": ("Añadir opciones de layering", "Add layering options"),
     "rec.layer.h": ("Combinaciones de layering", "Layering combinations"),
     "rec.layer.none": ("No he encontrado combinaciones que encajen entre estos perfumes.", "I found no combinations that fit among these perfumes."),
     "tip.rec.layer": ("Sugiere combinaciones (layering) entre los perfumes según sus notas y acordes.", "Suggest layering combinations among the perfumes based on their notes and accords."),
     "rec.hour": ("Por hora", "By time of day"),
     "rec.hint": ("Elige una ocasión, una hora o una estación y buscaré en tu colección.", "Pick an occasion, a time of day or a season and I will search your collection."),
     "rec.found": ("{0} de {1} perfumes de tu colección encajan", "{0} of {1} perfumes in your collection fit"),
     "tip.rec.reco": ("Perfumes de tu colección según ocasión, hora y estación.", "Perfumes from your collection by occasion, time of day and season."),
     "tip.rec.occ": ("Elige una o varias ocasiones.", "Pick one or more occasions."),
     "tip.rec.hour": ("Elige día, noche o ambos.", "Pick day, night or both."),
     "tip.rec.sea": ("Elige una o varias estaciones.", "Pick one or more seasons."),
    "rec.occ": ("Por ocasión", "By occasion"),
    "rec.sea": ("Por estación", "By season"),
    "rec.none": ("Sin resultados en tu colección.", "No results in your collection."),
    "rec.empty": ("Tu colección está vacía.", "Your collection is empty."),

    # --- añadir a la colección ---

    # --- asistente ---
    "chat.title": ("Góngora", "Góngora"),
    "chat.ph": ("Pregúntale a Góngora…", "Ask Góngora…"),
    "chat.empty": ("Tu colección está vacía. Añade perfumes desde «Descubrimientos» y podré aconsejarte.",
                   "Your collection is empty. Add perfumes from “Discoveries” and I can advise you."),
    "chat.combine.need": ("Necesito más perfumes en tu colección para combinar.",
                          "I need more perfumes in your collection to combine."),
    "chat.combine.for": ("Para combinar <b>{0}</b>:<br>", "To combine <b>{0}</b>:<br>"),
    "chat.combine.tip": ("<i>Tip: aplica primero el más denso y encima el más ligero.</i>",
                         "<i>Tip: apply the densest first and the lightest on top.</i>"),
    "chat.combine.best": ("Mis mejores combinaciones:<br>", "My best combinations:<br>"),
    "chat.combine.none": ("Aún no veo combinaciones claras.", "I don't see clear combinations yet."),
    "chat.gaps": ("Familias que no tienes: {0}.<br>Estaciones sin cubrir: {1}. Ocasiones: {2}.<br>"
                  "Perfiles que faltan: {3}.<br>Sugerencias: {4}",
                  "Families you don't have: {0}.<br>Uncovered seasons: {1}. Occasions: {2}.<br>"
                  "Missing profiles: {3}.<br>Suggestions: {4}"),
    "chat.similar.need": ("Dime de qué perfume quieres alternativas (por ejemplo: «similares a Sauvage»).",
                          "Tell me which perfume you want alternatives for (for example: “similar to Sauvage”)."),
    "chat.similar.for": ("Parecidos a <b>{0}</b>:<br>", "Similar to <b>{0}</b>:<br>"),
    "chat.today": ("Para {0} en {1}, te propongo:<br>", "For {0} in {1}, I'd suggest:<br>"),
    "chat.today.word": ("hoy", "today"),
    "chat.help": ("Pregúntame: «¿Qué me pongo hoy?», «¿Cómo combino Sauvage?», «¿Qué le falta a mi colección?» o «similares a Libre».",
                  "Ask me: “What should I wear today?”, “How do I combine Sauvage?”, “What's missing from my collection?” or “similar to Libre”."),
    "why.layer": ("{0} + {1} se complementan", "{0} + {1} complement each other"),
    "why.bridge": ("nota puente: ", "bridge note: "),
    "why.accord": ("acorde puente: ", "bridge accord: "),
    "why.same": ("demasiado parecidos", "too similar"),
    "why.contrast": ("contraste de perfil", "profile contrast"),

    # --- actualización / base de datos ---
    "up.help.title": ("Base de datos vacía", "Empty database"),
    "up.help": ("Para actualizar la base de datos de perfumes necesito tu acceso a Kaggle (es gratis; sin él la base de datos de perfumes no se actualiza).\n\n"
                "1) Entra en kaggle.com con tu cuenta → Settings → API (kaggle.com/settings/api).\n"
                "2) En el apartado API pulsa «Create Legacy API Key» (es la única opción que descarga el archivo kaggle.json).\n"
                "3) Cópialo a  C:\\Users\\TU_USUARIO\\.kaggle\\kaggle.json  (crea la carpeta .kaggle si no existe).\n"
                "4) Pulsa «Actualizar perfumes» en «Descubrimientos».",
                "To update the perfume database I need your Kaggle access (it is free; without it the perfume database is not updated).\n\n"
                "1) Sign in at kaggle.com → Settings → API (kaggle.com/settings/api).\n"
                "2) In the API section click “Create Legacy API Key” (it is the only option that downloads the kaggle.json file).\n"
                "3) Copy it to  C:\\Users\\YOUR_USER\\.kaggle\\kaggle.json  (create the .kaggle folder if it does not exist).\n"
                "4) Press “Update perfumes” in “Discoveries”."),
    "up.title": ("Actualización", "Update"),
    "up.none": ("Base de datos: sin actualizar", "Database: not updated"),
    "up.at": ("Base de datos actualizada el {0}", "Database updated on {0}"),
    "up.nopkg": ("Falta el paquete «kaggle»: ejecuta  pip install kaggle", "The “kaggle” package is missing: run  pip install kaggle"),
    "up.nocred": ("No encuentro tus credenciales de Kaggle.", "I can't find your Kaggle credentials."),
    "up.downloading": ("Descargando de Kaggle…", "Downloading from Kaggle…"),
    "up.importing": ("Importando…", "Importing…"),
    "up.nofile": ("La descarga no produjo ", "The download did not produce "),
    "up.starting": ("Preparando…", "Getting ready…"),
    "up.done": ("✓ Listo · {0}", "✓ Done · {0}"),
    "up.prog": ("Importando… {0:,}", "Importing… {0:,}"),
    "db.preparing": ("preparando… {0:,}", "preparing… {0:,}"),
    "db.res": ("nuevos: {0} · actualizados: {1}", "new: {0} · updated: {1}"),
    "db.total": ("Total:", "Total:"),
    "db.keys": ("claves del archivo:", "file keys:"),
    "db.mapped": ("mapeado:", "mapped:"),
    "db.uptodate": ("Ya está al día.", "Already up to date."),
}

def tr(key, *a):
    """Cadena de la interfaz en el idioma activo. Admite {0} y %s en las plantillas."""
    es, en = UI[key]
    s = es if LANG == "es" else en
    if not a: return s
    try: return s.format(*a) if "{" in s else s % a
    except (IndexError, KeyError, ValueError): return s

OCCASIONS = ["casual", "oficina", "cita", "formal", "noche", "deporte"]
SEASONS = ["primavera", "verano", "otoño", "invierno"]
GENDERS = {"male": ("Masculino", "Male"), "female": ("Femenino", "Female"), "unisex": ("Unisex", "Unisex")}
PROFILE_AXES = [("dulce", "fresco"), ("floral", "amaderado"), ("ligero", "intenso")]   # (izquierda, derecha), canónicos

FAMILIES_ES_EN = {  # familia canónica (ES) -> fragmentos con los que se busca en la BD
    "Cítrica": ["citric", "citrus"], "Floral": ["floral", "white floral", "rose"],
    "Amaderada": ["amader", "woody"], "Oriental": ["orient", "ambar", "amber", "balsamic"],
    "Aromática": ["aromat", "herbal"], "Gourmand": ["gourmand", "vanilla", "sweet"],
    "Fougère": ["fougere"], "Acuática": ["acuat", "aquatic", "marine", "ozonic"],
    "Chipre": ["chipre", "chypre", "mossy"], "Cuero": ["cuero", "leather"],
    "Especiada": ["especi", "spicy"], "Frutal": ["frutal", "fruity"]}
FAMILY_EN_ES = {"Cítrica": "Citrus", "Floral": "Floral", "Amaderada": "Woody", "Oriental": "Oriental",
                "Aromática": "Aromatic", "Gourmand": "Gourmand", "Fougère": "Fougère", "Acuática": "Aquatic",
                "Chipre": "Chypre", "Cuero": "Leather", "Especiada": "Spicy", "Frutal": "Fruity"}

LON_EN = {"Corta": "Short", "Moderada": "Moderate", "Larga": "Long-lasting", "Eterna": "Eternal"}
SIL_EN = {"Suave": "Subtle", "Moderada": "Moderate", "Fuerte": "Strong", "Enorme": "Enormous"}
OCC_EN = {"casual": "casual", "oficina": "office", "cita": "date", "formal": "formal", "noche": "night", "deporte": "sport"}
SEA_EN = {"primavera": "spring", "verano": "summer", "otoño": "autumn", "invierno": "winter"}
DAY_EN = {"día": "day", "noche": "night", "day": "day", "night": "night"}
AXIS_EN = {"dulce": "sweet", "fresco": "fresh", "floral": "floral", "amaderado": "woody", "ligero": "light", "intenso": "intense"}

# Acuerdos y familias tal como los guarda la base de datos (inglés) -> español (forma femenina,
# como las etiquetas de la app).  Los 92 valores reales del dataset, más los de las notas.
ACC_ES = {
    "alcohol": "Alcohol", "aldehydic": "Aldehídica", "almond": "Almendrada", "amber": "Ámbar",
    "ambergris": "Ámbar gris", "animal notes": "Animal", "animalic": "Animal", "anis": "Anís",
    "aquatic": "Acuática", "aromatic": "Aromática", "asphalt": "Asfalto", "asphault": "Asfalto",
    "bacon": "Tocino", "balsamic": "Bálsámica", "bbq": "Barbacoa", "beeswax": "Cera de abejas",
    "bitter": "Amarga", "brown scotch tape": "Cinta adhesiva", "cacao": "Cacao", "camphor": "Alcanfor",
    "cannabis": "Cannabis", "caramel": "Caramelo", "champagne": "Champán", "cherry": "Cereza",
    "chocolate": "Chocolate", "cinnamon": "Canela", "citrus": "Cítrica", "citruses": "Cítricos",
    "clay": "Arcilla", "coca-cola": "Coca-Cola", "coconut": "Coco", "coffee": "Café",
    "conifer": "Conífera", "earthy": "Terrosa", "floral": "Floral", "forest": "Bosque",
    "foresty": "Bosque", "fresh": "Fresco", "fresh spicy": "Especiada fresca", "fruity": "Frutal",
    "gasoline": "Gasolina", "gourmand": "Gourmand", "green": "Verde", "herbal": "Herbal",
    "honey": "Miel", "hot iron": "Hierro caliente", "industrial glue": "Pegamento industrial",
    "iris": "Iris", "lactonic": "Láctica", "lavender": "Lavanda", "leather": "Cuero",
    "marine": "Marina", "meat": "Carne", "metallic": "Metálica", "milky": "Láctea",
    "mineral": "Mineral", "mossy": "Musgosa", "musk": "Almizcle", "musky": "Almizclada",
    "nutty": "Avellana", "oily": "Aceitosa", "oud": "Oud", "ozonic": "Ozónica", "paper": "Papel",
    "patchouli": "Pachulí", "pear": "Pera", "plastic": "Plástica", "powdery": "Atalcada",
    "rose": "Rosa", "rubber": "Caucho", "rum": "Ron", "sake": "Sake", "salty": "Salada",
    "sand": "Arena", "savory": "Sabrosa", "smoky": "Ahumada", "soapy": "Jabón",
    "soft spicy": "Especiada suave", "sour": "Ácida", "spice": "Especias", "spices": "Especias",
    "spicy": "Especiada", "sweet": "Dulce", "tennis ball": "Pelota de tenis", "terpenic": "Terpénica",
    "tobacco": "Tabaco", "tropical": "Tropical", "tuberose": "Tuberosa", "vanilla": "Vainilla",
    "varnish": "Barniz", "vinyl": "Vinilo", "violet": "Violeta", "vodka": "Vodka",
    "warm spicy": "Especiada cálida", "water": "Agua", "wet plaster": "Yeso húmedo",
    "whiskey": "Whisky", "white floral": "Floral blanca", "wine": "Vino", "woody": "Amaderada",
    "yellow floral": "Floral amarilla", "chypre": "Chipre", "fougere": "Fougère"}

# Traducción de las claves de la paleta de acordes: la clave canónica es la que guarda la base de
# datos (inglés) y la traducida se busca con la inversa de ACC_ES, para que el color de un acorde
# sea el mismo vaya el nombre en inglés o ya en español.
_ACCORD_ES_KEY = {norm(es): en for en, es in ACC_ES.items()}

def accord_key(name):
    """Clave canónica (inglés) de un acorde: «Floral Blanca» -> «white floral», «White Floral» -> «white floral»."""
    n = norm(name)
    return _ACCORD_ES_KEY.get(n, n) if n else ""

def ACCORD_COLORS_ES(colors):
    """La paleta de accords con las claves traducidas añadidas («Amaderada» -> el color de «woody»),
    de modo que el color se resuelva tanto con el nombre canónico como con su traducción."""
    out = dict(colors)
    for en, color in list(colors.items()):
        es = ACC_ES.get(en)
        if es: out.setdefault(es, color)
    return out

# Palabras de nota: sustantivos en _N, adjetivos en _A (con género y plural correctos).
_N = {
    "musk": "almizcle", "vanilla": "vainilla", "vanille": "vainilla", "rose": "rosa",
    "amber": "ámbar", "ambergris": "ámbar gris", "sandalwood": "sándalo", "sandal": "sándalo",
    "jasmine": "jazmín", "orange": "naranja", "patchouli": "pachulí", "bergamot": "bergamota",
    "cedar": "cedro", "cedarwood": "cedro", "vetiver": "vetiver", "pepper": "pimienta",
    "oud": "oud", "agarwood": "oud", "akigalawood": "akigalawood", "lemon": "limón",
    "lavender": "lavanda", "tonka": "tonka", "green": "verde", "violet": "violeta",
    "leather": "cuero", "mandarin": "mandarina", "cardamom": "cardamono", "iris": "iris",
    "oakmoss": "musgo de roble", "cedarmoss": "musgo de cedro", "incense": "incienso",
    "labdanum": "labdano", "tobacco": "tabaco", "grapefruit": "pomelo", "leaf": "hoja",
    "cinnamon": "canela", "cinammon": "canela", "tea": "té", "saffron": "azafrán",
    "neroli": "neroli", "benzoin": "benzoína", "ginger": "jengibre", "lily": "lirio",
    "apple": "manzana", "wood": "madera", "coconut": "coco", "sugar": "azúcar",
    "ylang": "ylang", "geranium": "geranio", "tuberose": "tuberosa", "honey": "miel",
    "sage": "salvia", "lime": "lima", "caramel": "caramelo", "nutmeg": "nuez moscada",
    "almond": "almendra", "raspberry": "frambuesa", "mint": "menta", "peppermint": "hierbabuena",
    "spearmint": "hierbabuena blanca", "currant": "grosella", "blackcurrant": "grosella negra",
    "sea": "mar", "water": "agua", "milk": "leche", "moss": "musgo", "olibanum": "olibano",
    "frankincense": "incienso", "orris": "raíz de iris", "pear": "pera", "myrrh": "mirra",
    "juniper": "enebro", "fig": "higo", "magnolia": "magnolia", "balsam": "bálsamo",
    "coffee": "café", "peony": "peonía", "gardenia": "gardenia", "orchid": "orquídea",
    "cherry": "cereza", "guaiac": "guayacán", "plum": "ciruela", "freesia": "freesia",
    "strawberry": "fresa", "cream": "crema", "coriander": "cilantro", "pineapple": "piña",
    "galbanum": "galbano", "heliotrope": "heliotropo", "pine": "pino", "cypress": "ciprés",
    "fir": "abeto", "spruce": "abeto", "aldehyde": "aldehído", "aldehydes": "aldehídos", "ambrette": "ambretón",
    "petitgrain": "petitgrain", "rosemary": "romero", "osmanthus": "osmantus",
    "mimosa": "mimosa", "smoke": "humo", "rum": "ron", "oak": "roble", "lotus": "loto",
    "basil": "albahaca", "cacao": "cacao", "cocoa": "cacao", "root": "raíz", "salt": "sal",
    "sambac": "sambac", "cloves": "clavos de olor", "clove": "clavo de olor",
    "birch": "abedul", "carnation": "clavel", "ambroxan": "ambroxan", "herb": "hierba",
    "grass": "hierba", "oil": "aceite", "anise": "anís", "clary": "salvia",
    "resin": "resina", "resins": "resinas", "rosewood": "palisandro", "palisander": "palisandro",
    "blood": "sangre", "apricot": "albaricoque", "suede": "ante", "tangerine": "mandarina",
    "clementine": "clementina", "lilac": "lila", "bourbon": "borbón", "mango": "mango",
    "elemi": "elemi", "cashmeran": "cashmeran", "civet": "algalia", "honeysuckle": "madreselva",
    "frangipani": "frangipani", "castoreum": "castoreo", "mallow": "malva",
    "narcissus": "narciso", "thyme": "tomillo", "styrax": "estirax", "artemisia": "artemisia",
    "yuzu": "yuzu", "chamomile": "manzanilla", "hay": "heno", "ozonic": "ozónica",
    "immortelle": "inmortalelle", "marshmallow": "nubes", "cumin": "comino", "melon": "melón",
    "beeswax": "cera de abejas", "cypriol": "cipriol", "cassis": "grosella negra",
    "blackberry": "zarzamora", "cotton": "algodón", "opoponax": "opoponax", "butter": "mantequilla",
    "hyacinth": "jacinto", "hiacynth": "jacinto", "verbena": "verbena", "cognac": "coñac",
    "angelica": "angélica", "star": "estrella", "tincture": "tintura", "praline": "praliné",
    "watery": "acuosa", "hazelnut": "avellana", "champaca": "champaca", "candy": "caramelo",
    "whiskey": "whisky", "eucalyptus": "eucalipto", "rhubarb": "ruibarbo", "amyris": "amiris",
    "linden": "tilo", "tolu": "tolu", "coumarin": "cumarina", "litchi": "lichi",
    "lychee": "lichi", "pomegranate": "granada", "licorice": "regaliz", "absolute": "absoluto",
    "seaweed": "algas", "citron": "citrón", "bay": "laurel", "carrot": "zanahoria",
    "marigold": "caléndula", "pistachio": "pistacho", "rice": "arroz", "soil": "tierra",
    "champagne": "champán", "cucumber": "pepino", "wine": "vino", "hibiscus": "hibisco",
    "caraway": "alcaravea", "custard": "crema pastelera", "blueberry": "arándano",
    "cranberry": "arándano", "tar": "alquitrán", "mate": "mate", "lemongrass": "hierba limón",
    "bamboo": "bambú", "banana": "plátano", "berry": "baya", "syrup": "jarabe",
    "myrtle": "arrayán", "seed": "semilla", "tarragon": "dragón", "tomato": "tomate",
    "peel": "cáscara", "pumpkin": "calabaza", "maple": "arce", "petal": "pétalo",
    "olive": "oliva", "grape": "uva", "guava": "guayaba", "fern": "helecho", "teak": "teca",
    "ivy": "hiedra", "nectarine": "nectarina", "balm": "bálsamo", "toffee": "caramelo",
    "fennel": "hinojo", "date": "dátil", "skin": "piel", "nard": "nardo", "cane": "caña",
    "mahogany": "caoba", "cassia": "casia", "quince": "membrillo", "walnut": "nogal",
    "pea": "guisante", "truffle": "trufa", "tulip": "tulipán", "ink": "tinta",
    "papaya": "papaya", "sesame": "sésamo", "opium": "opio", "wisteria": "wisteria",
    "kiwi": "kiwi", "hyrax": "hyrax", "dew": "rocío", "drop": "gota", "gin": "gina",
    "oat": "avena", "oats": "avena", "bread": "pan", "matcha": "matcha", "meringue": "merengue",
    "popcorn": "palomitas", "amaretto": "amaretto", "espresso": "expreso", "cappuccino": "capuchino",
    "oregano": "orégano", "celery": "apio", "bark": "corteza", "palm": "palmera",
    "kumquat": "kumquat", "copal": "copal", "elder": "saúco", "calamus": "cálamo",
    "silk": "seda", "cactus": "cactus", "linen": "lino", "chili": "chile",
    "daisy": "margarita", "copaiba": "copaiba", "chrysanthemum": "crisantemo",
    "algae": "algas", "marzipan": "marzipán", "marjoram": "mejorana", "camellia": "camelia",
    "wool": "lana", "soap": "jabón", "pandanus": "pandano", "macarons": "macarons",
    "lichen": "liquen", "datura": "datura", "brandy": "coñac", "paprika": "pimentón",
    "chestnut": "castaño", "fenugreek": "fenugreco", "bellflower": "campanula",
    "molasses": "melaza", "mustard": "mostaza", "massoia": "massoia", "raisin": "pasas",
    "plumeria": "plumeria", "attar": "attar", "sunflower": "girasol", "kaffir": "kaffir",
    "pollen": "polen", "agave": "agave", "tamarind": "tamarindo", "peat": "turba",
    "rhododendron": "rododendro", "liatris": "liatris", "cistus": "cistus", "petrichor": "petricor",
    "macadamia": "macadamia", "ginseng": "ginseng", "mace": "maza", "thuja": "tuya",
    "rooibos": "rooibos", "hops": "lúpulo", "notes": "notas", "note": "notas",
    "ylang-ylang": "ylang-ylang", "candied": "confitado", "salt": "sal", "oakmoss": "musgo de roble",
    "cashmere": "cachemir", "ambrette": "ambretón", "petrichor": "petricor", "vetiver": "vetiver",
    "moss": "musgo", "resin": "resina", "frankincense": "incienso", "orris": "raíz de iris",
    "milk": "leche", "honey": "miel", "suede": "ante",
    "papyrus": "papiro", "birch": "abedul", "pod": "vaina",
    "crumb": "miga", "shell": "cáscara", "stone": "piedra", "stick": "vara",
    "sprig": "ramita", "twig": "ramita", "heart": "corazón", "flesh": "pulpa"}
_A = {  # adjetivo: (masculino, femenino, masculino plural, femenino plural)
    "white": ("blanco", "blanca", "blancos", "blancas"), "black": ("negro", "negra", "negros", "negras"),
    "red": ("rojo", "roja", "rojos", "rojas"), "pink": ("rosa", "rosa", "rosas", "rosas"),
    "yellow": ("amarillo", "amarilla", "amarillos", "amarillas"), "green": ("verde", "verde", "verdes", "verdes"),
    "wild": ("silvestre", "silvestre", "silvestres", "silvestres"), "dried": ("seco", "seca", "secos", "secas"),
    "fresh": ("fresco", "fresca", "frescos", "frescas"), "bitter": ("amargo", "amarga", "amargos", "amargas"),
    "spicy": ("especiado", "especiada", "especiados", "especiadas"), "sweet": ("dulce", "dulce", "dulces", "dulces"),
    "powdery": ("atalcado", "atalcada", "atalcados", "atalcadas"),
    "salty": ("salado", "salada", "salados", "saladas"), "smoky": ("ahumado", "ahumada", "ahumados", "ahumadas"),
    "woody": ("amaderado", "amaderada", "amaderados", "amaderadas"), "woodsy": ("leñoso", "leñosa", "leñosos", "leñosas"),
    "fruity": ("frutal", "frutal", "frutales", "frutales"), "floral": ("floral", "floral", "florales", "florales"),
    "herbal": ("herbal", "herbal", "herbales", "herbales"), "aquatic": ("acuático", "acuática", "acuáticos", "acuáticas"),
    "musky": ("almizclado", "almizclada", "almizclados", "almizcladas"),
    "earthy": ("terroso", "terrosa", "terrosos", "terrosas"), "creamy": ("cremoso", "cremosa", "cremosos", "cremosas"),
    "golden": ("dorado", "dorada", "dorados", "doradas"), "silver": ("plateado", "plateada", "plateados", "plateadas"),
    "brown": ("marrón", "marrón", "marrones", "marrones"), "dark": ("oscuro", "oscura", "oscuros", "oscuras"),
    "soft": ("suave", "suave", "suaves", "suaves"), "rich": ("rico", "rica", "ricos", "ricas"),
    "warm": ("cálido", "cálida", "cálidos", "cálidas"), "natural": ("natural", "natural", "naturales", "naturales"),
    "candied": ("confitado", "confitada", "confitados", "confitadas"),
    "toasted": ("tostado", "tostada", "tostados", "tostadas"), "liquid": ("líquido", "líquida", "líquidos", "líquidas"),
    "liqueur":("alicorado", "alicorada", "alicorados","alicoradas"),}
_FN = {"of": "de", "the": "la", "and": "y", "with": "con", "de": "de", "y": "y"}   # palabras funcionales

# Frases completas (el dataset trae muchas variantes de la misma nota).
_PHRASES = {
    "woody notes": "notas amaderadas", "floral notes": "notas florales", "green notes": "notas verdes",
    "spicy notes": "notas especiadas", "sweet notes": "notas dulces", "fruity notes": "notas frutales",
    "powdery notes": "notas atalcadas", "aquatic notes": "notas acuáticas", "herbal notes": "notas herbales",
    "oriental notes": "notas orientales", "animal notes": "notas animales", "sea notes": "notas de mar",
    "water notes": "notas de agua", "ozonic notes": "notas ozónicas", "fresh notes": "notas frescas",
    "musk notes": "notas de almizcle", "amber notes": "notas de ámbar", "clean notes": "notas limpias",
    "tonka bean": "haba de tonka", "lily-of-the-valley": "lirio de valle", "lily of the valley": "lirio de valle",
    "orris root": "raíz de iris", "mandarin orange": "mandarina", "blood orange": "naranja sanguina",
    "bittersweet orange": "naranja agridulce", "bitter orange": "naranja amarga",
    "black currant": "grosella negra", "black pepper": "pimienta negra", "pink pepper": "pimienta rosa",
    "green tea": "té verde", "black tea": "té negro", "red berries": "bayas rojas",
    "red apple": "manzana roja", "green apple": "manzana verde", "dark chocolate": "chocolate negro",
    "bourbon vanilla": "vainilla bourbon", "madagascar vanilla": "vainilla de Madagascar",
    "french vanilla": "vainilla francesa", "peru balsam": "bálsamo del Perú", "peruvian balsam": "bálsamo del Perú",
    "bulgarian rose": "rosa búlgara", "turkish rose": "rosa turca", "damask rose": "rosa de damasco",
    "baie rose": "rosa de la bahía", "may rose": "rosa de mayo", "wild rose": "rosa silvestre",
    "rose absolute": "absoluto de rosa", "jasmine sambac": "jazmín sambac", "clary sage": "salvia",
    "atlas cedar": "cedro del atlas", "virginia cedar": "cedro de virginia", "atlantic cedar": "cedro del Atlántico",
    "italian bergamot": "bergamota italiana", "calabrian bergamot": "bergamota calabresa",
    "sicilian lemon": "limón siciliano", "amalfi lemon": "limón de Amalfi",
    "cashmere": "cachemir", "ambrette": "ambretón", "ambrette (musk mallow)": "ambretón",
    "amber from tunis": "ámbar de Túnez", "amber xtreme": "ámbar xtreme",
    "ylang ylang": "ylang-ylang", "cocoa butter": "mantequilla de cacao", "shea butter": "mantequilla de karité",
    "whipped cream": "nata montada", "buttercream": "crema de mantequilla", "cocoa bean": "grano de cacao",
    "coffee bean": "grano de café", "rose petals": "pétalos de rosa", "pink grapefruit": "pomelo rosa",
    "white grape": "uva blanca", "red grape": "uva tinta", "amalfi": "Amalfi", "eau de parfum": "Eau de Parfum",
    "italian": "italiano", "french": "francés", "spanish": "español", "turkish": "turco",
    "indian": "indio", "russian": "ruso", "egyptian": "egipcio", "moroccan": "marroquí",
    "brazilian": "brasileño", "mexican": "mexicano", "colombian": "colombiano", "peruvian": "peruano",
    "haitian": "haitiano", "japanese": "japonés", "chinese": "chino", "korean": "coreano",
    "cambodian": "camboyano", "laotian": "laotiano", "indonesian": "indonesio",
    "australian": "australiano", "canadian": "canadiense", "tahitian": "tahitiano",
    "californian": "californiano", "guatemalan": "guatemalteco", "cuban": "cubano",
    "portuguese": "portugués", "greek": "griego", "irish": "irlandés", "scottish": "escocés",
    "german": "alemán", "belgian": "belga", "swiss": "suizo", "himalayan": "himalayo",
    "sichuan": "sichuan", "nepal": "nepal", "sumatran": "sumatrés", "borneo": "borneo",
    "java": "java", "ceylon": "Ceilán", "philippine": "filipino", "caribbean": "caribeño",
    "african": "africano", "asian": "asiático", "oriental": "oriental", "scandinavian": "escandinavo",
"vintage": "vintage", "antique": "antiguo", "heritage": "herencia", "madagascar": "madagascar",
"madras": "madrás", "concrete": "hormigón"}
# Sufijos compuestos: «X blossom» -> «flor de X».
_PATTERNS = {
    "blossoms": "flores de {0}", "blossom": "flor de {0}", "flowers": "flores de {0}",
    "flower": "flor de {0}", "notes": "notas de {0}", "leaves": "hojas de {0}",
    "leaf": "hoja de {0}", "seeds": "semillas de {0}", "seed": "semilla de {0}",
    "beans": "habas de {0}", "bean": "haba de {0}", "wood": "madera de {0}",
    "tree": "árbol de {0}", "bark": "corteza de {0}", "honey": "miel de {0}",
    "cream": "crema de {0}", "syrup": "jarabe de {0}", "absolute": "absoluto de {0}",
    "lily": "lirio de {0}", "root": "raíz de {0}", "peel": "cáscara de {0}",
    "zest": "ralladura de {0}", "juice": "jugo de {0}", "water": "agua de {0}",
    "butter": "mantequilla de {0}", "sugar": "azúcar de {0}", "petals": "pétalos de {0}",
    "petal": "pétalo de {0}", "powder": "polvo de {0}", "smoke": "humo de {0}",
    "resin": "resina de {0}", "salt": "sal de {0}", "plum": "ciruela de {0}",
    "juices": "jugos de {0}", "syrups": "jarabes de {0}", "drops": "gotas de {0}",
    "pod": "vaina de {0}", "pods": "vainas de {0}", "shavings": "virutas de {0}",
    "peel ": "cáscara de {0}"}
_FEM_EXTRA = {"miel", "sal", "piel", "tierra", "corteza", "polar", "brasa", "carrera"}

def _pluralize(s):
    return s + ("es" if s and s[-1] in "aeiouz" else "s")
_PLURAL_N = {norm(_pluralize(v)) for v in _N.values()}

# ---- inversa (español -> inglés canónico) -----------------------------------
def _build_inverse():
    inv = {}
    def put(es, en):
        k, v = norm(es), norm(en)
        if k and k != v and k not in inv: inv[k] = v
    for en, es in ACC_ES.items(): put(es, en)
    for en, es in _N.items(): put(es, en); put(_pluralize(es), en)
    for en, (m, f, mp, fp) in _A.items(): put(m, en); put(f, en); put(mp, en); put(fp, en)
    for en, es in _PHRASES.items(): put(es, en)
    notes = {norm(k) for k in list(ACC_ES) + list(_N) + list(_A) + list(_PHRASES)}
    for es, toks in FAMILIES_ES_EN.items():
        for t in toks:
            if norm(t) not in notes: put(t, es)     # «vanilla» es una nota, no la familia «Gourmand»
        put(FAMILY_EN_ES[es], es)
    for es, en in list(LON_EN.items()) + list(SIL_EN.items()) + list(OCC_EN.items()) + list(SEA_EN.items()) + list(AXIS_EN.items()):
        put(es, en)
    for en, (es, _e) in GENDERS.items(): put(es, en)
    for suf, tpl in _PATTERNS.items():               # «flor de naranja» -> «orange blossom»
        for en, es in _N.items():
            if en == suf: continue
            put(tpl.format(es), f"{en} {suf}")
    return inv
_TO_EN = _build_inverse()

# ---- traducción del contenido de la base de datos ---------------------------
def _adj(n, fem, plur):
    m, f, mp, fp = _A[n]
    return fp if (fem and plur) else mp if plur else f if fem else m

def _lower(s):
    """Baja la inicial salvo en siglas y palabras que ya son minúsculas."""
    return s[0].lower() + s[1:] if s[:1].isupper() and not s.isupper() else s

def _es_noun(w, lower=True):
    """Forma española (singular/plural) de un sustantivo de nota."""
    n = norm(w)
    if n in _N: return _N[n]
    if " " not in n and n in ACC_ES: return _lower(ACC_ES[n]) if lower else ACC_ES[n]
    return None

def tr_note(label):
    """Traduce el nombre de una nota de la base de datos («White Musk» -> «Almizcle blanco»)."""
    if not label: return ""
    if not is_es(): return label
    raw = label.strip()
    n = norm(raw)
    if n in _PHRASES: return _PHRASES[n]
    if " " not in n:
        if n in _N: return _N[n]
        if n in ACC_ES: return _lower(ACC_ES[n])
    core = re.sub(r"\s*\([^)]*\)", "", raw).strip()        # «Agarwood (Oud)» -> «Agarwood»
    cn = norm(core)
    if cn != n:
        if cn in _PHRASES: return _PHRASES[cn]
        if " " not in cn and cn in _N: return _N[cn]
        if " " not in cn and cn in ACC_ES: return _lower(ACC_ES[cn])
    toks = [t for t in re.split(r"[\s\-/]+", core) if t]
    last = norm(toks[-1]) if len(toks) > 1 else ""
    if last in _PATTERNS:                                 # «Orange Blossom» -> «flor de naranja»
        base = " ".join(toks[:-1])
        if len(toks) == 2 and norm(base) in _A:            # «White Flowers» -> «flores blancas»
            return _PATTERNS[last].replace("de {0}", "{0}").format(_adj(norm(base), True, True))
        es = tr_note(base)
        if es and norm(es) != norm(base): return _PATTERNS[last].format(_lower(es))
    out = []
    for i, t in enumerate(toks):
        w = norm(t)
        nxt = norm(toks[i + 1]) if i + 1 < len(toks) else ""
        nx = _es_noun(nxt)                    # el sustantivo que sigue: marca género y número
        fem = bool(nx) and (nx.endswith("a") or nx in _FEM_EXTRA)
        plur = bool(nx) and nxt in _PLURAL_N
        cur = _es_noun(w)
        if w in _A: out.append(_adj(w, fem, plur))
        elif cur: out.append(_pluralize(cur) if plur else cur)
        elif w in _PHRASES: out.append(_PHRASES[w])
        elif w in _FN: out.append(_FN[w])
        else: out.append(t)
    if len(out) == 2 and _es_noun(toks[1]) and not _es_noun(toks[0]):   # «Russian Leather» -> «cuero ruso»
        out = [out[1], out[0]]
    res = " ".join(out)
    return res if any(c.isalpha() for c in res) else raw

def tr_accord(label):
    """Traduce el nombre de un acorde de la base de datos («White Floral» -> «Floral Blanca»).

    Acepta también el nombre ya traducido, para que la paleta y la etiqueta nunca se desincronicen.
    """
    if not label: return ""
    key = accord_key(label)
    if key in ACC_ES:
        return ACC_ES[key] if is_es() else key.title()
    return tr_note(label) if is_es() else label

def tr_family_word(w):
    """Traduce el nombre de una familia venga como venga: «Amaderada» o «woody» -> «Woody» / «Amaderada»."""
    if not w: return ""
    n = norm(w)
    for es, toks in FAMILIES_ES_EN.items():
        if n == norm(es) or n in [norm(t) for t in toks]:
            return es if is_es() else FAMILY_EN_ES[es]
    if n in ACC_ES and " " not in n:
        return ACC_ES[n] if is_es() else n.capitalize()
    return w

def tr_text(s, sep=", "):
    """Traduce texto de la base de datos con separadores (familias, acordes)."""
    if not s: return s or ""
    out = []
    for p in [x.strip() for x in re.split(r"[,;|]", s) if x.strip()]:
        head, _, tail = p.partition(":")
        h = norm(head)
        if is_es():
            if h in ACC_ES: p = ACC_ES[h] + ((":" + tail) if tail else "")
        else:
            canon = _TO_EN.get(h)
            if canon: p = FAMILY_EN_ES.get(canon, canon) + ((":" + tail) if tail else "")
        out.append(p)
    return sep.join(out)

def tr_gender(g):
    if not g: return ""
    pair = GENDERS.get(norm(g))
    return (pair[0] if is_es() else pair[1]) if pair else ""

def tr_field(value, table):
    """Traduce un valor canónico de la tabla indicada (ocasiones, estaciones, duración…). Acepta ES o EN."""
    if not value: return ""
    out = []
    for p in [x.strip() for x in str(value).split(",") if x.strip()]:
        if is_es():   # el valor canónico ya es español; si viene en inglés, se busca su clave
            out.append(next((k for k, v in table.items() if norm(v) == norm(p)), p))
        else:
            out.append(table.get(p) or next((v for k, v in table.items() if norm(k) == norm(p)), None) or p)
    return ", ".join(out)

def tr_occasions(v): return tr_field(v, OCC_EN)
def tr_seasons(v): return tr_field(v, SEA_EN)
def tr_longevity(v): return tr_field(v, LON_EN)
def tr_sillage(v): return tr_field(v, SIL_EN)
def tr_axis(w):
    """Traduce un extremo de los ejes del perfil: «dulce» -> «Sweet», «amaderado» -> «Woody»."""
    if not w: return ""
    k = AXIS_EN.get(norm(w))
    if not k: return w
    return w if is_es() else k.capitalize()

def canon_tokens(value, table):
    """Vuelve a la forma canónica lo que el usuario elige o escribe: «summer, winter» -> ['verano', 'invierno']."""
    vals = value if isinstance(value, (list, tuple)) else [value]
    out = []
    for p in vals:
        n = norm(p)
        if not n: continue
        out.append(next((k for k, v in table.items() if n in (norm(k), norm(v))), p))
    return out

def _avg(v):
    m = re.search(r"average:([\d.]+)", str(v or ""))
    return float(m.group(1)) if m else None

def _canon_lon(a):
    return "Corta" if a < 2.5 else "Moderada" if a < 3.5 else "Larga" if a < 4.2 else "Eterna"
def _canon_sil(a):
    return "Suave" if a < 1.75 else "Moderada" if a < 2.5 else "Fuerte" if a < 3.25 else "Enorme"

def longevity_label(v):
    """«average:3.8|histogram» (el formato en crudo que trae el dataset) -> etiqueta traducida."""
    a = _avg(v)
    if a is None: return tr_longevity(v) if is_es() else (v or "")
    k = _canon_lon(a)
    return k if is_es() else LON_EN[k]
def sillage_label(v):
    a = _avg(v)
    if a is None: return tr_sillage(v) if is_es() else (v or "")
    k = _canon_sil(a)
    return k if is_es() else SIL_EN[k]


def _variant_rebuild(n):
    """«flor de naranja» -> «orange blossom»: reconstruye la nota en inglés a partir de sus partes."""
    for suf, tpl in _PATTERNS.items():
        pre = tpl.split("{0}")[0].strip()
        if not pre or not n.startswith(pre + " "): continue
        base = n[len(pre) + 1:].strip()
        en = _TO_EN.get(base)
        if en: return f"{en} {suf}"
    return None

def en_variants(word):
    """Variantes normalizadas de una palabra buscada, para que el buscador acierte en los dos idiomas."""
    n = norm(word)
    if not n: return []
    out = [n]
    if n in _TO_EN: out.append(_TO_EN[n])
    if " " in n:                                    # «flor de naranja» -> «orange blossom»
        reb = _variant_rebuild(n)
        if reb: out.append(reb)
    return list(dict.fromkeys(out))

def chat_keywords(es, en):
    """Une en ambos idiomas las palabras clave de una intención (separadas por comas o espacios), para el asistente."""
    return "|".join(re.escape(w) for w in (re.split(r"[,\s]+", norm(es)) + re.split(r"[,\s]+", norm(en))) if w)