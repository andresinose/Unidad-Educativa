export interface MethodologyPhases {
  activacion: string
  anticipacion: string
  construccion: string
  consolidacion: string
}

export interface CurricularAdaptation {
  student_ref: string
  need_description: string
  grade_level: string
  achievement_level: string
}

export interface SilaboWeek {
  week_number: number
  topic: string
  subtemas?: string[]
  competency_codes: string[]
  methodology_phases: MethodologyPhases
  resources: string[]
  achievement_level: string
  evaluation_technique: string
  adaptations: CurricularAdaptation[]
  adaptaciones_count?: number
}

export interface SilaboExtraction {
  subject: string
  teacher: string
  grade: string
  parallels: string
  unit_name: string
  trimester: string
  parcial: string
  unit_objective: string
  start_date: string
  end_date: string
  weeks: SilaboWeek[]
  warnings: string[]
}

export interface GuiaExtraction {
  subject: string
  grade: string
  fechas?: string
  semanas_mencionadas?: number[]
  weeks_detected: number[]
  competency_codes_by_week: Record<string, string[]>
  total_pages: number
  warnings: string[]
}

export type ConcordanceStatus = 'CUMPLE' | 'CUMPLE_PARCIAL' | 'NO_CUMPLE' | 'CONCORDANTE' | 'PARCIAL' | 'FALTANTE_EN_GUIA' | 'FALTANTE_EN_SILABO'

export type EstadoSubtema = 'CUBIERTO' | 'MENCIONADO' | 'AUSENTE'

export interface SubtemaEvidencia {
  texto: string
  estado: EstadoSubtema
  evidencia: string
  fuentes: string[]
}

export interface MatrizSubtemas {
  cobertura: number
  cubiertos: number
  total: number
  subtemas: SubtemaEvidencia[]
  enriquecimiento: string[]
}

export interface CoherenciaDetalle {
  ok: boolean
  detalle: string
  confianza: 'normal' | 'alta'
}

export interface CoherenciaTransversal {
  fechas: CoherenciaDetalle
  periodos: CoherenciaDetalle
  codigos_competencia: CoherenciaDetalle
}

export interface DetalleSemanal {
  semana: number
  tema_silabo: string
  tema_material: string | null
  desarrollada_en_material: boolean
  veredicto_semana: ConcordanceStatus
  habilita_generacion: boolean
  matriz_subtemas: MatrizSubtemas
  notas_informativas: string[]
  coherencia: CoherenciaTransversal
  observaciones: string[]
  recomendaciones: string[]

  // Legacy fields
  week_number?: number
  topic?: string
  silabo_codes?: string[]
  guia_codes?: string[]
  missing_codes_in_guia?: string[]
  page_range_guia?: string | null
  adaptation_in_silabo?: boolean
  adaptation_in_guia?: boolean
  status?: ConcordanceStatus
  observation?: string
}

export interface ResumenSemanasDura {
  silabo: number
  material_desarrolladas: number
  material_solo_mencionadas: number[]
  veredicto: ConcordanceStatus
  observaciones: string[]
  recomendaciones: string[]
}

export interface ConcordanceResult {
  veredicto_global: ConcordanceStatus
  resumen: string
  semanas: ResumenSemanasDura
  detalle_semanal: DetalleSemanal[]
  temas_validados: Array<{
    semana: number
    tema: string
    subtemas: string[]
    competencias: string[]
  }>

  // Legacy fields
  weeks?: DetalleSemanal[]
  key_findings?: string[]
  concordant_count?: number
  partial_count?: number
  missing_count?: number
}

export interface AnalyzeResponse {
  session_id: string
  silabo: SilaboExtraction
  guia: GuiaExtraction
  concordance: ConcordanceResult
}

export const INTENTS = [
  'presentar', 'comprender', 'visualizar', 'practicar', 'aplicar',
  'resolver', 'analizar', 'comparar', 'experimentar', 'reforzar',
  'comprobar', 'evaluar',
] as const

export type PedagogicalIntent = (typeof INTENTS)[number]

export interface ResourceBlock {
  type: 'diagram' | 'interactive_activity' | 'geogebra' | 'text'
  title: string
  payload: Record<string, unknown>
  rendered_html: string
}

export interface GeneratedResource {
  title: string
  week_number: number
  topic: string
  intent: PedagogicalIntent
  summary: string
  blocks: ResourceBlock[]
  mcp_tool_trace: string[]
}

export interface Material {
  id: string
  title: string
  subject: string
  grade: string
  unit: string
  teacher: string
  term: string
  pages: number
  filename: string
  source: 'curado' | 'convertido'
}

export interface ConversionJob {
  id: string
  estado: 'procesando' | 'completado' | 'error'
  pagina_actual: number
  total_paginas: number
  material_id: string | null
  error: string | null
}

