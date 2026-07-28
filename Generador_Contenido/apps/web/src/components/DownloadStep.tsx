import { useMemo, useState } from 'react'
import type { GeneratedResource } from '../lib/types'
import { exportHtml, exportPptx } from '../lib/api'

interface Props {
  resource: GeneratedResource
  onBack: () => void
  onRestart: () => void
}

function buildPreviewHtml(resource: GeneratedResource): string {
  const blocks = resource.blocks.map((b) => `<section style="margin-bottom:32px">${b.rendered_html}</section>`).join('\n')
  return `<!doctype html><html lang="es"><head><meta charset="utf-8">
  <style>body{font-family:system-ui,sans-serif;padding:20px;margin:0}</style>
  </head><body><h2>${resource.title}</h2>${blocks}</body></html>`
}

export default function DownloadStep({ resource, onBack, onRestart }: Props) {
  const [busy, setBusy] = useState<'html' | 'pptx' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const previewSrcDoc = useMemo(() => buildPreviewHtml(resource), [resource])

  async function handleExport(kind: 'html' | 'pptx') {
    setBusy(kind)
    setError(null)
    try {
      await (kind === 'html' ? exportHtml(resource) : exportPptx(resource))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo exportar el recurso.')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Recurso listo para descargar</h1>
      <p className="text-gray-600 mb-6">
        Semana {resource.week_number} — {resource.title}
      </p>

      <div className="bg-white rounded-xl border border-gray-200 mb-6 overflow-hidden">
        <iframe
          title="Vista previa del recurso"
          sandbox="allow-scripts allow-same-origin"
          srcDoc={previewSrcDoc}
          className="w-full"
          style={{ height: 500, border: 'none' }}
        />
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm p-3">{error}</div>
      )}

      <div className="flex flex-wrap gap-3 mb-6">
        <button
          type="button"
          disabled={busy !== null}
          className="rounded-lg bg-blue-600 text-white px-5 py-2.5 font-medium disabled:bg-gray-300 hover:bg-blue-700"
          onClick={() => handleExport('html')}
        >
          {busy === 'html' ? 'Descargando…' : '⬇ Descargar HTML para Canvas'}
        </button>
        <button
          type="button"
          disabled={busy !== null}
          className="rounded-lg bg-white border border-gray-300 px-5 py-2.5 font-medium disabled:opacity-50 hover:bg-gray-50"
          onClick={() => handleExport('pptx')}
        >
          {busy === 'pptx' ? 'Descargando…' : '⬇ Descargar PPTX'}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <button type="button" className="text-gray-500 hover:text-gray-800 text-sm" onClick={onBack}>
          ← Editar propuesta
        </button>
        <button type="button" className="ml-auto text-blue-600 hover:text-blue-800 text-sm font-medium" onClick={onRestart}>
          Generar otro recurso
        </button>
      </div>
    </div>
  )
}
