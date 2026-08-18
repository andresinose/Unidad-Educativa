# Integración: Menú principal + Generador de contenidos

Guía para integrar en la primera versión del aplicativo **únicamente**:

1. El **menú principal** (pantalla de inicio con las dos tarjetas).
2. El módulo **Generador de contenidos** completo tal como está hoy: subir un PDF
   pedagógico → conversión automática con Claude (visión) → HTML interactivo autónomo
   con vista previa y descarga.

> **Fuera de alcance de este documento:** el Validador de contenidos (sílabo/guía,
> concordancia, generación de recursos puntuales). Esa lógica ya existe en el aplicativo
> destino; aquí solo se referencia el punto donde el menú lo invoca.

Los archivos fuente citados están en este repositorio:
`Generador_Contenido/apps/api` (backend FastAPI) y `Generador_Contenido/apps/web`
(frontend React + Vite + Tailwind).

---

## 1. Arquitectura general

```text
┌─────────────────────────────────────────────┐
│                MENÚ PRINCIPAL               │  App.tsx (estado modulo:
│   [Validador]            [Generador]        │  'menu'|'validador'|'generador')
└──────┬──────────────────────┬───────────────┘
       │ (lógica existente)   │
       ▼                      ▼
  Validador           GeneratorView.tsx
                        │  POST /materials/upload  ── PDF → job en 2.º plano
                        │  GET  /materials/jobs/{id} ─ progreso "página X de N"
                        │  GET  /materials ─────────── convertidos vigentes
                        │  GET  /materials/{id}/preview | /download
                        ▼
              services/material_builder/
                converter.py  → PyMuPDF rasteriza páginas + extrae ilustraciones
                              → Claude (visión) transcribe cada página a BLOQUES
                blocks.py     → esquema Pydantic de bloques (el LLM nunca emite HTML)
                renderer.py   → bloques → HTML del diseño validado (todo escapado)
                shell.py      → cascarón único: CSS institucional + JS interactivo
                jobs.py       → jobs en memoria + var/materials_convertidos (TTL 6 h)
```

Propiedad de seguridad clave (misma filosofía del validador): **el modelo nunca emite
HTML/JS libre**. Transcribe a bloques tipados validados con Pydantic; un renderizador
determinista genera el HTML y todo texto pasa por `html.escape`.

---

## 2. Backend (FastAPI)

### 2.1 Dependencias Python

Añadir a `requirements.txt` (si no están ya):

```text
fastapi
uvicorn[standard]
python-multipart        # subida de archivos
pydantic>=2
anthropic               # SDK de Claude
pymupdf                 # rasterizado del PDF + extracción de imágenes
Pillow                  # optimización WebP de ilustraciones
```

### 2.2 Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | Sí (para convertir) | Clave de API de Anthropic. Sin ella, la subida termina en error controlado con mensaje claro. |
| `GENERATION_MODEL` | No | Modelo de visión/transcripción. Por defecto `claude-sonnet-5`. |
| `SESSION_TTL_SECONDS` | No | Vigencia de los convertidos. Por defecto 21600 (6 h). |

### 2.3 Utilidades de `core` requeridas

El módulo usa estas piezas (copiarlas si el aplicativo destino no las tiene):

- `app/core/config.py`: `BASE_DIR`, `WORK_DIR` (carpeta temporal de subidas),
  `MAX_UPLOAD_BYTES` (50 MB), `SESSION_TTL_SECONDS`, `ANTHROPIC_API_KEY`,
  `GENERATION_MODEL`.
- `app/core/session.py`: `random_filename()` (nunca conservar el nombre original del
  archivo subido; solo su extensión).

### 2.4 Archivos a copiar (sin cambios)

| Archivo | Rol |
|---|---|
| `app/services/material_builder/__init__.py` | paquete |
| `app/services/material_builder/blocks.py` | Esquema de bloques (`Bloque`, `PaginaTranscrita`, `MetadatosMaterial`, `EjercicioItem`). 12 tipos: titulo_seccion, periodo, subtitulo, parrafo, caja (6 estilos de color), lista, tabla_datos, tabla_generica, figura, flujo, ejercicio_relleno, zona_trabajo. |
| `app/services/material_builder/renderer.py` | Bloques → HTML. Ids deterministas por página (`pg{N}-e1-0`, `pg{N}-z1`, `pg{N}-c1`) para que el autoguardado del estudiante sea estable. Ejercicio con `respuesta` no vacía → input con `data-answer` + botón Comprobar; vacía → campo libre. |
| `app/services/material_builder/shell.py` | Cascarón único del HTML final: paleta institucional UEI (azul #0d3a80/#0a2f68, verde menta #5ecfb1, naranja #e9a13b, rosa #d0245f), toolbar (índice, navegación, resaltar, subrayar, quitar marca, exportar/restaurar avance, limpiar), capa JS completa (autoguardado localStorage con respaldo en memoria, comprobación, marcas, zonas Escribir/Dibujar con canvas, navegación con IntersectionObserver), aviso rojo automático si el visor no ejecuta JavaScript, y estilos de impresión. |
| `app/services/material_builder/converter.py` | Pipeline: rasteriza cada página (zoom 2.0), extrae ilustraciones raster → WebP base64 (máx. 1100 px de ancho, calidad 78), llama a Claude con `tool_choice` forzado al esquema de bloques, ensambla portada + páginas + índice. Página 1 del PDF = portada (se recrea con metadatos detectados). Las funciones de API son inyectables (`transcriptor`, `metadatos_fn`) para pruebas sin consumo real. |
| `app/services/material_builder/jobs.py` | Trabajos en hilo (`threading.Thread`, daemon) con estado en memoria; resultado en `var/materials_convertidos/{id}.html` + `{id}.json`; `listar_convertidos()` barre expirados por TTL; `ruta_convertido()` valida el id contra path traversal. |
| `app/routers/materials.py` | Endpoints del módulo (ver tabla). Incluye validación de extensión `.pdf` y límite de 50 MB en streaming. |

### 2.5 Registro en la aplicación

En `app/main.py`:

```python
from app.routers import materials          # + los routers existentes

app.include_router(materials.router)
```

### 2.6 Endpoints resultantes

| Método y ruta | Descripción |
|---|---|
| `POST /materials/upload` | Recibe el PDF (`multipart`, campo `archivo`). Valida extensión y tamaño. Inicia la conversión en segundo plano y devuelve `{id, estado, pagina_actual, total_paginas}`. |
| `GET /materials/jobs/{job_id}` | Estado del trabajo: `procesando` \| `completado` \| `error`, con `pagina_actual/total_paginas` para la barra de progreso, `material_id` al completar y `error` legible si falla. |
| `GET /materials` | Materiales convertidos vigentes (TTL 6 h). Cada uno: id, título, materia, grado, unidad, docente, período, páginas, filename, `source: "convertido"`. |
| `GET /materials/{id}/preview` | El HTML inline (para el iframe de vista previa). |
| `GET /materials/{id}/download` | El mismo HTML con `Content-Disposition: attachment`. |

> Nota: el router del repositorio incluye además un catálogo estático `_CATALOG` con el
> material curado de Matemática. Para el aplicativo destino puede dejarse vacío
> (`_CATALOG = {}`) o conservarse; el frontend de esta versión solo muestra
> `source == "convertido"`.

### 2.7 Persistencia (sin base de datos)

- PDF subido → `WORK_DIR` con nombre aleatorio; **se elimina** al terminar el job.
- Resultado → `var/materials_convertidos/` (HTML + JSON de metadatos), barrido por TTL.
- Estado de jobs → memoria del proceso (si el servidor se reinicia a mitad de una
  conversión, se vuelve a subir el PDF).

---

## 3. Frontend (React + Vite + Tailwind)

### 3.1 Archivos a copiar (sin cambios)

| Archivo | Rol |
|---|---|
| `src/components/MenuInicial.tsx` | Pantalla de inicio: fondo azul institucional `#0a2f68` con figuras geométricas de la portada (triángulo verde menta, rombo naranja, círculos translúcidos), encabezado "UNIDAD EDUCATIVA BILINGÜE INDOAMÉRICA / Plataforma pedagógica" y dos tarjetas blancas con hover. Recibe `onSelect: (m: 'validador' | 'generador') => void`. |
| `src/components/GeneratorView.tsx` | Vista del generador: zona de carga (botón + drag & drop, solo `.pdf`), subida a `/materials/upload`, sondeo del job cada 1,5 s con barra de progreso ("Convirtiendo… página X de N"), mensaje de éxito/error, y lista de convertidos con chips de metadatos, vista previa en iframe (`sandbox="allow-scripts allow-same-origin allow-downloads"`, alto 620 px), "Abrir en pestaña nueva" y "⬇ Descargar HTML". |

### 3.2 Tipos (`src/lib/types.ts`) — añadir

```ts
export interface Material {
  id: string
  title: string
  subject: string
  grade: string
  unit: string
  teacher: string
  term: string
  pages: number
  filename: string
  source: 'curado' | 'convertido'
}

export interface ConversionJob {
  id: string
  estado: 'procesando' | 'completado' | 'error'
  pagina_actual: number
  total_paginas: number
  material_id: string | null
  error: string | null
}
```

### 3.3 Cliente API (`src/lib/api.ts`) — añadir

```ts
export async function listMaterials(): Promise<Material[]> {
  const res = await fetch(`${BASE}/materials`)
  return unwrap(res)
}

export const materialPreviewUrl = (id: string) => `${BASE}/materials/${id}/preview`

export async function uploadMaterialPdf(archivo: File): Promise<ConversionJob> {
  const form = new FormData()
  form.append('archivo', archivo)
  const res = await fetch(`${BASE}/materials/upload`, { method: 'POST', body: form })
  return unwrap(res)
}

export async function getConversionJob(jobId: string): Promise<ConversionJob> {
  const res = await fetch(`${BASE}/materials/jobs/${jobId}`)
  return unwrap(res)
}

export async function downloadMaterial(material: Material) {
  const res = await fetch(`${BASE}/materials/${material.id}/download`)
  if (!res.ok) throw new ApiError(res.statusText, res.status)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = material.filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
```

(`BASE = '/api'`, `unwrap` y `ApiError` son los ya existentes en el aplicativo.)

### 3.4 Integración en `App.tsx`

```tsx
import MenuInicial from './components/MenuInicial'
import GeneratorView from './components/GeneratorView'

type Modulo = 'menu' | 'validador' | 'generador'

const MODULO_LABELS: Record<Exclude<Modulo, 'menu'>, string> = {
  validador: 'Validador de contenidos',
  generador: 'Generador de contenidos',
}

export default function App() {
  const [modulo, setModulo] = useState<Modulo>('menu')
  // ... estado existente del validador (se conserva al navegar) ...

  if (modulo === 'menu') {
    return <MenuInicial onSelect={setModulo} />
  }

  return (
    <div className="min-h-screen">
      {/* Cabecera azul con botón de regreso, visible en ambos módulos */}
      <header className="border-b border-gray-200" style={{ background: '#0a2f68' }}>
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4 flex-wrap">
          <button
            type="button"
            onClick={() => setModulo('menu')}
            className="text-sm font-medium text-white/85 hover:text-white border border-white/30 rounded-lg px-3 py-1.5"
          >
            ← Menú principal
          </button>
          <div>
            <h1 className="font-bold text-lg text-white">Unidad Educativa Bilingüe Indoamérica</h1>
            <p className="text-sm" style={{ color: '#5ecfb1' }}>{MODULO_LABELS[modulo]}</p>
          </div>
        </div>
      </header>

      {modulo === 'generador' && (
        <main className="px-4 py-8 pb-16">
          <GeneratorView />
        </main>
      )}

      {modulo === 'validador' && (
        /* aquí va el flujo existente del validador, sin cambios */
      )}
    </div>
  )
}
```

Claves de este patrón:
- El estado del validador vive en `App` (no en los pasos), por lo que **ir al menú y
  volver no pierde el análisis en curso**.
- El menú es la pantalla inicial (`modulo === 'menu'` al arrancar).

### 3.5 Proxy de desarrollo

`vite.config.ts` debe proxyear `/api` al backend (ya existente en el aplicativo):

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

En producción (nginx/docker) la regla equivalente: `location /api/ { proxy_pass ... }`.

---

## 4. El HTML generado (qué recibe el docente)

Un **solo archivo autónomo** (CSS/JS inline, ilustraciones WebP en base64, sin CDNs —
funciona offline y dentro de Canvas vía iframe) con:

- Portada institucional recreada con los metadatos detectados del PDF.
- Una `<section class="pagina">` por página, con cabecera y pie numerado.
- **Interactividad**: campos de respuesta con autocorrección (✔/✘ + puntaje) cuando la
  respuesta es cerrada; zonas de trabajo con pestañas ⌨ Escribir / ✏️ Dibujar (canvas
  con deshacer/borrar); resaltar/subrayar/quitar marca sobre el texto; índice lateral;
  navegación por páginas; autoguardado en `localStorage` (prefijo = id del material);
  exportar/restaurar el avance como JSON; botón limpiar.
- **Aviso rojo automático** si se abre en un visor sin JavaScript ("descarga el archivo
  y ábrelo con doble clic"), que desaparece solo en un navegador normal.
- Módulos JS aislados con try/catch: si uno falla en un navegador raro, el resto sigue.

## 5. Costo y tiempos (informar al docente)

- 1 llamada de visión por página + 1 para metadatos, con `GENERATION_MODEL`.
- PDF de ~95 páginas ⇒ varios minutos y costo proporcional; se muestra el progreso.
- La autocorrección solo se genera donde la respuesta es verificable (el modelo la
  calcula); los ejercicios abiertos quedan como campo libre o zona de trabajo.

## 6. Checklist de verificación post-integración

1. `GET /health` responde y `GET /materials` devuelve `[]` (o el catálogo estático).
2. La app abre en el **menú**; "Ingresar" en cada tarjeta entra al módulo correcto y
   "← Menú principal" regresa sin perder estado del validador.
3. Subir un no-PDF → error 400 con mensaje claro en la interfaz.
4. Sin `ANTHROPIC_API_KEY` → el job termina en `error` con mensaje explicativo (no se cuelga).
5. Con clave: subir un PDF corto → progreso → tarjeta con vista previa interactiva
   (probar "Comprobar" dentro del iframe) → descarga → abrir el archivo con doble clic
   → responder, recargar y verificar que el avance persiste.
6. Copiar las pruebas `tests/test_materials.py` y `tests/test_material_builder.py`
   (esta última convierte un PDF generado al vuelo con la API **simulada** — apta para CI
   sin consumo). Ejecutar: `pytest tests/ -q`.

## 7. Inventario rápido de archivos

```text
BACKEND  (copiar)
  app/services/material_builder/{__init__,blocks,renderer,shell,converter,jobs}.py
  app/routers/materials.py
BACKEND  (tocar)
  app/main.py                → include_router(materials.router)
  app/core/config.py         → claves indicadas en 2.3 (si faltan)
  requirements.txt           → pymupdf, Pillow, anthropic, python-multipart

FRONTEND (copiar)
  src/components/MenuInicial.tsx
  src/components/GeneratorView.tsx
FRONTEND (tocar)
  src/lib/types.ts           → Material, ConversionJob
  src/lib/api.ts             → listMaterials, materialPreviewUrl, uploadMaterialPdf,
                               getConversionJob, downloadMaterial
  src/App.tsx                → estado modulo + cabecera + render condicional (3.4)

PRUEBAS  (copiar, opcional pero recomendado)
  tests/test_materials.py
  tests/test_material_builder.py
```
