import React from 'react'

interface MenuInicialProps {
  onSelect: (modulo: 'validador' | 'generador') => void
}

export default function MenuInicial({ onSelect }: MenuInicialProps) {
  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-hidden bg-[#0a2f68] text-white">
      {/* Institutional Geometric Background Accents */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-[#5ecfb1]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#e9a13b]/10 rounded-full blur-3xl pointer-events-none" />

      {/* Decorative Geometric Shapes */}
      <div className="absolute top-12 left-12 w-16 h-16 border-4 border-[#5ecfb1]/30 transform rotate-45 pointer-events-none hidden sm:block" />
      <div className="absolute bottom-16 right-16 w-24 h-24 border-4 border-[#e9a13b]/30 rounded-full pointer-events-none hidden sm:block" />

      {/* Main Container */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 py-12 flex-1 flex flex-col justify-center">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-1.5 rounded-full bg-[#5ecfb1]/20 border border-[#5ecfb1]/40 text-[#5ecfb1] text-xs font-bold uppercase tracking-widest mb-4">
            Plataforma Pedagógica Indoamérica
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight mb-4">
            Unidad Educativa Bilingüe Indoamérica
          </h1>
          <p className="text-slate-300 text-base sm:text-lg max-w-2xl mx-auto font-medium">
            Selecciona el módulo con el que deseas trabajar hoy para enriquecer el proceso de enseñanza y aprendizaje.
          </p>
        </div>

        {/* 2 Main Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto w-full">
          {/* Card 1: Validador de Contenidos */}
          <div
            onClick={() => onSelect('validador')}
            className="group relative bg-white text-slate-900 rounded-3xl p-8 shadow-2xl border-2 border-transparent hover:border-[#5ecfb1] transition-all duration-300 transform hover:-translate-y-1.5 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-[#0a2f68] text-[#5ecfb1] flex items-center justify-center text-2xl font-bold mb-6 group-hover:scale-110 transition-transform">
                📋
              </div>
              <h2 className="text-2xl font-bold text-[#0a2f68] mb-3 group-hover:text-[#5ecfb1] transition-colors">
                Validador de Contenidos
              </h2>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">
                Valida la concordancia entre el sílabo y la guía didáctica, identificando brechas de contenidos y generando actividades interactivas personalizadas.
              </p>
            </div>
            <div className="flex items-center text-sm font-extrabold text-[#0a2f68] group-hover:text-[#5ecfb1] transition-colors">
              <span>Ingresar al Validador</span>
              <span className="ml-2 transform group-hover:translate-x-1 transition-transform">→</span>
            </div>
          </div>

          {/* Card 2: Generador de Contenidos */}
          <div
            onClick={() => onSelect('generador')}
            className="group relative bg-white text-slate-900 rounded-3xl p-8 shadow-2xl border-2 border-transparent hover:border-[#e9a13b] transition-all duration-300 transform hover:-translate-y-1.5 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-[#0a2f68] text-[#e9a13b] flex items-center justify-center text-2xl font-bold mb-6 group-hover:scale-110 transition-transform">
                ⚡
              </div>
              <h2 className="text-2xl font-bold text-[#0a2f68] mb-3 group-hover:text-[#e9a13b] transition-colors">
                Generador de Contenidos
              </h2>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">
                Transforma libros o folletos en PDF a páginas HTML interactivas con autoguardado, ejercicios comprobables, zona de dibujo y visor autónomo.
              </p>
            </div>
            <div className="flex items-center text-sm font-extrabold text-[#0a2f68] group-hover:text-[#e9a13b] transition-colors">
              <span>Ingresar al Generador</span>
              <span className="ml-2 transform group-hover:translate-x-1 transition-transform">→</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 text-center py-6 text-xs text-slate-400 font-semibold border-t border-white/10">
        © {new Date().getFullYear()} Unidad Educativa Bilingüe Indoamérica — Todos los derechos reservados
      </footer>
    </div>
  )
}
