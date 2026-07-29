# Remote Jobs Bot

MVP en Python que recopila ofertas remotas de desarrollo de software a nivel mundial desde APIs públicas gratuitas (Remotive y Arbeitnow) y las envía a Telegram. Se ejecuta cada 30 minutos mediante GitHub Actions.

Sin dependencias de pago, sin scraping de LinkedIn/Indeed/Computrabajo, sin servicios externos obligatorios.

## Características

- Fuentes: Remotive y Arbeitnow (solo APIs públicas gratuitas).
- Filtros configurables por palabras clave y por modalidad remota.
- Normalización a un esquema único: `título, empresa, ubicación, modalidad, salario, fuente, URL, fecha`.
- Deduplicación entre ejecuciones mediante archivo JSON local.
- Mensajes Telegram con escape MarkdownV2 y división segura por límite de caracteres.
- Manejo de errores por fuente: si una fuente cae, las demás siguen ejecutándose.
- Timeouts y reintentos razonables.
- Modo `dry-run` para probar sin credenciales.
- Tests con la stdlib `unittest`.
- Persistencia entre ejecuciones en GitHub Actions vía `actions/cache` (gratuito).

## Estructura

```
bot/
├── src/
│   ├── config.py            # Carga de variables de entorno
│   ├── dedupe.py            # Estado y deduplicación
│   ├── filters.py           # Filtro de remoto y keywords
│   ├── main.py              # Punto de entrada
│   ├── models.py            # Modelo JobOffer
│   ├── telegram.py          # Formateo, escape y envío a Telegram
│   ├── utils.py             # HTTP con reintentos
│   └── sources/
│       ├── base.py
│       ├── remotive.py
│       └── arbeitnow.py
├── tests/                   # Pruebas unitarias (stdlib unittest)
├── .github/workflows/bot.yml
├── .env.example
├── .gitignore
├── pyproject.toml           # Config de ruff/mypy
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Crear el bot de Telegram y obtener el chat ID

### 1. Crear el bot con BotFather

1. Abre Telegram y busca `@BotFather`.
2. Envía `/newbot`.
3. Asigna un nombre visible (por ejemplo `Remote Jobs Bot`).
4. Asigna un username único terminado en `bot` (por ejemplo `remote_jobs_xyz_bot`).
5. BotFather te responderá con un **token** con formato `123456789:AA...`. Guárdalo, es tu `TELEGRAM_BOT_TOKEN`.

### 2. Obtener tu chat ID

Tienes varias opciones, todas gratuitas:

**Opción A — Mensaje directo (chat privado con el bot):**

1. En Telegram, busca tu bot por su `@username` y envíale cualquier mensaje (por ejemplo `/start`).
2. Abre en el navegador:
   ```
   https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   ```
3. En el JSON resultante, busca el campo `chat.id` dentro de `message.chat`. Ese número (puede ser negativo si es un grupo) es tu `TELEGRAM_CHAT_ID`.

**Opción B — Grupo o canal:**

1. Añade el bot al grupo o canal.
2. Si es un canal público, usa el `@username` del canal como `chat_id` (por ejemplo `@mi_canal`).
3. Si es un grupo/canal privado, obtén el `chat.id` con `getUpdates` igual que en la opción A (será un número negativo para grupos).

> Importante: el bot necesita poder enviar mensajes. En canales, asegúrate de que sea administrador con permiso de publicar.

## Configurar secretos en GitHub

1. Sube el repositorio a GitHub.
2. Ve a `Settings → Secrets and variables → Actions`.
3. Crea dos secretos:
   - `TELEGRAM_BOT_TOKEN`: el token que te dio BotFather.
   - `TELEGRAM_CHAT_ID`: el id de chat del paso anterior.

El workflow `.github/workflows/bot.yml` ya los lee automáticamente.

## Ejecución local

### Requisitos

- Python 3.10 o superior (probado en 3.12 y 3.14).

### Instalar dependencias de desarrollo (opcional)

```
python -m pip install -r requirements-dev.txt
```

Para ejecutar el bot no necesitas instalar nada: solo usa la biblioteca estándar.

### Modo dry-run (sin credenciales)

```
BOT_DRY_RUN=true python -m src.main
```

Esto imprimirá por pantalla los mensajes que se enviarían a Telegram, sin hacer llamadas reales.

### Ejecución real

Configura `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` como variables de entorno y ejecuta:

```
python -m src.main
```

En PowerShell puedes exportar las variables directamente:

```
$env:TELEGRAM_BOT_TOKEN = "123456789:AA..."
$env:TELEGRAM_CHAT_ID = "-1001234567890"
python -m src.main
```

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | _obligatorio_ | Token del bot de Telegram. |
| `TELEGRAM_CHAT_ID` | _obligatorio_ | ID del chat o canal destino. |
| `BOT_KEYWORDS` | Desarrollo de software | Lista separada por comas; filtra ofertas cuyo título/empresa/ubicación contenga alguna (case-insensitive). Vacío = sin filtro. |
| `BOT_REQUIRE_REMOTE` | `true` | Si es `true`, solo se aceptan ofertas detectadas como remotas. |
| `BOT_ONLY_JUNIOR` | `true` | Si es `true`, filtra ofertas junior/entry-level (0-3 años) y excluye senior/lead/principal/staff. |
| `BOT_REQUEST_TIMEOUT` | `20` | Timeout HTTP en segundos. |
| `BOT_REQUEST_RETRIES` | `3` | Reintentos por fuente. |
| `BOT_STATE_PATH` | `state.json` | Ruta del archivo de estado (dedupe). |
| `BOT_MAX_OFFERS` | `30` | Máximo de ofertas nuevas a enviar por ejecución. |
| `BOT_TG_LIMIT` | `4000` | Límite de longitud por mensaje (Telegram admite hasta 4096). |
| `BOT_DRY_RUN` | `false` | Si es `true`, imprime en lugar de enviar. |
| `BOT_LOG_LEVEL` | `INFO` | Nivel de logging. |

## Ejecución automática cada 30 minutos

El workflow `.github/workflows/bot.yml` se dispara con la expresión cron `*/30 * * * *` (cada 30 minutos) y también manualmente desde la pestaña `Actions` (`workflow_dispatch`).

El estado (`state.json`) se persiste entre ejecuciones usando `actions/cache`, por lo que no se necesita un servicio externo ni credenciales adicionales en el repositorio.

## Tests, lint y typecheck

Los tests usan `unittest` (stdlib). Para ejecutarlos:

```
python -m unittest discover -s tests -v
```

Lint:

```
ruff check src tests
```

Typecheck:

```
mypy src
```

## Notas de diseño

- **Persistencia**: GitHub Actions es ephemeral; cada ejecución parte de un runner limpio. Por eso el estado se guarda en `state.json` y se restaura/guarda con `actions/cache`. El archivo tiene un tope de 5000 IDs vistos (FIFO) para no crecer indefinidamente.
- **Escape y splitting**: los mensajes usan `MarkdownV2`, escapando `_ * [ ] ( ) ~ \` > # + - = | { } . !`. Los mensajes se dividen por límite seguro respetando saltos de línea.
- **Errores por fuente**: cada fuente se aísla con `try/except` en `main.collect`; un fallo no detiene al resto. El nivel de log y los reintentos son configurables.
- **Filtros**: la detección de remoto es robusta (modalidad `Remote`, o coincidencia en `location`/`title`/`company` con patrones `remote`, `remoto`, `teletrabajo`, `WFH`, etc.).

## Licencia

MIT.