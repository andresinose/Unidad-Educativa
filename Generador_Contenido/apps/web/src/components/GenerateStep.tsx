import { useState } from 'react'
import { INTENTS, type PedagogicalIntent } from '../lib/types'
import CanvasTaskGenerator from './CanvasTaskGenerator'

const INTENT_LABELS: Record<PedagogicalIntent, string> = {
  presentar: 'Presentar el tema',
  comprender: 'Facilitar la comprensión',
  visualizar: 'Visualizar un proceso',
  practicar: 'Practicar un procedimiento',
  aplicar: 'Aplicar el contenido',
  resolver: 'Resolver un problema',
  analizar: 'Analizar una situación',
  comparar: 'Comparar conceptos',
  experimentar: 'Experimentar',
  reforzar: 'Reforzar',
  comprobar: 'Comprobar la comprensión',
  evaluar: 'Evaluar formativamente',
}

interface Props {
  weekNumber: number
  weekTopic: string
  loading: boolean
  error: string | null
  onGenerate: (intent: PedagogicalIntent, extraInstructions: string) => void
  onBack: () => void
}

export default function GenerateStep({ weekNumber, weekTopic, loading, error, onGenerate, onBack }: Props) {
  const [intent, setIntent] = useState<PedagogicalIntent | null>(null)
  const [extra, setExtra] = useState('')
  const [isTaskMode, setIsTaskMode] = useState(false)

  if (isTaskMode) {
    return (
      <CanvasTaskGenerator
        initialTitle={`Tarea Semana ${weekNumber}: ${weekTopic}`}
        initialIndicaciones={`1. Revisa detenidamente el contenido planificado para la Semana ${weekNumber} (${weekTopic}).\n2. Desarrolla las actividades propuestas en tu cuaderno.\n3. Asegúrate de presentar tus respuestas de forma clara y ordenada.`}
        onBack={() => setIsTaskMode(false)}
      />
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <h1 className="text-2xl font-bold mb-1">Generar recurso didáctico</h1>
          <p className="text-gray-600">
            Semana {weekNumber} — {weekTopic}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsTaskMode(true)}
          className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer flex items-center gap-1.5"
        >
          <span>📝 Crear Tarea Canvas Formateada</span>
        </button>
      </div>

      <label className="block font-medium mb-2">¿Qué desea lograr con este recurso?</label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-6">
        {INTENTS.map((i) => (
          <button
            key={i}
            type="button"
            className={`rounded-lg border px-3 py-2 text-sm text-left ${
              intent === i ? 'border-blue-600 bg-blue-50 font-semibold' : 'border-gray-300 bg-white hover:bg-gray-50'
            }`}
            onClick={() => setIntent(i)}
          >
            {INTENT_LABELS[i]}
          </button>
        ))}
      </div>

      <label htmlFor="extra" className="block font-medium mb-2">
        Instrucciones adicionales (opcional)
      </label>
      <textarea
        id="extra"
        className="w-full rounded-lg border border-gray-300 p-2 mb-6"
        rows={3}
        placeholder="Ej. enfocarlo en estudiantes con necesidades de apoyo visual…"
        value={extra}
        onChange={(e) => setExtra(e.target.value)}
      />

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm p-3">{error}</div>
      )}

      <div className="flex items-center gap-3">
        <button type="button" className="text-gray-500 hover:text-gray-800 text-sm" onClick={onBack}>
          ← Resultados
        </button>
        <button
          type="button"
          disabled={!intent || loading}
          className="ml-auto rounded-lg bg-blue-600 text-white px-6 py-3 font-semibold disabled:bg-gray-300 hover:bg-blue-700"
          onClick={() => intent && onGenerate(intent, extra)}
        >
          {loading ? 'Generando…' : 'Generar recurso'}
        </button>
      </div>
    </div>
  )
}
