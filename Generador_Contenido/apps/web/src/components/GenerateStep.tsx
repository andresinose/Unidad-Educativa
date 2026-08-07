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

const RESOURCE_TYPES = [
  { id: 'crucigrama', name: 'Crucigrama Interactivo', icon: '🧩', desc: 'Grilla interactiva con pistas horizontales y verticales' },
  { id: 'sopa', name: 'Sopa de Letras', icon: '🔠', desc: 'Búsqueda de términos clave en grilla interactiva' },
  { id: 'flashcards', name: 'Tarjetas de Estudio 3D', icon: '🃏', desc: 'Flashcards giratorias 3D para repaso de conceptos' },
  { id: 'logica', name: 'Rompecabezas de Lógica', icon: '🧠', desc: 'Emparejar columnas o secuencia lógica de pasos' },
  { id: 'diagrama', name: 'Mapa Conceptual SVG', icon: '📊', desc: 'Esquema visual de nodos y secuencias de aprendizaje' },
  { id: 'guia', name: 'Guía de Estudio Sintética', icon: '📋', desc: 'Ficha infográfica con secciones, viñetas e ideas clave' },
  { id: 'cuestionario', name: 'Cuestionario Interactivo', icon: '❓', desc: 'Autoevaluación con preguntas de opción múltiple' },
  { id: 'auto', name: 'Selección Automática por IA', icon: '🪄', desc: 'La IA elige el formato más adecuado según la intención' },
]

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
  const [selectedResourceType, setSelectedResourceType] = useState<string>('auto')
  const [customPrompt, setCustomPrompt] = useState('')
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

  const handleExecuteGenerate = () => {
    if (!intent) return
    let instructions = ''
    if (selectedResourceType !== 'auto') {
      const found = RESOURCE_TYPES.find((r) => r.id === selectedResourceType)
      instructions = `El docente solicitó generar un ${found?.name || selectedResourceType}.`
    }
    if (customPrompt.trim()) {
      instructions += ` ${customPrompt.trim()}`
    }
    onGenerate(intent, instructions.trim())
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1 text-slate-900">Generar recurso didáctico</h1>
          <p className="text-slate-600 text-sm">
            Semana {weekNumber} — <span className="font-semibold">{weekTopic}</span>
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

      {/* 1. Intención pedagógica */}
      <div className="mb-6">
        <label className="block font-semibold text-slate-800 mb-2 text-sm">
          1. Seleccione la intención pedagógica del recurso:
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {INTENTS.map((i) => (
            <button
              key={i}
              type="button"
              className={`rounded-xl border p-2.5 text-xs text-left transition-all cursor-pointer ${
                intent === i
                  ? 'border-blue-600 bg-blue-50 text-blue-900 font-bold shadow-xs ring-1 ring-blue-500/30'
                  : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
              }`}
              onClick={() => setIntent(i)}
            >
              {INTENT_LABELS[i]}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Seleccionar el tipo de recurso lúdico */}
      <div className="mb-6">
        <label className="block font-semibold text-slate-800 mb-2 text-sm">
          2. Seleccione el formato de recurso lúdico / interactivo a generar:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {RESOURCE_TYPES.map((type) => (
            <button
              key={type.id}
              type="button"
              onClick={() => setSelectedResourceType(type.id)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                selectedResourceType === type.id
                  ? 'border-blue-600 bg-blue-50/80 ring-2 ring-blue-500/20'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xl">{type.icon}</span>
                  <span className="font-bold text-xs text-slate-900">{type.name}</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">{type.desc}</p>
              </div>
              {selectedResourceType === type.id && (
                <span className="mt-2 text-[10px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full w-fit">
                  Seleccionado
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Indicaciones adicionales opcionales */}
      <div className="mb-6">
        <label htmlFor="customPrompt" className="block text-xs font-semibold text-slate-600 mb-1">
          Indicaciones didácticas específicas (opcional)
        </label>
        <input
          type="text"
          id="customPrompt"
          className="w-full rounded-xl border border-slate-200 p-2.5 text-xs text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder="Ej. Enfatizar vocabulario de la fase de construcción, incluir caso práctico de la vida real..."
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
        />
      </div>

      {error && (
        <div className="mb-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3 font-medium">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3 pt-2">
        <button type="button" className="text-slate-500 hover:text-slate-800 text-xs font-medium" onClick={onBack}>
          ← Resultados
        </button>
        <button
          type="button"
          disabled={!intent || loading}
          className="ml-auto rounded-xl bg-blue-600 text-white px-6 py-3 font-semibold text-sm disabled:bg-slate-300 hover:bg-blue-700 shadow-sm transition-all cursor-pointer"
          onClick={handleExecuteGenerate}
        >
          {loading ? 'Generando recurso…' : '✨ Generar recurso'}
        </button>
      </div>
    </div>
  )
}
