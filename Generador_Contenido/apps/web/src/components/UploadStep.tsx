import { useRef, useState } from 'react'

interface Props {
  onSubmit: (silabo: File, guia: File) => void
  loading: boolean
  error: string | null
}

function FilePicker({
  label,
  hint,
  file,
  onChange,
}: {
  label: string
  hint: string
  file: File | null
  onChange: (f: File) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  return (
    <div
      className={`flex-1 rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
        dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const f = e.dataTransfer.files[0]
        if (f) onChange(f)
      }}
    >
      <h3 className="font-semibold text-lg">{label}</h3>
      <p className="text-sm text-gray-500 mb-3">{hint}</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onChange(f)
        }}
      />
      <button
        type="button"
        className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700"
        onClick={() => inputRef.current?.click()}
      >
        Seleccionar archivo
      </button>
      <p className="mt-3 text-sm text-gray-700 truncate">
        {file ? `✓ ${file.name}` : 'Arrastre el archivo aquí o haga clic'}
      </p>
    </div>
  )
}

export default function UploadStep({ onSubmit, loading, error }: Props) {
  const [silabo, setSilabo] = useState<File | null>(null)
  const [guia, setGuia] = useState<File | null>(null)

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Cargue sus documentos</h1>
      <p className="text-gray-600 mb-6">
        Suba el sílabo o planificación microcurricular y la guía didáctica. La aplicación los
        analizará y validará su correspondencia.
      </p>
      <div className="flex flex-col sm:flex-row gap-4">
        <FilePicker label="Sílabo / Planificación" hint="DOCX o PDF — máx. 50 MB" file={silabo} onChange={setSilabo} />
        <FilePicker label="Guía didáctica" hint="PDF o DOCX — máx. 50 MB" file={guia} onChange={setGuia} />
      </div>
      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}
      <button
        type="button"
        disabled={!silabo || !guia || loading}
        className="mt-6 w-full rounded-lg bg-blue-600 text-white py-3 font-semibold disabled:bg-gray-300 hover:bg-blue-700"
        onClick={() => silabo && guia && onSubmit(silabo, guia)}
      >
        {loading ? 'Analizando…' : 'Analizar documentos'}
      </button>
    </div>
  )
}
