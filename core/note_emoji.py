"""Emoji por familia de nota olfativa.

Las notas de Fragrantica son miles de nombres distintos («Sicilian Lemon», «Madagascar Vanilla»,
«Flor de naranjo»…), así que en lugar de una tabla nota -> emoji se agrupan por familias: cada regla
es un emoji y una lista de palabras clave (inglés y español, sin acentos). Gana la PRIMERA regla que
coincida, por eso las específicas van antes que las genéricas («orange blossom» -> flor, antes de
«orange» -> naranja; «peppermint» -> menta, antes de «pepper» -> pimienta).

    from note_emoji import note_emoji
    note_emoji("Madagascar Vanilla")   # 🍦
    note_emoji("Naranja")              # 🍊
    note_emoji("algo desconocido")     # ✨  (nunca devuelve vacío)
"""
import re, unicodedata

FALLBACK = "✨"

# (emoji, "palabra|otra|raiz\w*|frase con espacios") — se busca como palabra completa; `\w*` admite sufijos.
_RULES = [
    # --- vainilla (primero: «vanilla orchid», «vanilla bean» son vainilla) ---
    ("🍦", r"vanill\w*|vainill\w*|ice cream|helado|gelato"),
    # --- compuestos que contienen otra palabra más genérica ---
    ("🌲", r"juniper\w*|enebro|fir balsam|balsam fir|abeto"),
    ("🪵", r"cashmere woods?|cachemir woods?"),
    # --- flores ---
    ("🌹", r"roses?|rosas?|damask"),
    ("🌷", r"lil(?:y|ies)|lirio\w*|muguet|tulip\w*|tulipan\w*"),
    ("💜", r"lavand\w*|lavender|violet\w*|violeta\w*|heliotrop\w*|wisteria|glicina"),
    ("🌸", r"cherry blossom|sakura|flor de cerezo|peon\w*|peony|tuberose|tuberosa|nardo|iris|orris|lotus|loto|nenufar\w*|camell?ia|"
           r"magnolia\w*|cyclamen|ciclamen|poppy|amapola|lilac|lila|hyacinth|jacinto|orchid\w*|orquide\w*|hibiscus|hibisco|mimosa|carnation|clavel\w*"),
    ("🌼", r"jasmin\w*|jazmin\w*|ylang\w*|neroli|honeysuckle|madreselva|chamomile|manzanilla|osmanthus|narcis\w*|daffodil|"
           r"freesia|frangipani|plumeria|gardenia|tiare|champaca|linden|tilo|elderflower|sunflower|girasol|marigold|"
           r"blossom\w*|azahar|flor de \w+|buttercup|calendula|immortelle|inmortal\w*|helichrysum|pollen|polen"),
    ("🌸", r"floral\w*|flower\w*|flor|flores|bouquet|petal\w*|petalo\w*"),
    # --- verdes que contienen otra palabra («lemongrass» antes de «lemon») ---
    ("🌿", r"lemon ?grass|citronel\w*|hierba luisa"),
    # --- cítricos y frutas ---
    ("🍊", r"bigarade"),
    ("🍋", r"lemon\w*|limon\w*|limonada|limes?|lima|bergamot\w*|citron|cedrat|yuzu|verbena|calamansi"),
    ("🍊", r"orang\w*|naranj\w*|mandarin\w*|tangerin\w*|clementin\w*|grapefruit|pomelo|toronja|petitgrain|kumquat|tangelo|"
           r"citrus\w*|citric\w*|citricos?"),
    ("🍎", r"apples?|manzana\w*|pomme|pomegranate|granada"),
    ("🍐", r"pears?|peras?|quinces?|membrillo"),
    ("🍑", r"peach\w*|melocoton\w*|durazno\w*|apricot\w*|albaricoque\w*|nectarin\w*|plums?|ciruela\w*|prunes?|damson"),
    ("🍒", r"cherr(?:y|ies)|cereza\w*|guinda\w*|amarena|kirsch"),
    ("🍓", r"strawberr\w*|fresa\w*|raspberr\w*|frambuesa\w*|red fruits?|red berr\w*|frutos? rojos?|berr(?:y|ies)|bayas?|"
           r"wild berr\w*|cranberr\w*|mulberr\w*|bramble|zarzamora"),
    ("🍇", r"grapes?|uvas?|black ?currant\w*|currants?|cassis|grosella\w*|blackberr\w*|blueberr\w*|arandano\w*|moras?|"
           r"figs?|higos?|raisins?|pasas?|tamarind\w*"),
    ("🍍", r"pineapple\w*|pina|ananas|tropical\w*|exotic fruits?"),
    ("🥭", r"mango\w*|papaya|guava|guayaba|passion ?fruit|maracuya|lychee|litchi|lichi|pitaya|dragon ?fruit"),
    ("🥥", r"coco|coconut\w*"),
    ("🍌", r"banana\w*|platano\w*"),
    ("🍈", r"melon\w*"),
    ("🍉", r"watermelon|sandia"),
    ("🥝", r"kiwi\w*"),
    ("🍅", r"tomato\w*|tomate\w*"),
    ("🥒", r"cucumber\w*|pepino\w*"),
    ("🥕", r"carrot\w*|zanahoria\w*"),
    ("🍓", r"jam|mermelada|compota|compote"),
    ("🍎", r"fruit\w*|fruta\w*|frutal\w*|frutos?"),
    ("🍫", r"chocolat\w*|cacao|cocoa|mocha|brownie"),
    ("☕", r"coffee|cafe|espresso|cappuccino|latte"),
    ("🌰", r"almond\w*|almendr\w*|hazelnut\w*|avellana\w*|chestnut\w*|castana\w*|walnut\w*|pecan\w*|pistach\w*|nuts?|nuez|nueces|"
           r"peanut\w*|cacahuete\w*|marzipan|mazapan|tonka|coumarin\w*|cumarin\w*|beans?|habas?"),
    # --- golosas y bebidas ---
    ("🍵", r"tea|teas|te verde|te negro|te blanco|matcha|mate|yerba mate|rooibos|earl grey|chai|tisana"),
    ("🍯", r"honey\w*|miel|beeswax|cera de abeja|nectar|syrup|jarabe|sirope|maple|arce"),
    ("🍬", r"caramel\w*|toffee|candy|candies|sugar\w*|azucar\w*|praline\w*|nougat|turron|cotton candy|bubble ?gum|chicle|"
           r"marshmallow|lollipop|piruleta|sweet\w*|dulce\w*|licorice|liquorice|regaliz|sorbet|jelly|gummy|fudge|gourmand\w*"),
    ("🍿", r"popcorn|palomitas"),
    ("🌽", r"corn|maiz"),
    ("🍰", r"cake|pastr\w*|bakery|brioche|biscuit\w*|cookie\w*|galleta\w*|bread|pan|toast\w*|dough|masa|pie|tarta\w*|pastel\w*|"
           r"croissant|waffle|gofre|crumble|custard|flan|pudding"),
    ("🥛", r"milk\w*|leche|cream\w*|crema\w*|lacton\w*|lactic\w*|lacteo\w*|butter\w*|mantequilla|yogurt|yogur|cheese|queso|ghee"),
    ("🍷", r"wine\w*|vino|mosto|merlot|sherry|jerez|vermouth|port"),
    ("🍾", r"champagn\w*|prosecco|cava|sparkling|espumoso"),
    ("🍸", r"gin|vodka|absinth\w*|cocktail\w*|martini|mojito|negroni|campari|aperol|spritz|margarita"),
    ("🥃", r"whisk\w*|bourbon|cognac|brandy|rum|ron|scotch|armagnac|tequila|mezcal|liquor|licor\w*|spirits?|alcohol\w*|sake"),
    ("🍺", r"beer|cerveza|hops?|lupulo|malt\w*|ale|stout"),
    ("🥤", r"cola|coca[- ]?cola|soda|soft drink|refresco"),
    # --- menta y frío (antes de «pepper» por «peppermint») ---
    ("🌱", r"mint\w*|menta\w*|spearmint|peppermint|hierbabuena|yerbabuena"),
    ("❄️", r"menth\w*|mentol|ice|icy|hielo|cold|frio|frost\w*|snow\w*|nieve|glaci\w*|polar|arctic|artico|cooling|frozen"),
    # --- especias ---
    ("🌶️", r"pepper\w*|pimienta\w*|pimiento|chil(?:i|e|li)\w*|cayenne|paprika|pimenton|ginger\w*|jengibre|szechuan|sichuan|"
            r"spic(?:e|es|y|ed)|especia\w*|especiad\w*|cinnamon\w*|canela|clove\w*|clavo|nutmeg|nuez moscada|cardamom\w*|"
            r"cardamono|saffron|azafran|cumin|comino|anis|anise\w*|star anise|badian\w*|fennel|hinojo|turmeric|curcuma|"
            r"caraway|alcaravea|allspice|sumac"),
    ("🧂", r"salt\w*|sal|salin\w*|saline"),
    # --- hongos, humo y fuego (antes que maderas: «birch tar», «smoked woods») ---
    ("🌵", r"cactus|cactus|agave|nopal|prickly pear|chumbera"),
    ("🎃", r"pumpkin|calabaza"),
    ("🍄", r"mushroom\w*|champinon\w*|seta|setas|hongo\w*|truffle\w*|trufa\w*|fung\w*|moldy|moho"),
    ("🔥", r"soot|hollin|smok\w*|humo|burnt|burned|quemad\w*|fire\w*|fuego|flame|llama|charcoal|carbon|ash|ashes|ceniza\w*|campfire|"
           r"fogata|bonfire|hoguera|tar|alquitran|bbq|barbecue|roast\w*|tostad\w*|ember|brasa|cade|gunpowder|polvora|matchstick|"
           r"firewood|cerilla\w*"),
    # --- resinas, incienso, ámbar ---
    ("🕯️", r"incens\w*|incienso|frankincens\w*|olibanum|elemi|myrrh\w*|mirra|church|iglesia|candle\w*|vela|velas|wax\w*|cera|copal"),
    ("🔶", r"mastic\w*|almaciga|amber\w*|ambar\w*|ambrox\w*|ambroxan|ambrett\w*|labdan\w*|benzoin|benjui|opoponax|styrax|storax|tolu|balsam\w*|"
           r"balsamic\w*|resin\w*|resina\w*|cistus|jara"),
    # --- almizcle, polvo, jabón, telas, cuero ---
    ("☁️", r"musk\w*|almizcl\w*|powder\w*|polvo\w*|talc\w*|talco|cashmeran|skin"),
    ("🧼", r"soap\w*|jabon\w*|clean\w*|limpi\w*|laundry|colada|detergent\w*|shampoo|champu|lather|aldehyd\w*|aldehid\w*"),
    ("🧥", r"leather\w*|cuero\w*|suede|gamuza|ante|piel|pieles|saddle"),
    ("🐾", r"hyrax|animal\w*|civet\w*|castore\w*|barnyard|cuadra|stable|horse|caballo|dung|estiercol|sweat|sudor|fur"),
    ("🧶", r"cotton\w*|algodon|linen\w*|lino|silk\w*|seda|cashmere|cachemir\w*|wool\w*|lana|velvet\w*|terciopelo|satin\w*|"
           r"fabric\w*|tela|textile\w*|cloth\w*|tejido|sheets?|sabanas?|towel\w*|toalla"),
    # --- musgos, hierbas, verdes ---
    ("🌿", r"angelica|cypriol|cipriol|nagarmotha|davana|ivy|hiedra|aloe\w*|celery|apio|moss\w*|musgo\w*|oak ?moss|lichen|liquen|basil\w*|albahaca|thym\w*|tomillo|rosemar\w*|romero|sage|salvia\w*|"
           r"oregano|marjoram|mejorana|tarragon|estragon|artemisi\w*|wormwood|ajenjo|herb\w*|hierba\w*|yerba\w*|aromatic\w*|"
           r"aromatico\w*|coriander|cilantro|dill|eneldo|parsley|perejil|chives?|laurel|bay leaf|geranium\w*|geranio\w*|"
           r"patchoul\w*|pachul\w*|patchuli|eucalypt\w*|camphor\w*|alcanfor|ruda|tea tree"),
    # --- árboles y maderas ---
    ("🌲", r"poplar|alamo|hemlock|cedar\w*|cedro\w*|pines?|pinos?|pine needles?|fir|abeto|spruce|cypress|cipres\w*|juniper|enebro|conifer\w*|"
           r"forest\w*|bosque\w*|evergreen|hinoki|thuja|larch|alerce|christmas tree|redwood|sequoia"),
    ("🪵", r"akigalawood|ebony|ebano|mahogany|caoba|amaderad\w*|wood\w*|madera\w*|sandal\w*|oud|agarwood|aloeswood|aoud|guaia\w*|guayaco|teak|teca|oak|roble|birch\w*|abedul|"
           r"rosewood|palo de rosa|palo santo|bamboo|bambu|driftwood|iso e super"),
    ("🍂", r"tobacco\w*|tabaco|cigar\w*|cigarette|dry leaves|hojas secas|autumn|otono|fall leaves"),
    ("🌾", r"papyrus|papiro|vetiver\w*|vetyver|hay|heno|straw|paja|wheat|trigo|oats?|avena|barley|cebada|rice|arroz|grain\w*|cereal\w*|tatami"),
    ("🍃", r"leaf|leaves|hoja\w*"),
    ("🌱", r"rhubarb|ruibarbo|green\w*|verde\w*|grass\w*|cesped|galbanum|stem\w*|tallo\w*|sprout\w*|brote\w*|clover|trebol|sap|savia"),
    # --- tierra, mineral, metal ---
    ("🌍", r"dust\w*|earth\w*|tierra|terros\w*|soil|dirt\w*|mud|barro|clay|arcilla|sand|sands|arena|arenas|petrichor|humus|root\w*|raiz|raices"),
    ("🪨", r"mineral\w*|stone\w*|piedra\w*|rock\w*|roca\w*|flint|pedernal|concrete|hormigon|cement\w*|asphalt\w*|asfalto|chalk|tiza|"
           r"slate|pizarra|marble|marmol|granite|granito|quartz|cuarzo"),
    ("💎", r"crystal\w*|cristal\w*|diamond\w*|diamante\w*|gem|gems|glass|vidrio"),
    ("🔩", r"metal\w*|iron\w*|hierro|steel|acero|copper|cobre|silver|plata|rust\w*|oxido|aluminum|aluminium|brass|bronze|zinc|coins?|monedas?"),
    # --- aire, agua, sol ---
    ("💨", r"ozon\w*|air|airy|aire|wind\w*|viento|breeze|brisa|sky|cielo|clouds?|vapor|vapour|steam"),
    ("💧", r"seaweed|algae|algas?|kelp|water\w*|agua\w*|aquatic\w*|acuatic\w*|marine\w*|marin\w*|sea|mar|ocean\w*|oceano|rain\w*|lluvia|dew|rocio|"
           r"fresh\w*|fresc\w*|splash|wet|humed\w*|damp|river|rio|lake|lago|calone|cool"),
    ("☀️", r"sun|sunny|sol|solar\w*|suntan|sunscreen|bronce\w*|tanning|summer|verano|beach\w*|playa\w*|desert\w*|desierto\w*|hot|heat\w*|calor"),
    ("🌴", r"palm\w*|palma\w*|palmera\w*|dates?|datil\w*"),
    # --- papel y sintético ---
    ("📖", r"paper\w*|papel|books?|libros?|library|biblioteca|ink|tinta|pencil|lapiz|cardboard|carton|parchment|pergamino"),
    ("🧪", r"synthetic\w*|sintetic\w*|molecul\w*|hedione|ethyl\w*|chemical\w*|quimic\w*|solvent\w*|disolvente|paint\w*|"
           r"pintura|varnish|barniz|glue|pegamento|pvc|plastic\w*|rubber|caucho|goma|latex|vinyl|vinilo|tape|cinta|gasoline|"
           r"gasolina|petrol|diesel|oil\w*|aceite\w*|petroleum|kerosene|queroseno|industrial|ethanol|etanol|acetone|acetona|nail polish"),
]

_COMPILED = [(emoji, re.compile(r"\b(?:" + pat + r")\b")) for emoji, pat in _RULES]
_cache = {}

def _norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("_", " ")).strip()

def note_emoji(name):
    """Emoji de la familia a la que pertenece la nota. Siempre devuelve uno (✨ si no encaja en ninguna)."""
    key = _norm(name)
    hit = _cache.get(key)
    if hit is None:
        hit = next((e for e, rx in _COMPILED if rx.search(key)), FALLBACK)
        _cache[key] = hit
    return hit
