import { useState } from 'react'
import MenuInicial from './components/MenuInicial'
import GeneratorView from './components/GeneratorView'
import UploadStep from './components/UploadStep'
import ConcordanceStep from './components/ConcordanceStep'
import GenerateStep from './components/GenerateStep'
import DownloadStep from './components/DownloadStep'
import { analyzeDocuments, generateResource, ApiError } from './lib/api'
import type { AnalyzeResponse, GeneratedResource, PedagogicalIntent } from './lib/types'

type Modulo = 'menu' | 'validador' | 'generador'
type Step = 1 | 2 | 3 | 4

const MODULO_LABELS: Record<Exclude<Modulo, 'menu'>, string> = {
  validador: 'Validador de Contenidos Curriculares',
  generador: 'Generador de Contenidos Didácticos',
}

const STEP_LABELS: Record<Step, string> = {
  1: 'Cargar documentos',
  2: 'Revisar y validar',
  3: 'Generar recurso',
  4: 'Exportar',
}

function StepIndicator({ current }: { current: Step }) {
  return (
    <nav className="flex items-center justify-center gap-2 py-4 text-sm">
      {([1, 2, 3, 4] as Step[]).map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full ${
              s === current ? 'bg-blue-600 text-white font-semibold' : s < current ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                s === current ? 'bg-white text-blue-600' : s < current ? 'bg-blue-100' : 'bg-gray-200'
              }`}
            >
              {s < current ? '✓' : s}
            </span>
            {STEP_LABELS[s]}
          </div>
          {i < 3 && <span className="text-gray-300">—</span>}
        </div>
      ))}
    </nav>
  )
}

export default function App() {
  const [modulo, setModulo] = useState<Modulo>('menu')
  
  // Validador State (Preserved when navigating to menu)
  const [step, setStep] = useState<Step>(1)
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null)
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null)
  const [resource, setResource] = useState<GeneratedResource | null>(null)

  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)

  async function handleAnalyze(silabo: File, guia: File) {
    setAnalyzing(true)
    setAnalyzeError(null)
    try {
      const result = await analyzeDocuments(silabo, guia)
      setAnalysis(result)
      setStep(2)
    } catch (e) {
      setAnalyzeError(e instanceof ApiError ? e.message : 'No se pudo analizar los documentos.')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleGenerate(intent: PedagogicalIntent, extraInstructions: string) {
    if (!analysis || selectedWeek === null) return
    setGenerating(true)
    setGenerateError(null)
    try {
      const result = await generateResource(analysis.session_id, selectedWeek, intent, extraInstructions)
      setResource(result)
      setStep(4)
    } catch (e) {
      setGenerateError(e instanceof ApiError ? e.message : 'No se pudo generar el recurso.')
    } finally {
      setGenerating(false)
    }
  }

  function restartValidador() {
    setStep(1)
    setAnalysis(null)
    setSelectedWeek(null)
    setResource(null)
    setAnalyzeError(null)
    setGenerateError(null)
  }

  // 1. Initial Menu Screen
  if (modulo === 'menu') {
    return <MenuInicial onSelect={setModulo} />
  }

  const weeksList = analysis?.concordance.detalle_semanal || analysis?.concordance.weeks || []
  const selectedWeekTopic =
    (selectedWeek !== null && weeksList.find((w) => (w.semana ?? w.week_number) === selectedWeek)?.tema_silabo) || ''

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Top Header with Back to Main Menu button */}
      <header className="border-b border-slate-200" style={{ background: '#0a2f68' }}>
        <div className="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setModulo('menu')}
              className="text-xs font-bold text-white/90 hover:text-white border border-white/30 hover:border-white/60 bg-white/10 rounded-xl px-3.5 py-2 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span>← Menú principal</span>
            </button>
            <div>
              <h1 className="font-extrabold text-base sm:text-lg text-white">Unidad Educativa Bilingüe Indoamérica</h1>
              <p className="text-xs font-bold" style={{ color: '#5ecfb1' }}>
                {MODULO_LABELS[modulo]}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Module 2: Generador de Contenidos */}
      {modulo === 'generador' && (
        <main className="px-4 py-8 pb-16">
          <GeneratorView />
        </main>
      )}

      {/* Module 1: Validador de Contenidos (Preserved Flow) */}
      {modulo === 'validador' && (
        <>
          <StepIndicator current={step} />
          <main className="px-4 pb-16">
            {step === 1 && <UploadStep onSubmit={handleAnalyze} loading={analyzing} error={analyzeError} />}
            {step === 2 && analysis && (
              <ConcordanceStep
                data={analysis}
                onBack={restartValidador}
                onContinue={(weekNumber) => {
                  setSelectedWeek(weekNumber)
                  setStep(3)
                }}
              />
            )}
            {step === 3 && selectedWeek !== null && (
              <GenerateStep
                weekNumber={selectedWeek}
                weekTopic={selectedWeekTopic}
                loading={generating}
                error={generateError}
                onGenerate={handleGenerate}
                onBack={() => setStep(2)}
              />
            )}
            {step === 4 && resource && (
              <DownloadStep resource={resource} onBack={() => setStep(3)} onRestart={restartValidador} />
            )}
          </main>
        </>
      )}
    </div>
  )
}
