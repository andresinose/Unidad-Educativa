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
  competency_codes: string[]
  methodology_phases: MethodologyPhases
  resources: string[]
  achievement_level: string
  evaluation_technique: string
  adaptations: CurricularAdaptation[]
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
  weeks_detected: number[]
  competency_codes_by_week: Record<string, string[]>
  total_pages: number
  warnings: string[]
}

export type ConcordanceStatus = 'CONCORDANTE' | 'PARCIAL' | 'FALTANTE_EN_GUIA' | 'FALTANTE_EN_SILABO'

export interface WeekConcordance {
  week_number: number
  topic: string
  silabo_codes: string[]
  guia_codes: string[]
  missing_codes_in_guia: string[]
  page_range_guia: string | null
  adaptation_in_silabo: boolean
  adaptation_in_guia: boolean
  status: ConcordanceStatus
  observation: string
}

export interface ConcordanceResult {
  weeks: WeekConcordance[]
  key_findings: string[]
  concordant_count: number
  partial_count: number
  missing_count: number
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
