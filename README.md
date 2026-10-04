# Perfúmappte

> ## ⚠️ Uso NO comercial
> Perfúmappte es un proyecto personal y gratuito. **Su uso es exclusivamente no comercial**: puedes usarlo, estudiarlo y modificarlo para fines
> personales, de ocio, educativos o de investigación, pero **no puedes venderlo, cobrar por él ni usarlo en un producto o servicio comercial**.
> Se distribuye bajo la licencia [PolyForm Noncommercial 1.0.0](LICENSE).

Tu colección de perfumes en el escritorio: descubre qué ponerte según la ocasión, la hora o la estación, prueba combinaciones (layering) y habla con **Góngora**, un perfumista con IA.

## Apartados
- **Mi colección** – tus perfumes (propiedad y deseados) con tres pestañas: *Perfumes*, *Combinaciones favoritas* y *Mis gustos* (gráficos).
- **Descubrimientos** – toda la base de datos filtrable por texto, género, estado, familia olfativa y notas. Aquí está *Actualizar perfumes*.
- **Recomendaciones** – filtros por ocasión, hora y estación (y un perfume concreto) sobre tu colección, con *opciones de layering* y *de compra*.
- **Góngora** – el botón flotante abre el chat con el perfumista (IA de Google Gemini).
- **Versiones** – abajo a la izquierda: versión instalada, novedades y actualización con un clic.

## Instalar en Windows (recomendado)
1. Descarga `Perfumappte-Setup-X.Y.Z.exe` de la página de [Releases](../../releases/latest) y ejecútalo (no necesita administrador).
   Windows SmartScreen puede avisar porque el instalador no está firmado: *Más información → Ejecutar de todas formas*.
2. El asistente te guía en dos pasos:
   - **Kaggle (obligatorio en las Releases públicas)**: la base de datos de perfumes se descarga de Kaggle la primera vez. Necesitas una cuenta gratuita:
     1. Entra en [kaggle.com](https://www.kaggle.com) (crea una cuenta o inicia sesión).
     2. Ve a [Settings → API](https://www.kaggle.com/settings/api).
     3. Pulsa **«Create Legacy API Key»**. **Es la única opción que descarga el archivo `kaggle.json`** (las demás no sirven).
     4. En el instalador elige ese archivo: se guarda por ti en `C:\Users\TU_USUARIO\.kaggle\kaggle.json`.
   - **Clave de Góngora (opcional)**: crea una clave gratuita en [Google AI Studio](https://aistudio.google.com/apikey) y pégala. Sin ella, Góngora
     responde solo con reglas básicas (sin IA). Se puede añadir después con el ⚙ del chat.
3. Abre *Perfúmappte* desde el menú Inicio. Al arrancar por primera vez descarga la base de datos (unos minutos).

Tus datos (base de datos, imágenes, clave) se guardan en `%LOCALAPPDATA%\Perfumappte`; el desinstalador te pregunta si quieres borrarlos.
Instalación desatendida: `Perfumappte-Setup-X.Y.Z.exe /VERYSILENT /GEMINIKEY=... /KAGGLEFILE=C:\ruta\kaggle.json`.

### Actualizaciones de la aplicación
Cuando se publica una versión nueva en GitHub, la app lo detecta al abrirse (como mucho una vez al día) y muestra la ventana **Versiones** con las
novedades y el botón *Actualizar*: descarga el instalador de esa Release (comprobando su huella SHA-256), se instala sola conservando tus datos y
se vuelve a abrir. También puedes abrirla cuando quieras desde el número de versión de la barra lateral.

## Ejecutar desde el código fuente
Requiere Python 3.10 o superior (probado con 3.12 y 3.14).

    git clone https://github.com/marinaescobar/perfumappte.git
    cd perfumappte
    python -m venv venv && venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

Sin base de datos, la app te guía para conseguirla: necesitas el `kaggle.json` de arriba (*Create Legacy API Key*) en `C:\Users\TU_USUARIO\.kaggle\`;
después pulsa *Actualizar perfumes* en Descubrimientos (o ejecuta `python -m core.updater`). La base se actualiza sola cada 7 días si hay credenciales.
- Importar a mano un archivo (.jsonl, .json o .csv): `python -m core.db archivo.jsonl`; para revisar cómo se lee: `python -m core.db --inspect archivo.jsonl`.
- Clave de Góngora: variable de entorno `GEMINI_API_KEY` o el ⚙ del chat.

## Góngora y privacidad
- Usa la API de **Google Gemini** con tu propia clave (hay capa gratuita, con una cuota diaria pequeña por modelo; si se agota uno, prueba el siguiente).
- Cada pregunta envía a Google tu colección y tu lista de deseados como contexto. En la capa gratuita Google puede usar las consultas para mejorar sus productos.
- La clave se guarda solo en tu equipo (`gemini.key` o la base de datos local). **Nunca subas tu `perfumappte.db`, `gemini.key` ni `kaggle.json`**: el `.gitignore` ya los excluye.

## Idiomas
Español e inglés (selector arriba a la derecha, con banderas). La base de datos guarda los valores originales y se traducen al mostrarlos;
el buscador acepta los dos idiomas («vainilla» y «vanilla» encuentran lo mismo).

## Estructura del proyecto
    main.py              arranque (python main.py; --selftest comprueba el ejecutable)
    core/                lógica sin interfaz: db, recommender, gongora (IA), i18n, updater (Kaggle), selfupdate (versiones), paths, version
    ui/                  interfaz PyQt6: mainwindow, widgets, cards, chat, versions, charts, logo, avatar, theme y pages/
    tools/               make_assets.py (imágenes de assets/) y build_installer.py (instalador)
    installer/           script de Inno Setup
    assets/              icono, logotipo y avatar de Góngora
    .github/workflows/   publicación automática de Releases

## Para quien mantiene el proyecto: publicar una versión
1. En `core/version.py` pon tu repositorio real en `GITHUB_REPO` (`usuario/repositorio`) y sube `VERSION` (por ejemplo `1.1.0`).
2. Sube los cambios y crea la etiqueta: `git tag v1.1.0 && git push --tags`.
3. GitHub Actions (`.github/workflows/release.yml`) construye `Perfumappte-Setup-1.1.0.exe` **sin la base de datos** y lo adjunta a la Release.
   Escribe las novedades en la descripción de la Release: es lo que verán los usuarios en la ventana *Versiones*.
4. Para construir en tu equipo: `pip install -r requirements-dev.txt` + `winget install JRSoftware.InnoSetup` y `python -m tools.build_installer`
   Con `--no-seed` se genera `Perfumappte-Setup-X.Y.Z.exe` (el que se publica); sin esa opción se incluye una copia **limpia** de tu base de datos
   (sin colección ni claves) y el archivo se llama `...-con-base-de-datos.exe`, solo para uso personal.

## Herramientas de desarrollo
    python -m pyflakes main.py core ui tools                  # nombres sin definir e imports sin usar
    python -m vulture main.py core ui --min-confidence 80     # código sin uso

---

## English summary
**Perfúmappte** is a free desktop app (Windows, PyQt6) to manage your perfume collection, get recommendations by
occasion/time/season, try layering combinations and chat with *Góngora*, an AI perfumer (Google Gemini, bring your own key).

**Non-commercial use only** ([PolyForm Noncommercial 1.0.0](LICENSE)). Not affiliated with Kaggle or Google.

Install from the [Releases](../../releases/latest) page. The wizard asks for your Kaggle `kaggle.json` (required to download the perfume database —
on kaggle.com/settings/api click **“Create Legacy API Key”**, the only option that gives you that file) and, optionally, a free Gemini API key.
New versions are announced inside the app (**Versions** panel) and can be installed with one click. Run from source with `pip install -r requirements.txt && python main.py`.
