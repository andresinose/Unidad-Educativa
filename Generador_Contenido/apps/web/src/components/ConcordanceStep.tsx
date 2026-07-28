import type { AnalyzeResponse, ConcordanceStatus } from '../lib/types'

interface Props {
  data: AnalyzeResponse
  onContinue: (weekNumber: number) => void
  onBack: () => void
}

const STATUS_STYLE: Record<ConcordanceStatus, { label: string; className: string }> = {
  CONCORDANTE: { label: 'Concordante', className: 'bg-green-100 text-green-800' },
  PARCIAL: { label: 'Parcial', className: 'bg-amber-100 text-amber-800' },
  FALTANTE_EN_GUIA: { label: 'Falta en la guía', className: 'bg-red-100 text-red-800' },
  FALTANTE_EN_SILABO: { label: 'Falta en el sílabo', className: 'bg-red-100 text-red-800' },
}

function InfoRow({ label, value }: { label: string; value: string }) {
  if (!value) return null
  return (
    <div className="flex justify-between text-sm py-1 border-b border-gray-100 last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-right">{value}</span>
    </div>
  )
}

export default function ConcordanceStep({ data, onContinue, onBack }: Props) {
  const { silabo, guia, concordance } = data
  const generatableWeeks = concordance.weeks.filter((w) => w.status !== 'FALTANTE_EN_SILABO')

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Correspondencia curricular</h1>
      <p className="text-gray-600 mb-6">
        Revise los datos detectados y el resultado del análisis de concordancia entre el sílabo y
        la guía didáctica.
      </p>

      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h2 className="font-semibold mb-2">📋 Sílabo</h2>
          <InfoRow label="Asignatura" value={silabo.subject} />
          <InfoRow label="Docente" value={silabo.teacher} />
          <InfoRow label="Grado" value={silabo.grade} />
          <InfoRow label="Unidad" value={silabo.unit_name} />
          <InfoRow label="Trimestre / Parcial" value={`${silabo.trimester} / ${silabo.parcial}`} />
          <InfoRow label="Fechas" value={`${silabo.start_date} – ${silabo.end_date}`} />
          <InfoRow label="Semanas detectadas" value={String(silabo.weeks.length)} />
          {silabo.warnings.map((w) => (
            <p key={w} className="text-amber-700 text-xs mt-2">⚠ {w}</p>
          ))}
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h2 className="font-semibold mb-2">📖 Guía didáctica</h2>
          <InfoRow label="Asignatura" value={guia.subject} />
          <InfoRow label="Grado" value={guia.grade} />
          <InfoRow label="Páginas totales" value={String(guia.total_pages)} />
          <InfoRow label="Semanas con contenido" value={guia.weeks_detected.join(', ') || '(ninguna)'} />
          {guia.warnings.map((w) => (
            <p key={w} className="text-amber-700 text-xs mt-2">⚠ {w}</p>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <h2 className="font-semibold mb-2">Hallazgos clave</h2>
        <ul className="list-disc list-inside text-sm space-y-1">
          {concordance.key_findings.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto mb-6">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="p-3">Semana</th>
              <th className="p-3">Tema</th>
              <th className="p-3">Estado</th>
              <th className="p-3">Páginas guía</th>
              <th className="p-3">Adaptaciones</th>
              <th className="p-3">Códigos faltantes en guía</th>
            </tr>
          </thead>
          <tbody>
            {concordance.weeks.map((w) => {
              const style = STATUS_STYLE[w.status]
              return (
                <tr key={w.week_number} className="border-t border-gray-100 align-top">
                  <td className="p-3 font-medium">{w.week_number}</td>
                  <td className="p-3 max-w-xs">{w.topic}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.className}`}>
                      {style.label}
                    </span>
                  </td>
                  <td className="p-3">{w.page_range_guia || '—'}</td>
                  <td className="p-3 text-xs">
                    sílabo: {w.adaptation_in_silabo ? 'sí' : 'no'} · guía: {w.adaptation_in_guia ? 'sí' : 'no'}
                  </td>
                  <td className="p-3 text-xs text-red-700">{w.missing_codes_in_guia.join(', ') || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mb-6">
        <label htmlFor="week-select" className="block font-medium mb-2">
          Elija una semana para generar un recurso
        </label>
        <select
          id="week-select"
          className="w-full rounded-lg border border-gray-300 p-2"
          defaultValue=""
          onChange={(e) => {
            const wn = parseInt(e.target.value, 10)
            if (!Number.isNaN(wn)) onContinue(wn)
          }}
        >
          <option value="" disabled>
            — Seleccione una semana —
          </option>
          {generatableWeeks.map((w) => (
            <option key={w.week_number} value={w.week_number}>
              Semana {w.week_number} — {w.topic} ({STATUS_STYLE[w.status].label})
            </option>
          ))}
        </select>
      </div>

      <button type="button" className="text-gray-500 hover:text-gray-800 text-sm" onClick={onBack}>
        ← Volver a cargar documentos
      </button>
    </div>
  )
}
