import React, { useState } from 'react'
import type { ActivitiesUploadResponse, GeneratedResource, SilaboWeek } from '../lib/types'
import { downloadActivityPdf, generateActivity, uploadActivitiesSilabo } from '../lib/api'

interface ActividadesViewProps {
  onBackToMenu: () => void
}

export const ActividadesView: React.FC<ActividadesViewProps> = ({ onBackToMenu }) => {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadData, setUploadData] = useState<ActivitiesUploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [selectedWeek, setSelectedWeek] = useState<number | null>(null)
  const [resourceType, setResourceType] = useState<'crossword' | 'logic_puzzle' | 'word_search' | 'flashcards'>('crossword')
  const [extraInstructions, setExtraInstructions] = useState('')
  const [generating, setGenerating] = useState(false)
  const [resource, setResource] = useState<GeneratedResource | null>(null)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setUploading(true)
    setError(null)
    setResource(null)

    try {
      const data = await uploadActivitiesSilabo(file)
      setUploadData(data)
      if (data.silabo.weeks.length > 0) {
        setSelectedWeek(data.silabo.weeks[0].week_number)
      }
    } catch (err: any) {
      setError(err.message || 'Error al subir y procesar el documento de planificación.')
    } finally {
      setUploading(false)
    }
  }

  const handleGenerate = async () => {
    if (!uploadData || selectedWeek === null) return

    setGenerating(true)
    setError(null)
    setResource(null)

    try {
      const res = await generateActivity(
        uploadData.session_id,
        selectedWeek,
        resourceType,
        extraInstructions
      )
      setResource(res)
    } catch (err: any) {
      setError(err.message || 'Error al generar la actividad lúdica.')
    } finally {
      setGenerating(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (!uploadData) return
    setDownloadingPdf(true)
    try {
      await downloadActivityPdf(uploadData.session_id)
    } catch (err: any) {
      setError(err.message || 'Error al descargar el archivo PDF.')
    } finally {
      setDownloadingPdf(false)
    }
  }

  const currentWeekObj: SilaboWeek | undefined = uploadData?.silabo.weeks.find(
    (w) => w.week_number === selectedWeek
  )

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🎮</span>
              <h1 className="text-2xl font-bold text-slate-900">
                Generador de Actividades Lúdicas
              </h1>
            </div>
            <p className="text-slate-600 text-sm mt-1">
              Crea crucigramas, rompecabezas de lógica, sopas de letras y flashcards autónomos a partir de tu planificación curricular.
            </p>
          </div>
          <button
            onClick={onBackToMenu}
            className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-300 self-start sm:self-auto"
          >
            ← Menú Principal
          </button>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-lg shadow-sm">
            <div className="flex items-center gap-2 text-rose-800 font-medium">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Nivel Switcher Notice */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🎓</span>
            <div>
              <span className="font-semibold text-emerald-900">Nivel Educativo Actual: </span>
              <span className="text-emerald-800 font-bold">Educación General Básica (EGB)</span>
            </div>
          </div>
          <span className="text-xs bg-emerald-200 text-emerald-800 font-semibold px-2.5 py-1 rounded-full">
            Fase 2: Educación Inicial (Próximamente)
          </span>
        </div>

        {/* Step 1: Upload Planificación */}
        {!uploadData && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <span>1️⃣</span> Cargar Planificación Curricular (.docx)
            </h2>
            <p className="text-sm text-slate-600">
              Sube el documento del Sílabo o Planificación Semanal en formato Word.
            </p>

            <form onSubmit={handleUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-8 text-center bg-slate-50 transition-colors cursor-pointer">
                <input
                  type="file"
                  accept=".docx"
                  onChange={handleFileChange}
                  className="hidden"
                  id="silabo-activities-input"
                />
                <label htmlFor="silabo-activities-input" className="cursor-pointer block">
                  <span className="text-4xl block mb-2">📄</span>
                  <span className="text-sm font-semibold text-slate-700 block">
                    {file ? file.name : 'Haz clic para seleccionar o arrastra tu archivo .docx'}
                  </span>
                  <span className="text-xs text-slate-500 block mt-1">
                    Solo archivos de Microsoft Word (.docx) de hasta 50 MB
                  </span>
                </label>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!file || uploading}
                  className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <span className="animate-spin">🌀</span> Procesando Sílabo...
                    </>
                  ) : (
                    'Cargar y Extraer Semanas →'
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 2 & 3: Selection and Generation */}
        {uploadData && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <span>2️⃣</span> Configurar Recurso Lúdico
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Asignatura: <strong className="text-slate-700">{uploadData.silabo.subject || 'N/A'}</strong> | Grado:{' '}
                  <strong className="text-slate-700">{uploadData.silabo.grade || 'N/A'}</strong>
                </p>
              </div>
              <button
                onClick={() => {
                  setUploadData(null)
                  setFile(null)
                  setResource(null)
                }}
                className="text-xs text-rose-600 hover:text-rose-800 font-semibold"
              >
                🔄 Cambiar Sílabo
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Selector de Semana */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Seleccionar Semana del Sílabo:
                </label>
                <select
                  value={selectedWeek ?? ''}
                  onChange={(e) => setSelectedWeek(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  {uploadData.silabo.weeks.map((w) => (
                    <option key={w.week_number} value={w.week_number}>
                      Semana {w.week_number}: {w.topic}
                    </option>
                  ))}
                </select>
                {currentWeekObj && (
                  <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 space-y-1">
                    <p>
                      <strong>Contenido:</strong> {currentWeekObj.methodology_phases?.construccion || '(no especificado)'}
                    </p>
                  </div>
                )}
              </div>

              {/* Selector de Tipo de Recurso */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Tipo de Actividad Lúdica:
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'crossword', label: '🧩 Crucigrama', desc: 'Pistas y grilla de intersección' },
                    { id: 'logic_puzzle', label: '🧩 Lógica & Relación', desc: 'Emparejamiento / Secuencia' },
                    { id: 'word_search', label: '🔍 Sopa de Letras', desc: 'Vocabulario interactivo' },
                    { id: 'flashcards', label: '🎴 Tarjetas 3D', desc: 'Repaso con giratorio' },
                  ].map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setResourceType(item.id as any)}
                      className={`p-3 text-left border rounded-lg transition-all ${
                        resourceType === item.id
                          ? 'border-emerald-600 bg-emerald-50 text-emerald-900 ring-2 ring-emerald-500/20'
                          : 'border-slate-200 hover:border-slate-300 bg-white text-slate-700'
                      }`}
                    >
                      <span className="font-bold text-sm block">{item.label}</span>
                      <span className="text-xs text-slate-500 block mt-0.5">{item.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Extra instructions */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Instrucciones Adicionales (Opcional):
              </label>
              <input
                type="text"
                value={extraInstructions}
                onChange={(e) => setExtraInstructions(e.target.value)}
                placeholder="Ej. Enfocar en términos de ecuaciones lineales, incluir al menos 8 palabras..."
                className="w-full border border-slate-300 rounded-lg p-2.5 text-sm bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>

            {/* Action button */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={generating}
                className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold rounded-lg shadow-sm transition-colors flex items-center gap-2 text-sm"
              >
                {generating ? (
                  <>
                    <span className="animate-spin">🌀</span> Generando Actividad...
                  </>
                ) : (
                  '✨ Generar Actividad Lúdica'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Preview & Download */}
        {resource && resource.blocks.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <span>🎉</span> Vista Previa Interactiva: {resource.title}
                </h2>
                <p className="text-xs text-slate-500">
                  Semana {resource.week_number} — Probar interactividad directamente en pantalla.
                </p>
              </div>
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold rounded-lg text-sm transition-colors flex items-center gap-2"
              >
                {downloadingPdf ? 'Descargando...' : '📥 Descargar PDF para Imprimir'}
              </button>
            </div>

            {/* Iframe preview */}
            <div className="border border-slate-300 rounded-xl overflow-hidden bg-slate-100 min-h-[500px]">
              <iframe
                title="Preview Actividad Lúdica"
                srcDoc={resource.blocks[0].rendered_html}
                className="w-full h-[600px] border-none"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
