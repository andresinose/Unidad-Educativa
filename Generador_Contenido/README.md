# Motor de análisis curricular y generación de recursos

Sube un sílabo (DOCX/PDF) y una guía didáctica (DOCX/PDF), valida su
correspondencia curricular semana a semana, y genera recursos didácticos
interactivos descargables (HTML autónomo listo para Canvas, PPTX). Sin base
de datos: cada análisis vive en una carpeta de sesión temporal en disco.

Ver [`.claude/plans/jolly-yawning-spring.md`](../../.claude/plans/jolly-yawning-spring.md) para el plan de arquitectura completo.

## Requisitos

- Python 3.12+
- Node.js 20+
- Una API key de Anthropic (solo necesaria para el paso de generación — `/analyze` funciona sin ella)

## Desarrollo local

```bash
# Backend
cd apps/api
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt   # o .venv/bin/pip en macOS/Linux
export ANTHROPIC_API_KEY=sk-...                    # opcional, requerido solo para /generate
./.venv/Scripts/uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd apps/web
npm install
npm run dev
```

El frontend en `http://localhost:5173` proxea `/api/*` hacia `http://localhost:8000` (ver `vite.config.ts`).

## Docker

```bash
cd infra
cp .env.example .env   # y completa ANTHROPIC_API_KEY
docker compose up --build
```

Web en `http://localhost:8080`, API en `http://localhost:8000`.

## Pruebas

```bash
cd apps/api
./.venv/Scripts/pytest tests/ -v
```

Usa como fixture un sílabo y guía reales de Matemática 8vo EGB (`tests/fixtures/`) —
las pruebas de concordancia verifican que el motor detecta exactamente los
mismos vacíos hallados manualmente: las Semanas 5-6 del sílabo no tienen
desarrollo en la guía, y ninguna adaptación curricular individual del sílabo
se refleja en la guía.

## Servidor MCP independiente

Las herramientas de generación (`build_interactive_activity`, `render_diagram`)
también se exponen como servidor MCP standalone, reutilizable desde Claude
Desktop o cualquier cliente MCP:

```bash
cd apps/api
./.venv/Scripts/python -m app.mcp_server.server
```

## Qué falta (fuera de alcance de esta iteración)

- Exportación a PDF (requiere un toolchain de navegador headless que se
  evitó deliberadamente por simplicidad de autoalojamiento).
- Autenticación, roles y multiusuario real.
- Persistencia/base de datos e historial de proyectos.
