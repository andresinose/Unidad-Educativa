import React, { useState } from 'react'

interface Props {
  initialTitle?: string
  initialIndicaciones?: string
  onBack?: () => void
}

export function generateCanvasTaskHtml(
  _nombreTarea: string,
  indicaciones: string,
  entregables: string,
  calificacion: string
): string {
  const parseListItems = (text: string, accentColor: string = '#0a2f68') => {
    if (!text.trim()) return '<p style="color: #64748b; font-style: italic;">Sin especificación.</p>'
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)

    const items = lines
      .map((l, idx) => {
        const cleanLine = l.replace(/^[-•\d\.\)]+\s*/, '')
        return `<li style="margin-bottom: 12px; display: flex; align-items: flex-start; gap: 10px;">
        <span style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; min-width: 24px; background-color: ${accentColor}; color: #ffffff; font-weight: bold; font-size: 10pt; border-radius: 50%; text-align: center; margin-top: 1px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">${idx + 1}</span>
        <span style="flex: 1; font-size: 11pt; color: #1e293b; line-height: 1.6;">${cleanLine}</span>
      </li>`
      })
      .join('\n')

    return `<ul style="list-style-type: none; padding-left: 0; margin-top: 8px; margin-bottom: 8px;">\n${items}\n</ul>`
  }

  const parseBullets = (text: string) => {
    if (!text.trim()) return '<p style="color: #64748b; font-style: italic;">Sin especificación.</p>'
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)

    const items = lines
      .map((l) => {
        const cleanLine = l.replace(/^[-•\d\.\)]+\s*/, '')
        return `<li style="margin-bottom: 10px; font-size: 11pt; color: #1e293b; line-height: 1.6; display: flex; align-items: flex-start; gap: 8px;">
        <strong style="color: #059669; font-size: 12pt;">✓</strong>
        <span>${cleanLine}</span>
      </li>`
      })
      .join('\n')

    return `<ul style="list-style-type: none; padding-left: 0; margin-top: 8px; margin-bottom: 8px;">\n${items}\n</ul>`
  }

  const parseRubricTable = (text: string) => {
    if (!text.trim()) return ''
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean)

    const tableRows = lines
      .map((l, idx) => {
        let crit = l
        let pts = '—'
        if (l.includes(':')) {
          const parts = l.split(':')
          crit = parts[0].replace(/^[-•\d\.\)]+\s*/, '').trim()
          pts = parts.slice(1).join(':').trim()
        }
        const rowBg = idx % 2 === 0 ? '#ffffff' : '#f8fafc'
        return `<tr style="border-bottom: 1px solid #e2e8f0; background-color: ${rowBg};">
        <td style="padding: 10px 14px; font-size: 10.5pt; color: #1e293b; font-weight: 500;">${crit}</td>
        <td style="padding: 10px 14px; font-size: 10.5pt; color: #0a2f68; font-weight: bold; text-align: right; white-space: nowrap;">${pts}</td>
      </tr>`
      })
      .join('\n')

    return `<table style="width: 100%; border-collapse: collapse; margin-top: 12px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
      <thead>
        <tr style="background-color: #0a2f68; color: #ffffff;">
          <th style="padding: 11px 14px; font-size: 10pt; font-weight: bold; text-align: left; text-transform: uppercase; letter-spacing: 0.5px;">Criterio de Evaluación</th>
          <th style="padding: 11px 14px; font-size: 10pt; font-weight: bold; text-align: right; text-transform: uppercase; letter-spacing: 0.5px;">Puntaje</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>`
  }

  const indicHtml = parseListItems(indicaciones, '#0a2f68')
  const entregHtml = parseBullets(entregables)
  const califTableHtml = parseRubricTable(calificacion)

  return `<p><img src="https://indoamerica.instructure.com/courses/30038/files/10414935/preview" alt="Etiquetas aula_Tarea 4.png" data-api-endpoint="https://indoamerica.instructure.com/api/v1/courses/30038/files/10414935" data-api-returntype="File" /></p>
<p><strong><span style="font-size: 18pt;">INDICACIONES&nbsp;</span></strong></p>

<!-- Tarjeta Elegante de Indicaciones -->
<div style="font-family: Arial, Helvetica, sans-serif; background-color: #ffffff; border-left: 6px solid #0a2f68; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; box-shadow: 0 4px 14px rgba(0,0,0,0.05); border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
  <div style="font-size: 12pt; font-weight: bold; color: #0a2f68; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
    <span style="font-size: 14pt;">📌</span> Guía Paso a Paso para el Estudiante
  </div>
  ${indicHtml}
</div>

<p><strong><span style="font-size: 18pt;">ENTREGABLES&nbsp;</span></strong></p>

<!-- Tarjeta Elegante de Entregables -->
<div style="font-family: Arial, Helvetica, sans-serif; background-color: #f0fdf4; border-left: 6px solid #059669; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; box-shadow: 0 4px 14px rgba(0,0,0,0.05); border-top: 1px solid #bbf7d0; border-right: 1px solid #bbf7d0; border-bottom: 1px solid #bbf7d0;">
  <div style="font-size: 12pt; font-weight: bold; color: #065f46; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #bbf7d0; padding-bottom: 8px;">
    <span style="font-size: 14pt;">📦</span> Requisitos y Formato de la Entrega
  </div>
  ${entregHtml}
</div>

<p><strong><span style="font-size: 18pt;">CALIFICACIÓN&nbsp;</span></strong></p>

<!-- Tarjeta Elegante de Rúbrica y Calificación -->
<div style="font-family: Arial, Helvetica, sans-serif; background-color: #fffbeb; border-left: 6px solid #d97706; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; box-shadow: 0 4px 14px rgba(0,0,0,0.05); border-top: 1px solid #fef08a; border-right: 1px solid #fef08a; border-bottom: 1px solid #fef08a;">
  <div style="font-size: 12pt; font-weight: bold; color: #78350f; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; border-bottom: 2px solid #fef08a; padding-bottom: 8px;">
    <span style="font-size: 14pt;">📊</span> Matriz y Criterios de Evaluación
  </div>
  ${califTableHtml}
</div>`
}

export default function CanvasTaskGenerator({ initialTitle = '', initialIndicaciones = '', onBack }: Props) {
  const [nombreTarea, setNombreTarea] = useState(initialTitle || 'Tarea 4: Taller Integrador de Números Enteros')
  const [indicaciones, setIndicaciones] = useState(
    initialIndicaciones ||
      '1. Revisa detenidamente el contenido de la guía didáctica en la sección de números enteros.\n2. Resuelve los 5 ejercicios del taller propuesto en tu cuaderno.\n3. Justifica detalladamente cada procedimiento matemático realizado.'
  )
  const [entregables, setEntregables] = useState(
    '• Archivo en formato PDF o fotografías legibles de alta resolución con las páginas de tu cuaderno.\n• El nombre del archivo debe seguir el estándar: Apellido_Nombre_Tarea4.pdf'
  )
  const [calificacion, setCalificacion] = useState(
    'Puntualidad y formato de presentación: 2 puntos\nProcedimiento matemático lógico y completo: 5 puntos\nRespuestas correctas y reflexión final: 3 puntos'
  )

  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview')

  const applyPreset = (tipo: 'taller' | 'proyecto' | 'informe') => {
    if (tipo === 'taller') {
      setNombreTarea('Tarea 4: Taller Práctico de Operaciones Combinadas')
      setIndicaciones(
        '1. Revisa el contenido de las páginas 18 a 41 de la guía didáctica.\n2. Resuelve los ejercicios del taller práctico en tu cuaderno de materia.\n3. Verifica los resultados usando la jerarquía de operaciones.'
      )
      setEntregables(
        '• Documento PDF con fotos legibles de las páginas resueltas de tu cuaderno.\n• Portada corta con tu Nombre, Grado y Fecha.'
      )
      setCalificacion(
        'Puntualidad y orden de entrega: 2 puntos\nDesarrollo paso a paso de procedimientos: 5 puntos\nResultados finales correctos: 3 puntos'
      )
    } else if (tipo === 'proyecto') {
      setNombreTarea('Tarea Integradora: Proyecto de Aplicación Financiera')
      setIndicaciones(
        '1. Investiga la aplicación de los números negativos en cuentas bancarias y estados de cuenta.\n2. Elabora un cuadro comparativo de ingresos, egresos y saldos en Excel o Word.\n3. Escribe una breve conclusión pedagógica de 100 palabras sobre la importancia de la educación financiera.'
      )
      setEntregables(
        '• Archivo PDF con el marco de investigación, el cuadro comparativo y la reflexión final.'
      )
      setCalificacion(
        'Investigación y conceptos clave: 3 puntos\nEstructura del cuadro comparativo: 4 puntos\nConclusiones y reflexión pedagógica: 3 puntos'
      )
    } else if (tipo === 'informe') {
      setNombreTarea('Tarea de Lectura: Resumen Crítico y Mapa Conceptual')
      setIndicaciones(
        '1. Lee atentamente la lectura asignada en el módulo de aprendizaje.\n2. Diseña un mapa conceptual interactivo o diagrama de ideas principales.\n3. Responde a las 3 preguntas de comprensión lectora adjuntas.'
      )
      setEntregables(
        '• Enlace al mapa conceptual (o imagen exportada en alta calidad).\n• Documento con las respuestas a las preguntas de reflexión.'
      )
      setCalificacion(
        'Mapa conceptual claro y estructurado: 4 puntos\nRespuestas argumentadas a las preguntas: 4 puntos\nOrtografía y redacción impecable: 2 puntos'
      )
    }
  }

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault()
    const htmlCode = generateCanvasTaskHtml(nombreTarea, indicaciones, entregables, calificacion)
    setGeneratedHtml(htmlCode)
    setCopied(false)
  }

  const handleCopy = () => {
    if (!generatedHtml) return
    navigator.clipboard.writeText(generatedHtml)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  const handleDownload = () => {
    if (!generatedHtml) return
    const blob = new Blob([generatedHtml], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${nombreTarea.toLowerCase().replace(/[^\w]+/g, '_')}.html`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex items-center justify-between flex-wrap gap-4">
        <div>
          <span className="px-3 py-1 bg-blue-100 text-blue-900 rounded-full text-xs font-bold uppercase tracking-wider">
            Canvas LMS · Formato Didáctico Elegante
          </span>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-2">Generador de Tareas para Canvas</h2>
          <p className="text-sm text-slate-600 mt-1">
            Diseña tareas pedagógicas estructuradas con tarjetas elegantes, listas numeradas y matriz de evaluación para Canvas LMS.
          </p>
        </div>
        {onBack && (
          <button type="button" onClick={onBack} className="text-xs text-slate-500 hover:text-slate-800 font-semibold cursor-pointer">
            ← Volver
          </button>
        )}
      </div>

      {/* Preset Quick Fill Bar */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex items-center gap-3 flex-wrap">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">⚡ Plantillas Rápidas:</span>
        <button
          type="button"
          onClick={() => applyPreset('taller')}
          className="px-3 py-1.5 bg-white border border-slate-300 hover:border-blue-500 rounded-xl text-xs font-semibold text-slate-800 transition-all cursor-pointer shadow-2xs"
        >
          📐 Taller Práctico
        </button>
        <button
          type="button"
          onClick={() => applyPreset('proyecto')}
          className="px-3 py-1.5 bg-white border border-slate-300 hover:border-emerald-500 rounded-xl text-xs font-semibold text-slate-800 transition-all cursor-pointer shadow-2xs"
        >
          🚀 Proyecto Integrador
        </button>
        <button
          type="button"
          onClick={() => applyPreset('informe')}
          className="px-3 py-1.5 bg-white border border-slate-300 hover:border-amber-500 rounded-xl text-xs font-semibold text-slate-800 transition-all cursor-pointer shadow-2xs"
        >
          📖 Informe de Lectura
        </button>
      </div>

      {/* Form Card */}
      <form onSubmit={handleGenerate} className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-5">
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            1. Nombre de la Tarea
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-sm font-medium text-slate-900"
            placeholder="Ej. Tarea 4: Operaciones Combinadas con Números Enteros"
            value={nombreTarea}
            onChange={(e) => setNombreTarea(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            2. Indicaciones de la Tarea (Paso a Paso)
          </label>
          <textarea
            required
            rows={4}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-sm font-normal text-slate-900"
            placeholder="Escribe cada instrucción en una línea separada..."
            value={indicaciones}
            onChange={(e) => setIndicaciones(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            3. Entregables y Requisitos de Entrega
          </label>
          <textarea
            required
            rows={3}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-sm font-normal text-slate-900"
            placeholder="Ej. Archivo PDF o imágenes del cuaderno..."
            value={entregables}
            onChange={(e) => setEntregables(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            4. Calificación y Criterios (Ej. Criterio: Puntaje)
          </label>
          <textarea
            required
            rows={3}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-sm font-normal text-slate-900"
            placeholder="Ej. Puntualidad: 2 pts&#10;Procedimiento paso a paso: 5 pts&#10;Resultados correctos: 3 pts"
            value={calificacion}
            onChange={(e) => setCalificacion(e.target.value)}
          />
        </div>

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 bg-blue-700 hover:bg-blue-800 text-white font-bold text-sm rounded-xl shadow-md transition-all cursor-pointer flex items-center gap-2"
          >
            <span>⚡ Generar HTML Elegante para Canvas</span>
          </button>
        </div>
      </form>

      {/* Generated Result Output */}
      {generatedHtml && (
        <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h3 className="text-lg font-bold text-slate-900">Resultado Didáctico Enriquecido para Canvas LMS</h3>

            <div className="flex items-center gap-2">
              <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1 border border-slate-200">
                <button
                  type="button"
                  onClick={() => setActiveTab('preview')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    activeTab === 'preview' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  👁 Vista Previa
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('code')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    activeTab === 'code' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  💻 Código HTML
                </button>
              </div>

              <button
                type="button"
                onClick={handleCopy}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>{copied ? '✅ ¡Copiado!' : '📋 Copiar Código HTML'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownload}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer flex items-center gap-1.5"
              >
                <span>⬇ Descargar .html</span>
              </button>
            </div>
          </div>

          {activeTab === 'preview' ? (
            <div className="border border-slate-300 rounded-2xl p-6 bg-white min-h-[300px]">
              <div dangerouslySetInnerHTML={{ __html: generatedHtml }} />
            </div>
          ) : (
            <textarea
              readOnly
              rows={16}
              className="w-full font-mono text-xs p-4 bg-slate-900 text-emerald-400 rounded-2xl border border-slate-800 focus:outline-none"
              value={generatedHtml}
            />
          )}
        </div>
      )}
    </div>
  )
}
