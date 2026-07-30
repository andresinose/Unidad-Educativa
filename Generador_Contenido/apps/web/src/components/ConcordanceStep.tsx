import { useState } from 'react'
import type { AnalyzeResponse, DetalleSemanal } from '../lib/types'

interface Props {
  data: AnalyzeResponse
  onContinue: (weekNumber: number) => void
  onBack: () => void
}

const GLOBAL_STAMP_STYLE: Record<string, { label: string; bg: string; border: string; text: string; badgeBg: string }> = {
  CUMPLE: {
    label: 'VEREDICTO: CUMPLE',
    bg: 'bg-emerald-50',
    border: 'border-emerald-500',
    text: 'text-emerald-900',
    badgeBg: 'bg-emerald-600 text-white',
  },
  CUMPLE_PARCIAL: {
    label: 'VEREDICTO: CUMPLE PARCIAL',
    bg: 'bg-amber-50',
    border: 'border-amber-500',
    text: 'text-amber-900',
    badgeBg: 'bg-amber-600 text-white',
  },
  NO_CUMPLE: {
    label: 'VEREDICTO: NO CUMPLE',
    bg: 'bg-rose-50',
    border: 'border-rose-500',
    text: 'text-rose-900',
    badgeBg: 'bg-rose-600 text-white',
  },
}

const WEEK_STATUS_STYLE: Record<string, { label: string; className: string }> = {
  CUMPLE: { label: 'CUMPLE', className: 'bg-emerald-100 text-emerald-800 border border-emerald-300' },
  CONCORDANTE: { label: 'CUMPLE', className: 'bg-emerald-100 text-emerald-800 border border-emerald-300' },
  CUMPLE_PARCIAL: { label: 'CUMPLE PARCIAL', className: 'bg-amber-100 text-amber-800 border border-amber-300' },
  PARCIAL: { label: 'CUMPLE PARCIAL', className: 'bg-amber-100 text-amber-800 border border-amber-300' },
  NO_CUMPLE: { label: 'NO CUMPLE', className: 'bg-rose-100 text-rose-800 border border-rose-300' },
  FALTANTE_EN_GUIA: { label: 'NO CUMPLE', className: 'bg-rose-100 text-rose-800 border border-rose-300' },
  FALTANTE_EN_SILABO: { label: 'NO CUMPLE', className: 'bg-rose-100 text-rose-800 border border-rose-300' },
}

function InfoRow({ label, value }: { label: string; value: string }) {
  if (!value) return null
  return (
    <div className="flex justify-between text-sm py-1 border-b border-gray-100 last:border-0">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-right text-gray-800">{value}</span>
    </div>
  )
}

export default function ConcordanceStep({ data, onContinue, onBack }: Props) {
  const { silabo, guia, concordance } = data
  const [expandedWeeks, setExpandedWeeks] = useState<Record<number, boolean>>({})

  const toggleWeek = (wn: number) => {
    setExpandedWeeks((prev) => ({ ...prev, [wn]: !prev[wn] }))
  }

  const veredictoGlobalKey = concordance.veredicto_global || (concordance.missing_count === 0 ? 'CUMPLE' : 'CUMPLE_PARCIAL')
  const stamp = GLOBAL_STAMP_STYLE[veredictoGlobalKey] || GLOBAL_STAMP_STYLE['CUMPLE_PARCIAL']

  const weeksList: DetalleSemanal[] = concordance.detalle_semanal || concordance.weeks || []
  const findings: string[] = concordance.key_findings || (concordance.semanas?.observaciones || [])

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Encabezado y Sello Global */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Correspondencia Curricular v1.2</h1>
          <p className="text-gray-600 text-sm mt-1">
            Análisis de trazabilidad semana a semana y cobertura de subtemas atómicos.
          </p>
        </div>

        {/* Sello de Veredicto Global (Elemento firma de la UI: recuadro doble borde con ligera rotación) */}
        <div
          className={`relative transform -rotate-1 border-4 border-double ${stamp.border} ${stamp.bg} p-4 rounded-xl shadow-sm text-center min-w-[240px]`}
        >
          <span className={`inline-block text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded ${stamp.badgeBg} mb-1`}>
            SELLO PEDAGÓGICO
          </span>
          <h2 className={`text-lg font-extrabold ${stamp.text}`}>{stamp.label}</h2>
          <p className="text-xs text-gray-600 mt-1 font-medium">{concordance.resumen}</p>
        </div>
      </div>

      {/* Tarjetas resumen de documentos */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <span>📋</span> Sílabo (Microplanificación)
          </h2>
          <InfoRow label="Asignatura" value={silabo.subject} />
          <InfoRow label="Docente" value={silabo.teacher} />
          <InfoRow label="Grado" value={silabo.grade} />
          <InfoRow label="Unidad" value={silabo.unit_name} />
          <InfoRow label="Trimestre / Parcial" value={`${silabo.trimester || '1'} / ${silabo.parcial || '1'}`} />
          <InfoRow label="Fechas" value={`${silabo.start_date} – ${silabo.end_date}`} />
          <InfoRow label="Semanas planificadas" value={String(silabo.weeks.length)} />
          {silabo.warnings.map((w) => (
            <p key={w} className="text-amber-700 text-xs mt-2">⚠ {w}</p>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <span>📖</span> Material Pedagógico (Guía)
          </h2>
          <InfoRow label="Asignatura" value={guia.subject} />
          <InfoRow label="Grado" value={guia.grade} />
          <InfoRow label="Páginas totales" value={String(guia.total_pages)} />
          <InfoRow label="Semanas con desarrollo" value={guia.weeks_detected.join(', ') || '(ninguna)'} />
          {guia.warnings.map((w) => (
            <p key={w} className="text-amber-700 text-xs mt-2">⚠ {w}</p>
          ))}
        </div>
      </div>

      {/* Hallazgos clave */}
      {findings.length > 0 && (
        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
          <h2 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
            <span>💡</span> Hallazgos e Incidencias Clave
          </h2>
          <ul className="list-disc list-inside text-sm text-amber-800 space-y-1">
            {findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Matriz Semanal Expandible */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">Matriz de Trazabilidad Curricular por Semana</h2>
          <span className="text-xs text-gray-500">Haga clic en una semana para ver sus subtemas</span>
        </div>

        <div className="divide-y divide-gray-100">
          {weeksList.map((w) => {
            const wn = w.semana ?? w.week_number ?? 0
            const statusKey = w.veredicto_semana || w.status || 'NO_CUMPLE'
            const statusStyle = WEEK_STATUS_STYLE[statusKey] || WEEK_STATUS_STYLE['NO_CUMPLE']
            const isExpanded = !!expandedWeeks[wn]
            const coberturaPct = Math.round((w.matriz_subtemas?.cobertura || 0) * 100)

            return (
              <div key={wn} className="transition-colors hover:bg-gray-50/50">
                {/* Fila Principal */}
                <div
                  className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 cursor-pointer"
                  onClick={() => toggleWeek(wn)}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-extrabold text-gray-800 text-lg w-8">S{wn}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 text-sm">{w.tema_silabo || w.topic}</h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {w.desarrollada_en_material !== false ? (
                          <span>Págs. {w.page_range_guia || 'desarrolladas'} · Cobertura: <strong>{coberturaPct}%</strong> ({w.matriz_subtemas?.cubiertos || 0}/{w.matriz_subtemas?.total || 0} subtemas)</span>
                        ) : (
                          <span className="text-rose-600 font-semibold">Sin lección desarrollada en la guía</span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${statusStyle.className}`}>
                      {statusStyle.label}
                    </span>
                    <button type="button" className="text-gray-400 hover:text-gray-600 text-sm">
                      {isExpanded ? '▲' : '▼'}
                    </button>
                  </div>
                </div>

                {/* Detalle Expandible */}
                {isExpanded && (
                  <div className="bg-gray-50/80 p-4 border-t border-gray-100 space-y-3 text-sm">
                    {/* Matriz de Subtemas */}
                    {w.matriz_subtemas?.subtemas && w.matriz_subtemas.subtemas.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-xs text-gray-700 uppercase tracking-wider mb-2">
                          Subtemas Atómicos ({w.matriz_subtemas.cubiertos}/{w.matriz_subtemas.total} cubiertos)
                        </h4>
                        <div className="space-y-1.5">
                          {w.matriz_subtemas.subtemas.map((sub, i) => {
                            let badge = <span className="text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-xs font-bold">❌ AUSENTE</span>
                            if (sub.estado === 'CUBIERTO') {
                              badge = <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-xs font-bold">✅ CUBIERTO</span>
                            } else if (sub.estado === 'MENCIONADO') {
                              badge = <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-xs font-bold">⚠️ MENCIONADO</span>
                            }
                            return (
                              <div key={i} className="bg-white p-2.5 rounded-lg border border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                <span className="font-medium text-gray-800 capitalize">{sub.texto}</span>
                                <div className="flex items-center gap-2">
                                  {badge}
                                  {sub.evidencia && <span className="text-xs text-gray-500 italic">({sub.evidencia})</span>}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* Notas Informativas Neutras (ℹ️ gris neutro) */}
                    {w.notas_informativas && w.notas_informativas.length > 0 && (
                      <div className="bg-slate-100 border border-slate-200 text-slate-800 p-3 rounded-lg text-xs space-y-1">
                        <span className="font-semibold text-slate-900 block mb-1">ℹ️ Notas Informativas de Estilo (Sin penalización):</span>
                        {w.notas_informativas.map((note, idx) => (
                          <p key={idx}>{note}</p>
                        ))}
                      </div>
                    )}

                    {/* Coherencia Transversal */}
                    {w.coherencia && (
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-1">
                        <div className={`p-2 rounded border ${w.coherencia.fechas?.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'}`}>
                          <strong>Fechas:</strong> {w.coherencia.fechas?.detalle}
                        </div>
                        <div className={`p-2 rounded border ${w.coherencia.periodos?.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'}`}>
                          <strong>Períodos:</strong> {w.coherencia.periodos?.detalle}
                        </div>
                        <div className={`p-2 rounded border ${w.coherencia.codigos_competencia?.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'}`}>
                          <strong>Códigos:</strong> {w.coherencia.codigos_competencia?.detalle}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Compuerta Módulo 3 (Generación de Herramientas Didácticas) */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Sección: Herramientas Didácticas (Módulo 3)</h2>
          <p className="text-xs text-gray-500">
            Regla de compuerta v1.2: Únicamente las semanas con veredicto <strong>CUMPLE</strong> están habilitadas para generar recursos.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
          {weeksList.map((w) => {
            const wn = w.semana ?? w.week_number ?? 0
            const canGen = w.habilita_generacion ?? (w.veredicto_semana === 'CUMPLE' || w.status === 'CONCORDANTE')

            return (
              <div
                key={wn}
                className={`p-3 rounded-lg border flex flex-col justify-between space-y-2 ${
                  canGen ? 'border-emerald-300 bg-emerald-50/30' : 'border-gray-200 bg-gray-50 opacity-70'
                }`}
              >
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-xs text-gray-800">Semana {wn}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${canGen ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-200 text-gray-600'}`}>
                      {canGen ? 'HABILITADA' : 'BLOQUEADA'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 line-clamp-2">{w.tema_silabo || w.topic}</p>
                </div>

                {canGen ? (
                  <button
                    type="button"
                    onClick={() => onContinue(wn)}
                    className="w-full text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white py-1.5 rounded-md shadow-sm transition-colors"
                  >
                    Generar Recursos →
                  </button>
                ) : (
                  <div className="relative group">
                    <button
                      type="button"
                      disabled
                      className="w-full text-xs font-semibold bg-gray-200 text-gray-400 py-1.5 rounded-md cursor-not-allowed"
                    >
                      Bloqueado
                    </button>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 hidden group-hover:block w-48 p-2 bg-gray-900 text-white text-[10px] rounded shadow-lg z-10 text-center">
                      Corrige el material de esta semana para habilitar la generación
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <button type="button" className="text-gray-500 hover:text-gray-800 text-sm font-medium pt-2" onClick={onBack}>
        ← Volver a cargar documentos
      </button>
    </div>
  )
}
