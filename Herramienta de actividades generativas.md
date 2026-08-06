# Módulo "Generador de Actividades Lúdicas" — Diseño y Plan de Implementación

**Fecha:** 2026-08-04
**Estado:** Diseño aprobado por el usuario (conversación en sesión) · Fase 2 bloqueada por documentos de ejemplo pendientes
**Alcance:** Nuevo módulo del aplicativo `Generador_Contenido` (tercera tarjeta del menú, junto a Validador y Generador)

---

## 1. Resumen

Se solicitó evaluar la viabilidad de un nuevo tipo de generación de contenido, basado en el sílabo, que cubra: crucigramas, rompecabezas, juegos interactivos (opcional), juegos lúdicos, figuras geométricas para imprimir (hojas de relación, discriminación visual, correspondencia, formas y figuras), hojas de trabajo generales y orientación espacial.

**Conclusión de viabilidad: SÍ es factible.** La arquitectura actual del backend (`app/services/generation/orchestrator.py` + `app/mcp_server/tools/*`) ya implementa exactamente el patrón necesario — un LLM elige una "herramienta" tipada (Pydantic) y una función Python determinista la renderiza a HTML/SVG, nunca al revés. Extender esto con más herramientas es aditivo, no un rediseño.

Lo pedido se descompone en **dos familias técnicamente distintas**, por lo que el trabajo se divide en dos fases independientes:

- **Fase 1** — Crucigrama + rompecabezas de lógica/relación. Reutiliza 100% el parser de sílabo que ya existe. Riesgo bajo, se puede construir de inmediato.
- **Fase 2** — Hojas de Educación Inicial (figuras geométricas, discriminación visual, correspondencia, orientación espacial). Requiere un parser nuevo para la plantilla de planificación de Educación Inicial (aún no vista) y componentes de dibujo/arrastre en pantalla. Riesgo medio-alto, bloqueada hasta contar con documentos de ejemplo reales.

Quedan **fuera de alcance** (por falta de definición concreta, no por imposibilidad): rompecabezas tipo jigsaw de imagen (piezas encajables) y "juegos interactivos" sin especificar más allá de lo ya cubierto.

---

## 2. Decisiones tomadas durante el diseño

| Pregunta | Decisión |
|---|---|
| Nivel educativo de las hojas de Educación Inicial | Educación Inicial / primeros años (a confirmar con documentos reales) |
| Origen del contenido de entrada | Se sube el sílabo/documento de planificación (el usuario ya tiene documentos de ejemplo) |
| Ubicación en la app | Nuevo módulo independiente en el menú principal (no extiende Validador ni Generador) |
| ¿Requiere segundo documento "guía" + concordancia? | No — solo el documento de planificación, sin cruce de concordancia |
| Selección del tipo de recurso | El docente elige explícitamente de una lista (no automático) |
| "Rompecabezas" | Sin especificación adicional disponible — se interpreta como rompecabezas de lógica/relación (texto), no jigsaw de imagen, por ser lo técnicamente viable con el patrón actual |
| Salida de las hojas de Educación Inicial | Debe funcionar interactivo en pantalla (arrastrar, tocar, dibujar) además de imprimible |
| Enfoque de construcción | Fases separadas por nivel de riesgo (no big-bang, no motor genérico prematuro) |

---

## 3. Arquitectura general

```text
┌─────────────────────────────────────────────┐
│                MENÚ PRINCIPAL               │
│  [Validador]   [Generador]   [Actividades]  │  ← nueva tarjeta
└──────┬──────────────┬───────────────┬───────┘
                                       ▼
                          ActividadesView.tsx (nuevo)
                           │  Toggle "Nivel: EGB / Inicial"
                           │  1. Subir documento de planificación (.docx)
                           │  2. EGB → elegir semana · Inicial → elegir destreza
                           │  3. Elegir tipo de recurso (lista explícita)
                           │  4. Generar → preview interactivo + descarga (HTML/PDF)
                           ▼
                POST /activities/generate  (router nuevo: activities.py)
                           ▼
                services/generation/orchestrator.py
                           │  MISMO mecanismo _TOOL_SPECS/_TOOL_IMPLS ya existente,
                           │  generalizado con concordance opcional + forced_tool
                           ▼
                mcp_server/tools/{crossword,logic_puzzle,geometric_worksheet,...}.py
                           │  Schema Pydantic + función pura → HTML/SVG
                           ▼
                services/export/pdf_export.py
                           │  + nuevos casos en el dispatch por ResourceBlockType
```

**Principio rector:** reutilizar al máximo la infraestructura de generación ya probada (multi-proveedor LLM: OpenRouter/Gemini/Anthropic, validación Pydantic, renderizado determinista con `html.escape`, exportación PDF). Lo nuevo son las herramientas (schema + render function) y un router/UI delgados encima.

---

## 4. Fase 1 — Crucigrama y rompecabezas de lógica

### 4.1 Cambios a código existente (pequeños, aditivos)

1. **Extraer helpers de subida compartidos.** `_validate_upload`, `_save_upload`, `_validate_upload_bytes` hoy son privados en `app/routers/documents.py`. Se mueven a `app/services/parsing/upload_utils.py` para que `activities.py` no duplique la lógica de seguridad (extensión, magic bytes, límite 50MB). `documents.py` pasa a importar desde ahí; su comportamiento no cambia.
2. **Generalizar `orchestrator.py`:**
   - `generate_resource(week, concordance: WeekConcordance | None, request)` — cuando `concordance` es `None`, `_build_prompt` omite esa sección del prompt. El Validador sigue mandando concordancia igual que hoy.
   - Nuevo parámetro `forced_tool: str | None` — si se especifica, el prompt instruye directamente "DEBES invocar `<forced_tool>`", sin pasar por el heurístico de palabras clave.
   - Se corrige un mapeo incorrecto preexistente: la palabra clave "crucigrama" hoy enruta a `build_word_search` (sopa de letras); pasa a enrutar a `build_crossword`.
   - Se agrega un punto de inyección para el cliente LLM (mismo patrón que ya usa `material_builder/converter.py` con `transcriptor`/`metadatos_fn`), necesario para poder probar `activities.py` en CI sin gastar API real.
3. **`app/schemas/generation.py`:** +2 valores en `ResourceBlockType` (`crossword`, `logic_puzzle`).
4. **`app/services/export/pdf_export.py`:** +2 casos en el dispatch de `export_resource_pdf`, siguiendo el mismo patrón ya usado para `word_search` (grid → `Table` de ReportLab).

### 4.2 Componentes nuevos

**Backend — `app/routers/activities.py`**

```
POST /activities/upload              → sube solo el documento de planificación
GET  /activities/{session_id}/weeks  → lista semanas parseadas (selector EGB)
POST /activities/generate            → { session_id, week_number, resource_type, extra_instructions }
```

**`app/mcp_server/tools/crossword.py` — `build_crossword`**
- Schema: `items: list[{word, clue}]` (4–15 palabras), `title`, `instructions`.
- Algoritmo: coloca la palabra más larga primero; cada palabra siguiente busca una intersección válida (misma letra, ambas orientaciones) con alguna ya colocada, priorizando la posición más compacta. Si no logra intersección tras los intentos, se descarta con traza (no falla en seco).
- Numeración de casillas en orden de lectura + listas "Horizontales"/"Verticales".
- Render HTML: tabla con `<input>` por celda activa + botón "Comprobar" (mismo patrón `data-answer` que ya usa `material_builder/renderer.py`).

**`app/mcp_server/tools/logic_puzzle.py` — `build_logic_puzzle`**
- Schema con `mode: "relacionar" | "ordenar"`.
- `relacionar`: pares izquierda/derecha, clic para emparejar (mismo patrón click-to-mark que `word_search.py`).
- `ordenar`: lista con botones subir/bajar (no drag-and-drop crudo, más confiable en tablets dentro del iframe de Canvas).

**Frontend — `apps/web/src/components/ActividadesView.tsx`**
- Reutiliza patrones de `UploadStep.tsx` y `DownloadStep.tsx`.
- Selector de tipo de recurso explícito (no automático).

### 4.3 Plan de implementación paso a paso

1. Crear `upload_utils.py`, mover los 3 helpers desde `documents.py`, actualizar sus imports. Verificar que los tests existentes de `documents.py` siguen pasando sin cambios.
2. Generalizar `orchestrator.py` (concordance opcional, forced_tool, inyección de cliente LLM, fix del mapeo "crucigrama"). Verificar que el flujo del Validador (`generation.py` → `orchestrator.generate_resource`) sigue funcionando idéntico.
3. Implementar `mcp_server/tools/crossword.py` con su algoritmo de colocación + render HTML. Escribir `tests/test_crossword_tool.py` (intersección real, sin conflictos, HTML escapado) antes o junto con la implementación.
4. Implementar `mcp_server/tools/logic_puzzle.py` (ambos modos). Escribir `tests/test_logic_puzzle_tool.py`.
5. Registrar ambas herramientas en `_TOOL_SPECS`/`_TOOL_IMPLS` de `orchestrator.py` y en `ResourceBlockType`.
6. Agregar los 2 casos nuevos en `pdf_export.py::export_resource_pdf`.
7. Crear `app/routers/activities.py` (upload solo-sílabo + listar semanas + generar), registrar el router en `app/main.py`. Escribir `tests/test_activities_router.py` con el fixture real ya existente (`tests/fixtures/silabo_matematica_8vo_u1.docx`) y el cliente LLM inyectado/simulado.
8. Frontend: `ActividadesView.tsx`, agregar tarjeta en `MenuInicial.tsx`, rama `modulo === 'actividades'` en `App.tsx`, tipos/cliente API en `lib/types.ts`/`lib/api.ts`.
9. Verificación manual: generar un crucigrama y un rompecabezas de lógica desde la UI real, para una semana del fixture de Matemática 8vo; confirmar "Comprobar" funciona; confirmar descarga PDF imprime la grilla/columnas correctamente; confirmar que el Validador (Fase 3, `GenerateStep.tsx`) también puede alcanzar las 2 herramientas nuevas vía las palabras clave, sin regresión en las 5 herramientas existentes.

### 4.4 Archivos nuevos vs. tocados

```
NUEVOS
  app/routers/activities.py
  app/services/parsing/upload_utils.py
  app/mcp_server/tools/crossword.py
  app/mcp_server/tools/logic_puzzle.py
  apps/web/src/components/ActividadesView.tsx
  tests/test_crossword_tool.py, test_logic_puzzle_tool.py, test_activities_router.py

TOCADOS (pequeños, aditivos)
  app/routers/documents.py                 → extraer helpers a upload_utils.py
  app/services/generation/orchestrator.py  → concordance opcional + forced_tool + inyección para tests + fix mapeo "crucigrama"
  app/schemas/generation.py                → +2 ResourceBlockType
  app/services/export/pdf_export.py        → +2 casos en el dispatch
  app/main.py                              → registrar router de activities
  apps/web/src/App.tsx                     → +1 rama de modulo ('actividades')
  apps/web/src/components/MenuInicial.tsx  → +1 tarjeta
  apps/web/src/lib/types.ts, api.ts        → tipos y llamadas del nuevo módulo
```

---

## 5. Fase 2 — Hojas de Educación Inicial

**Bloqueada hasta recibir los documentos de ejemplo de Educación Inicial.** Todo lo que sigue es el diseño de lo que sí se puede definir sin depender de ellos; los campos exactos del schema de extracción se finalizan en el paso 0.

### 5.1 Paso 0 (obligatorio, previo a todo lo demás): descubrimiento del formato

Mismo proceso que se siguió originalmente para construir el Spec v1.2 del sílabo de EGB: recibir los documentos de ejemplo reales → identificar tablas/encabezados/estructura → mapear campos → escribir el parser contra fixtures reales, no contra suposiciones.

### 5.2 Nuevo parser + schema (forma esperada — a confirmar en el paso 0)

```python
# app/schemas/extraction.py — nuevos modelos, sujetos a ajuste según los documentos reales
class DestrezaInicial(BaseModel):
    ambito: str            # ej. "Relaciones lógico-matemáticas"
    codigo: str = ""
    descripcion: str

class SilaboInicialExtraction(BaseModel):
    grade: str = ""         # ej. "Inicial 2"
    teacher: str = ""
    destrezas: list[DestrezaInicial] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

`app/services/parsing/docx_parser_inicial.py::parse_silabo_inicial_docx()` — mismo estilo que el parser actual (tablas + regex determinista, no LLM).

**Selección explícita de nivel:** en `ActividadesView.tsx`, el toggle "Nivel: EGB / Inicial" (agregado en Fase 1 para la UI, activado aquí) determina qué parser corre y qué opciones de recurso se ofrecen. No se auto-detecta la plantilla del documento.

### 5.3 Herramientas nuevas

**`app/mcp_server/tools/geometric_worksheet.py` — `build_geometric_worksheet`**
- Figuras (círculo, cuadrado, triángulo, rombo, estrella, óvalo...) como SVG puro en Python, mismo enfoque que ya usa `diagram.py`.
- `activity_type`: reconocer (clic) / colorear por forma (clic cicla color) / trazar (requiere canvas de dibujo, ver 5.5).

**`app/mcp_server/tools/visual_discrimination.py` — `build_visual_discrimination`**
- Filas de íconos SVG; el estudiante hace clic en "el diferente" o "el igual". Interacción por clic, sin dibujo.

**Correspondencia — no es una herramienta nueva.** Es estructuralmente igual al modo `relacionar` de `build_logic_puzzle` (Fase 1), solo con íconos en vez de palabras. Se agrega un modo de renderizado visual a `logic_puzzle.py` en vez de duplicar el tool.

**`app/mcp_server/tools/spatial_orientation.py` — `build_spatial_orientation`**
- `arriba_abajo` / `izquierda_derecha`: preguntas de clic sobre grilla con íconos posicionados.
- `laberinto`: **componente de mayor riesgo/esfuerzo de la Fase 2.** Requiere algoritmo de generación de laberintos (recursive backtracker, grilla 5×5–8×8) que no existe hoy en el código. Grilla acotada + reintento si no resulta resoluble tras N intentos; nunca se entrega un laberinto sin solución (`assert maze_is_solvable(...)` en tests).

### 5.4 Salida dual (pantalla + impresión)

Misma estrategia que Fase 1: la función de render produce SVG/HTML interactivo; `pdf_export.py` gana los casos nuevos usando `reportlab.graphics.shapes` para redibujar las figuras nativamente en el PDF (no como imagen capturada).

### 5.5 Reutilización del canvas de dibujo

Para "trazar figura" y "resolver laberinto a mano" se reutiliza el módulo JS de dibujo ya existente y probado en `app/services/material_builder/shell.py` (zonas de trabajo ✏️ Dibujar: canvas táctil con deshacer/borrar, ya maneja mouse y touch). Se extrae a un snippet compartido en vez de reimplementarlo — evita el riesgo de manejo de eventos táctiles desde cero.

### 5.6 Manejo de errores

- Parser: documento que no matchea la estructura esperada → 422 con mensaje claro, usando el mismo campo `warnings: list[str]` que ya existe en `SilaboExtraction`.
- Laberinto: grilla acotada + reintento automático si no es resoluble.
- Canvas no soportado: reutiliza el aviso rojo automático que ya existe en `shell.py` para visores sin JavaScript.

### 5.7 Testing

- `tests/test_docx_parser_inicial.py` — una vez existan los fixtures, mismo rigor que `test_docx_parser.py` (valores exactos verificados a mano).
- `tests/test_geometric_worksheet_tool.py`, `test_visual_discrimination_tool.py`, `test_spatial_orientation_tool.py` — estructura SVG válida, escapado, conteo de figuras correcto, `maze_is_solvable(...)`.
- **No cubierto por tests automáticos:** dibujo táctil real en tablet — queda como ítem de QA manual explícito antes de dar la Fase 2 por completa.

### 5.8 Plan de implementación paso a paso

1. Recibir y revisar los documentos de ejemplo de Educación Inicial. Confirmar/ajustar el schema de la sección 5.2 contra la estructura real.
2. Implementar `docx_parser_inicial.py` contra los fixtures reales. Escribir `test_docx_parser_inicial.py` con valores verificados a mano.
3. Extraer el módulo de dibujo de `shell.py` a un snippet compartido reutilizable, sin cambiar su comportamiento actual en el módulo Generador (verificar regresión ahí antes de seguir).
4. Implementar `geometric_worksheet.py` (modos reconocer/colorear primero, trazar al final una vez el canvas compartido esté listo). Tests correspondientes.
5. Implementar `visual_discrimination.py`. Tests correspondientes.
6. Agregar modo visual (íconos) a `logic_puzzle.py` para correspondencia. Test de regresión del modo texto existente.
7. Implementar `spatial_orientation.py`: arriba/abajo e izquierda/derecha primero (bajo riesgo); laberinto al final, como hito separado con su propio test de resolubilidad.
8. Registrar las 3 herramientas nuevas en `orchestrator.py`. Agregar los 3 casos nuevos en `pdf_export.py`.
9. Frontend: activar la rama "Inicial" del toggle en `ActividadesView.tsx` (selector de destreza en vez de semana, lista de tipos de hoja de Inicial).
10. QA manual en tablet real (Canvas embebido) antes de considerar la fase completa.

### 5.9 Archivos nuevos vs. tocados

```
NUEVOS (bloqueados por documentos de ejemplo)
  app/services/parsing/docx_parser_inicial.py
  app/schemas/extraction.py                → +DestrezaInicial, SilaboInicialExtraction
  app/mcp_server/tools/geometric_worksheet.py
  app/mcp_server/tools/visual_discrimination.py
  app/mcp_server/tools/spatial_orientation.py
  tests/fixtures/silabo_inicial_*.docx
  tests/test_docx_parser_inicial.py + 3 tests de tools

TOCADOS (pequeños, aditivos)
  app/mcp_server/tools/logic_puzzle.py     → +modo visual (íconos) para correspondencia
  app/services/export/pdf_export.py        → +3 casos de dispatch
  app/services/generation/orchestrator.py  → registrar 3 tools más
  app/services/material_builder/shell.py   → extraer el módulo de dibujo a algo compartido
  apps/web/src/components/ActividadesView.tsx → activar selector de destreza para nivel Inicial
```

---

## 6. Fuera de alcance (por ahora)

- **Rompecabezas tipo jigsaw de imagen** (piezas encajables arrastrables): requiere imagen base (¿generada por IA? ¿ilustración fija?), lógica de corte de piezas y drag-and-drop en canvas. Es un desarrollo aparte que no encaja en el patrón "texto → HTML" actual. Se retoma si hay un caso de uso concreto.
- **"Juegos interactivos"** sin especificación adicional más allá de lo ya cubierto por las herramientas de Fase 1/2 y las 5 herramientas existentes (sopa de letras, flashcards, etc.).
- Autenticación, multiusuario e historial persistente — siguen fuera de alcance del aplicativo en general (ya documentado en el README principal), no específico de este módulo.

## 7. Riesgos principales

| Riesgo | Fase | Mitigación |
|---|---|---|
| Documento de Educación Inicial con estructura muy irregular o inconsistente entre ejemplos | 2 | Paso 0 dedicado a descubrimiento antes de programar nada; parser determinista con `warnings` explícitos, nunca falla en silencio |
| Generación de laberintos sin solución | 2 | Grilla acotada + reintento automático + test de resolubilidad obligatorio |
| Dibujo táctil poco confiable en tablets dentro del iframe de Canvas | 2 | Reutilizar el canvas ya probado de `shell.py` en vez de escribir uno nuevo; QA manual obligatorio en dispositivo real |
| Colisión de la palabra clave "crucigrama" con `build_word_search` | 1 | Corregido explícitamente en el paso 2 del plan de Fase 1 |
