import type { AnalyzeResponse, GeneratedResource, PedagogicalIntent } from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // ignore — keep statusText
    }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export async function analyzeDocuments(silabo: File, guia: File): Promise<AnalyzeResponse> {
  const form = new FormData()
  form.append('silabo', silabo)
  form.append('guia', guia)
  const res = await fetch(`${BASE}/analyze`, { method: 'POST', body: form })
  return unwrap(res)
}

export async function generateResource(
  sessionId: string,
  weekNumber: number,
  intent: PedagogicalIntent,
  extraInstructions: string,
): Promise<GeneratedResource> {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      week_number: weekNumber,
      intent,
      extra_instructions: extraInstructions,
    }),
  })
  return unwrap(res)
}

async function downloadBlob(path: string, resource: GeneratedResource, fallbackName: string) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resource),
  })
  if (!res.ok) {
    throw new ApiError(res.statusText, res.status)
  }
  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = /filename="([^"]+)"/.exec(disposition)
  const filename = match ? match[1] : fallbackName
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export const exportHtml = (resource: GeneratedResource) => downloadBlob('/export/html', resource, 'recurso.html')
export const exportPptx = (resource: GeneratedResource) => downloadBlob('/export/pptx', resource, 'recurso.pptx')

export async function listMaterials(): Promise<import('./types').Material[]> {
  const res = await fetch(`${BASE}/materials`)
  return unwrap(res)
}

export const materialPreviewUrl = (id: string) => `${BASE}/materials/${id}/preview`

export async function uploadMaterialPdf(archivo: File): Promise<import('./types').ConversionJob> {
  const form = new FormData()
  form.append('archivo', archivo)
  const res = await fetch(`${BASE}/materials/upload`, { method: 'POST', body: form })
  return unwrap(res)
}

export async function getConversionJob(jobId: string): Promise<import('./types').ConversionJob> {
  const res = await fetch(`${BASE}/materials/jobs/${jobId}`)
  return unwrap(res)
}

export async function downloadMaterial(material: import('./types').Material) {
  const res = await fetch(`${BASE}/materials/${material.id}/download`)
  if (!res.ok) throw new ApiError(res.statusText, res.status)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = material.filename || `material_${material.id}.html`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function downloadMaterialZip(material: import('./types').Material) {
  const res = await fetch(`${BASE}/materials/${material.id}/download-zip`)
  if (!res.ok) throw new ApiError(res.statusText, res.status)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `material_${material.id}.zip`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

