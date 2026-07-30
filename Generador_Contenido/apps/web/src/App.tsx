import { useState } from 'react'
import UploadStep from './components/UploadStep'
import ConcordanceStep from './components/ConcordanceStep'
import GenerateStep from './components/GenerateStep'
import DownloadStep from './components/DownloadStep'
import { analyzeDocuments, generateResource, ApiError } from './lib/api'
import type { AnalyzeResponse, GeneratedResource, PedagogicalIntent } from './lib/types'

type Step = 1 | 2 | 3 | 4

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

  function restart() {
    setStep(1)
    setAnalysis(null)
    setSelectedWeek(null)
    setResource(null)
    setAnalyzeError(null)
    setGenerateError(null)
  }

  const weeksList = analysis?.concordance.detalle_semanal || analysis?.concordance.weeks || []
  const selectedWeekTopic =
    (selectedWeek !== null && weeksList.find((w) => (w.semana ?? w.week_number) === selectedWeek)?.tema_silabo) || ''

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <h1 className="font-bold text-lg text-gray-900">Unidad Educativa Bilingüe Indoamérica</h1>
          <p className="text-sm text-gray-500">Validador Pedagógico Curricular (Especificación v1.2)</p>
        </div>
      </header>
      <StepIndicator current={step} />
      <main className="px-4 pb-16">
        {step === 1 && <UploadStep onSubmit={handleAnalyze} loading={analyzing} error={analyzeError} />}
        {step === 2 && analysis && (
          <ConcordanceStep
            data={analysis}
            onBack={restart}
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
          <DownloadStep resource={resource} onBack={() => setStep(3)} onRestart={restart} />
        )}
      </main>
    </div>
  )
}
