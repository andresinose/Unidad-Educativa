import React, { useEffect, useState } from 'react'
import { downloadMaterial, downloadMaterialZip, getConversionJob, listMaterials, materialPreviewUrl, uploadMaterialPdf } from '../lib/api'
import type { ConversionJob, Material } from '../lib/types'
import CanvasTaskGenerator from './CanvasTaskGenerator'

export default function GeneratorView() {
  const [mode, setMode] = useState<'pdf' | 'tarea'>('pdf')
  const [file, setFile] = useState<File | null>(null)
  const [job, setJob] = useState<ConversionJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [materials, setMaterials] = useState<Material[]>([])
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null)
  const [uploading, setUploading] = useState<boolean>(false)

  // Load existing materials on mount
  useEffect(() => {
    fetchMaterials()
  }, [])

  async function fetchMaterials() {
    try {
      const data = await listMaterials()
      setMaterials(data)
      if (data.length > 0 && !selectedMaterial) {
        setSelectedMaterial(data[0])
      }
    } catch {
      // Ignore initial list error
    }
  }

  // Poll active conversion job
  useEffect(() => {
    if (!job || job.estado !== 'procesando') return

    const interval = setInterval(async () => {
      try {
        const updated = await getConversionJob(job.id)
        setJob(updated)
        if (updated.estado === 'completado') {
          clearInterval(interval)
          setUploading(false)
          fetchMaterials()
        } else if (updated.estado === 'error') {
          clearInterval(interval)
          setUploading(false)
          setError(updated.error || 'Ocurrió un error en la conversión del archivo.')
        }
      } catch (err: any) {
        clearInterval(interval)
        setUploading(false)
        setError(err.message || 'Fallo de conexión al verificar el trabajo.')
      }
    }, 1500)

    return () => clearInterval(interval)
  }, [job])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0]
      if (!f.name.toLowerCase().endsWith('.pdf')) {
        setError('Por favor selecciona un archivo en formato PDF (.pdf).')
        return
      }
      setFile(f)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const newJob = await uploadMaterialPdf(file)
      setJob(newJob)
    } catch (err: any) {
      setUploading(false)
      setError(err.message || 'Fallo al subir el archivo PDF.')
    }
  }

  if (mode === 'tarea') {
    return (
      <div className="space-y-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="bg-slate-100 p-1 rounded-2xl flex items-center gap-1 border border-slate-200">
            <button
              type="button"
              onClick={() => setMode('pdf')}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 cursor-pointer transition-all"
            >
              📄 Conversor de PDF a HTML
            </button>
            <button
              type="button"
              onClick={() => setMode('tarea')}
              className="px-4 py-2 bg-white rounded-xl text-xs font-bold text-slate-900 shadow-xs cursor-pointer transition-all"
            >
              📝 Generador de Tareas Canvas
            </button>
          </div>
        </div>
        <CanvasTaskGenerator onBack={() => setMode('pdf')} />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Module Title Banner */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex items-center justify-between flex-wrap gap-4">
        <div>
          <span className="px-3 py-1 bg-amber-100 text-amber-900 rounded-full text-xs font-bold uppercase tracking-wider">
            Generador de Contenidos Didácticos
          </span>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-2">Herramientas Didácticas para Canvas LMS</h2>
          <p className="text-sm text-slate-600 mt-1">
            Convierte libros en PDF o genera Tareas oficiales formateadas con el encabezado institucional UEI.
          </p>
        </div>

        <div className="bg-slate-100 p-1.5 rounded-2xl flex items-center gap-1 border border-slate-200">
          <button
            type="button"
            onClick={() => setMode('pdf')}
            className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer transition-all ${
              mode === 'pdf' ? 'bg-blue-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            📄 Conversor de PDF
          </button>
          <button
            type="button"
            onClick={() => setMode('tarea')}
            className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer transition-all ${
              mode === 'tarea' ? 'bg-blue-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            📝 Crear Tarea Canvas
          </button>
        </div>
      </div>

      {/* PDF Upload Dropzone Card */}
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm">
        <h3 className="text-lg font-bold text-slate-800 mb-4">1. Subir Libro o Folleto Pedagógico (PDF)</h3>

        <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-blue-600 transition-colors bg-slate-50/50">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
            id="pdf-input"
          />
          <label htmlFor="pdf-input" className="cursor-pointer block">
            <div className="text-4xl mb-3">📄</div>
            <span className="text-sm font-semibold text-slate-700 block">
              {file ? file.name : 'Haz clic aquí o arrastra tu archivo PDF (máx. 50 MB)'}
            </span>
            <span className="text-xs text-slate-400 mt-1 block">Formato aceptado: .pdf</span>
          </label>
        </div>

        {file && !uploading && (
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleUpload}
              className="px-6 py-2.5 bg-blue-700 hover:bg-blue-800 text-white font-bold text-sm rounded-xl shadow-sm transition-all cursor-pointer flex items-center gap-2"
            >
              <span>🚀 Iniciar conversión con visión</span>
            </button>
          </div>
        )}

        {/* Conversion Progress Bar */}
        {job && job.estado === 'procesando' && (
          <div className="mt-6 p-5 bg-blue-50 border border-blue-200 rounded-2xl">
            <div className="flex items-center justify-between text-xs font-bold text-blue-900 mb-2">
              <span>Convirtiendo documento...</span>
              <span>
                Página {job.pagina_actual} de {job.total_paginas || '?'}
              </span>
            </div>
            <div className="w-full bg-blue-200 h-3 rounded-full overflow-hidden">
              <div
                className="bg-blue-700 h-full transition-all duration-500 rounded-full"
                style={{
                  width: `${job.total_paginas ? Math.min(100, (job.pagina_actual / job.total_paginas) * 100) : 10}%`,
                }}
              />
            </div>
            <p className="text-xs text-blue-700 mt-2">
              Transcribiendo estructuras pedagógicas, tablas e ilustraciones a bloques didácticos seguros...
            </p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-sm font-medium flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Materials List and Interactive Preview */}
      {materials.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
          <h3 className="text-lg font-bold text-slate-800">2. Materiales Convertidos Disponibles</h3>

          {/* Chips Selector */}
          <div className="flex items-center gap-3 overflow-x-auto pb-2">
            {materials.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setSelectedMaterial(m)}
                className={`px-4 py-2 rounded-xl text-xs font-bold cursor-pointer border transition-all shrink-0 ${
                  selectedMaterial?.id === m.id
                    ? 'bg-blue-900 text-white border-blue-900 shadow-xs'
                    : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                }`}
              >
                {m.title || `Material ${m.id}`} ({m.pages} pág.)
              </button>
            ))}
          </div>

          {/* Selected Material Action Header */}
          {selectedMaterial && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-3 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <div>
                  <h4 className="font-bold text-slate-900 text-base">{selectedMaterial.title}</h4>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                    {selectedMaterial.subject && <span>Materia: {selectedMaterial.subject}</span>}
                    {selectedMaterial.grade && <span>• Grado: {selectedMaterial.grade}</span>}
                    <span>• {selectedMaterial.pages} Páginas</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <a
                    href={materialPreviewUrl(selectedMaterial.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3.5 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold text-xs rounded-xl transition-all inline-flex items-center gap-1.5"
                  >
                    <span>↗ Abrir pestaña</span>
                  </a>
                  <button
                    type="button"
                    onClick={() => downloadMaterialZip(selectedMaterial)}
                    className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <span>📦 Descargar Paquete ZIP (HTML + CSS + JS)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadMaterial(selectedMaterial)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <span>📄 Descargar HTML Único</span>
                  </button>
                </div>
              </div>

              {/* iFrame Interactive Preview */}
              <div className="border border-slate-300 rounded-2xl overflow-hidden shadow-inner bg-slate-100">
                <iframe
                  src={materialPreviewUrl(selectedMaterial.id)}
                  title="Vista Previa de Material Interactivo"
                  className="w-full h-[620px] border-none"
                  sandbox="allow-scripts allow-same-origin allow-downloads"
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
