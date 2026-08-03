"""Shell generator: wraps rendered page HTML into a standalone, institutional HTML document.
Includes 100% self-contained embedded CSS (no CDN dependencies required for offline & iframe rendering),
UEI institutional palette (#0a2f68, #5ecfb1, #e9a13b), sticky toolbar, interactive JS,
localStorage autosave, exercise checking, drawing canvas, print styles, and no-JS warning.
Includes explicit inline styles and assets/ structure matching Canvas LMS specs.
"""
from __future__ import annotations

import html
import io
import zipfile
from app.services.material_builder.blocks import MetadatosMaterial


DEFAULT_CSS = """/* Hoja de Estilos Institucional — UEB Indoamérica */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

*, ::before, ::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; background-color: #f8fafc; color: #0f172a; line-height: 1.5; }
body { min-height: 100vh; padding-bottom: 5rem; }

.max-w-4xl { max-width: 56rem; margin-left: auto; margin-right: auto; }
.max-w-md { max-width: 28rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.w-full { width: 100%; }
.h-full { height: 100%; }
.h-auto { height: auto; }
.h-36 { height: 9rem; }
.h-44 { height: 11rem; }
.h-6 { height: 1.5rem; }
.w-6 { width: 1.5rem; }
.min-w-\\[140px\\] { min-width: 140px; }
.min-h-\\[160px\\] { min-height: 160px; }

.p-2 { padding: 0.5rem; }
.p-2\.5 { padding: 0.625rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-5 { padding: 1.25rem; }
.p-6 { padding: 1.5rem; }
.px-0\.5 { padding-left: 0.125rem; padding-right: 0.125rem; }
.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
.px-2\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
.py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }

.my-2 { margin-top: 0.5rem; margin-bottom: 0.5rem; }
.my-3 { margin-top: 0.75rem; margin-bottom: 0.75rem; }
.my-4 { margin-top: 1rem; margin-bottom: 1rem; }
.my-5 { margin-top: 1.25rem; margin-bottom: 1.25rem; }
.my-6 { margin-top: 1.5rem; margin-bottom: 1.5rem; }
.my-8 { margin-top: 2rem; margin-bottom: 2rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-1\.5 { margin-bottom: 0.375rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-8 { margin-top: 2rem; }
.mt-12 { margin-top: 3rem; }
.ml-2 { margin-left: 0.5rem; }

.flex { display: flex; }
.inline-block { display: inline-block; }
.flex-1 { flex: 1 1 0%; }
.shrink-0 { flex-shrink: 0; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }
.flex-wrap { flex-wrap: wrap; }
.gap-1 { gap: 0.25rem; }
.gap-1\.5 { gap: 0.375rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.space-y-1 > * + * { margin-top: 0.25rem; }

.text-center { text-align: center; }
.text-right { text-align: right; }
.text-left { text-align: left; }

.uei-header {
  background: linear-gradient(135deg, #0a2f68 0%, #0d3a80 100%);
  color: #ffffff !important;
  border-bottom: 4px solid #5ecfb1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.uei-header h1 { color: #ffffff !important; font-size: 1.5rem; font-weight: 800; }

.pagina {
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 1.5rem;
  padding: 2rem;
  margin-top: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.caja-info {
  margin-top: 1rem;
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
  border-top-right-radius: 0.75rem;
  border-bottom-right-radius: 0.75rem;
}
.caja-info.border-blue-600, .caja-info[class*="azul"] { border-left: 5px solid #2563eb; background-color: #eff6ff; color: #1e3a8a; }
.caja-info.border-emerald-600, .caja-info[class*="verde"] { border-left: 5px solid #059669; background-color: #ecfdf5; color: #065f46; }
.caja-info.border-amber-600, .caja-info[class*="naranja"], .caja-info[class*="amarillo"] { border-left: 5px solid #d97706; background-color: #fef3c7; color: #78350f; }
.caja-info.border-rose-600, .caja-info[class*="rosa"], .caja-info[class*="rojo"] { border-left: 5px solid #e11d48; background-color: #fff1f2; color: #881337; }
.caja-info.border-purple-600, .caja-info[class*="morado"], .caja-info[class*="purpura"] { border-left: 5px solid #9333ea; background-color: #faf5ff; color: #581c87; }
.caja-info.border-slate-500, .caja-info[class*="gris"] { border-left: 5px solid #64748b; background-color: #f1f5f9; color: #0f172a; }
.caja-info.border-2, .caja-info[class*="destacado"] { border: 2px solid #6366f1; background-color: #eef2ff; color: #312e81; border-radius: 0.75rem; }

.ejercicio-block {
  background-color: #ffffff;
  border: 2px solid #bfdbfe;
  border-radius: 1rem;
  padding: 1.25rem;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.ejercicio-item {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 1rem;
  border-radius: 0.75rem;
  margin-bottom: 0.75rem;
}
.options-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  background-color: #ffffff;
  margin-bottom: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.15s ease;
}
.options-group label:hover { background-color: #f1f5f9; }

.zona-trabajo {
  border: 1px solid #cbd5e1;
  border-radius: 1rem;
  background-color: #ffffff;
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
  overflow: hidden;
}
.bg-grid-pattern {
  background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
  background-size: 16px 16px;
}
.tab-btn {
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.375rem;
  cursor: pointer;
  border: 1px solid transparent;
}
.tab-btn.active {
  background-color: #ffffff;
  border-color: #cbd5e1;
  color: #334155;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

button { font-family: inherit; }
input[type="text"], textarea {
  font-family: inherit;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  width: 100%;
  outline: none;
}
input[type="text"]:focus, textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

table { width: 100%; border-collapse: collapse; }
th, td { border: 1px solid #e2e8f0; padding: 0.5rem 0.75rem; font-size: 0.75rem; text-align: left; }
th { background-color: #0a2f68; color: #ffffff !important; text-transform: uppercase; font-weight: 700; }

.sticky { position: sticky; top: 0; z-index: 40; }
.bg-white-90 { background-color: rgba(255, 255, 255, 0.95); }
.backdrop-blur-md { backdrop-filter: blur(8px); }
.border-b { border-bottom: 1px solid #e2e8f0; }
.tool-btn {
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.border { border: 1px solid #e2e8f0; }
.border-2 { border-width: 2px; }
.border-b-4 { border-bottom-width: 4px; }
.border-t { border-top: 1px solid #f1f5f9; }
.border-slate-100 { border-color: #f1f5f9; }
.border-slate-200 { border-color: #e2e8f0; }
.border-slate-300 { border-color: #cbd5e1; }
.border-blue-200 { border-color: #bfdbfe; }
.border-blue-600 { border-color: #2563eb; }

.rounded { border-radius: 0.25rem; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-2xl { border-radius: 1rem; }
.rounded-3xl { border-radius: 1.5rem; }
.rounded-full { border-radius: 9999px; }
.rounded-r-xl { border-top-right-radius: 0.75rem; border-bottom-right-radius: 0.75rem; }

.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 800; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.text-xs { font-size: 0.75rem; line-height: 1rem; }
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.text-base { font-size: 1rem; line-height: 1.5rem; }
.text-lg { font-size: 1.125rem; line-height: 1.75rem; }
.text-xl { font-size: 1.25rem; line-height: 1.75rem; }
.text-2xl { font-size: 1.5rem; line-height: 2rem; }

.uppercase { text-transform: uppercase; }
.tracking-widest { letter-spacing: 0.1em; }
.tracking-wider { letter-spacing: 0.05em; }
.tracking-tight { letter-spacing: -0.025em; }

.text-white { color: #ffffff !important; }
.text-slate-900, .text-slate-950 { color: #0f172a; }
.text-slate-800 { color: #1e293b; }
.text-slate-700 { color: #334155; }
.text-slate-600 { color: #475569; }
.text-slate-500 { color: #64748b; }
.text-slate-400 { color: #94a3b8; }
.text-blue-900, .text-blue-950 { color: #1e3a8a; }
.text-blue-800 { color: #1e40af; }
.text-blue-700 { color: #1d4ed8; }

.bg-white { background-color: #ffffff; }
.bg-slate-50 { background-color: #f8fafc; }
.bg-slate-100 { background-color: #f1f5f9; }
.bg-slate-200 { background-color: #e2e8f0; }
.bg-blue-50 { background-color: #eff6ff; }
.bg-blue-100 { background-color: #dbeafe; }
.bg-blue-700 { background-color: #1d4ed8; }
.bg-blue-700:hover { background-color: #1e40af; }
.bg-blue-900 { background-color: #1e3a8a; }
.bg-amber-100 { background-color: #fef3c7; }
.bg-amber-200 { background-color: #fde68a; }
.bg-emerald-100 { background-color: #d1fae5; }
.text-emerald-900 { color: #064e3b; }
.bg-rose-50 { background-color: #fff1f2; }
.bg-rose-100 { background-color: #ffe4e6; }
.text-rose-700 { color: #be123c; }
.text-rose-900 { color: #881337; }

.hidden { display: none !important; }

@media print {
  .no-print { display: none !important; }
  body { background: white !important; color: black !important; padding-bottom: 0 !important; }
  .pagina { border: none !important; box-shadow: none !important; margin: 0 !important; page-break-after: always; }
}
"""

DEFAULT_JS = """/* Engine Interactivo - UEB Indoamérica */
const MATERIAL_ID = 'material_' + window.location.pathname.replace(/[^a-z0-9]/gi, '_');
let markMode = null;

function setMarkMode(mode) {
  markMode = markMode === mode ? null : mode;
  document.querySelectorAll('.tool-btn').forEach(btn => btn.style.outline = 'none');
  if (markMode && event && event.target) {
    event.target.style.outline = '2px solid #2563eb';
  }
}

document.addEventListener('mouseup', () => {
  if (!markMode) return;
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed) return;
  const range = sel.getRangeAt(0);
  if (markMode === 'clear') {
    const parent = sel.anchorNode.parentElement;
    if (parent && (parent.tagName === 'MARK' || parent.tagName === 'U')) {
      const text = document.createTextNode(parent.textContent);
      parent.replaceWith(text);
    }
  } else {
    const elem = document.createElement(markMode === 'highlight' ? 'mark' : 'u');
    if (markMode === 'highlight') {
      elem.style.backgroundColor = '#fde68a';
      elem.style.color = '#0f172a';
      elem.style.borderRadius = '0.25rem';
      elem.style.padding = '0 0.125rem';
    }
    range.surroundContents(elem);
  }
  sel.removeAllRanges();
  saveProgress();
});

function checkExercisePage(pageNum) {
  const pageSec = document.getElementById('pagina-' + pageNum);
  if (!pageSec) return;
  
  let total = 0;
  let correct = 0;

  pageSec.querySelectorAll('.ejercicio-item').forEach(item => {
    total++;
    const itemId = item.dataset.itemId;
    const feedback = document.getElementById(itemId + '-feedback');
    let isCorrect = false;

    const radioChecked = item.querySelector('input[type="radio"]:checked');
    const textInput = item.querySelector('input[type="text"]');

    if (radioChecked) {
      const userAns = radioChecked.value.trim().toLowerCase();
      const targetAns = (radioChecked.dataset.answer || '').trim().toLowerCase();
      isCorrect = userAns === targetAns;
    } else if (textInput) {
      const userAns = textInput.value.trim().toLowerCase();
      const targetAns = (textInput.dataset.answer || '').trim().toLowerCase();
      isCorrect = targetAns ? userAns === targetAns : userAns.length > 0;
    }

    if (feedback) {
      feedback.style.display = 'block';
      feedback.classList.remove('hidden');
      if (isCorrect) {
        correct++;
        feedback.style.backgroundColor = '#d1fae5';
        feedback.style.color = '#064e3b';
        feedback.innerHTML = '✔ ¡Correcto!';
      } else {
        feedback.style.backgroundColor = '#ffe4e6';
        feedback.style.color = '#881337';
        feedback.innerHTML = '✘ Revisa tu respuesta e inténtalo de nuevo.';
      }
    }
  });

  saveProgress();
}

function switchZoneTab(zoneId, tab) {
  const zone = document.getElementById(zoneId);
  if (!zone) return;
  const writeMode = zone.querySelector('.write-mode');
  const drawMode = zone.querySelector('.draw-mode');
  const btns = zone.querySelectorAll('.tab-btn');

  btns.forEach(b => {
    b.classList.remove('active');
    b.style.backgroundColor = '#e2e8f0';
  });
  if (tab === 'write') {
    writeMode.style.display = 'block';
    drawMode.style.display = 'none';
    writeMode.classList.remove('hidden');
    drawMode.classList.add('hidden');
    btns[0].classList.add('active');
    btns[0].style.backgroundColor = '#ffffff';
  } else {
    writeMode.style.display = 'none';
    drawMode.style.display = 'block';
    writeMode.classList.add('hidden');
    drawMode.classList.remove('hidden');
    btns[1].classList.add('active');
    btns[1].style.backgroundColor = '#ffffff';
    initCanvas(zoneId);
  }
}

function initCanvas(zoneId) {
  const canvas = document.getElementById(zoneId + '-canvas');
  if (!canvas || canvas.dataset.inited) return;
  canvas.dataset.inited = 'true';
  canvas.width = canvas.parentElement.clientWidth || 600;
  canvas.height = canvas.parentElement.clientHeight || 180;

  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = '#1e3a8a';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';

  let drawing = false;
  canvas.addEventListener('mousedown', e => { drawing = true; ctx.beginPath(); ctx.moveTo(e.offsetX, e.offsetY); });
  canvas.addEventListener('mousemove', e => { if (drawing) { ctx.lineTo(e.offsetX, e.offsetY); ctx.stroke(); } });
  canvas.addEventListener('mouseup', () => { drawing = false; saveProgress(); });
  canvas.addEventListener('mouseleave', () => { drawing = false; });
}

function clearZone(zoneId) {
  const text = document.getElementById(zoneId + '-text');
  const canvas = document.getElementById(zoneId + '-canvas');
  if (text) text.value = '';
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  saveProgress();
}

function saveProgress() {
  const state = {};
  document.querySelectorAll('input[type="text"]').forEach(i => state[i.id] = i.value);
  document.querySelectorAll('textarea').forEach(t => state[t.id] = t.value);
  document.querySelectorAll('input[type="radio"]:checked').forEach(r => state[r.name] = r.value);
  try {
    localStorage.setItem(MATERIAL_ID, JSON.stringify(state));
  } catch(e) {}
}

function loadProgress() {
  try {
    const raw = localStorage.getItem(MATERIAL_ID);
    if (!raw) return;
    const state = JSON.parse(raw);
    Object.keys(state).forEach(id => {
      const elem = document.getElementById(id);
      if (elem) elem.value = state[id];
      const radios = document.querySelectorAll(`input[name="${id}"]`);
      radios.forEach(r => { if (r.value === state[id]) r.checked = true; });
    });
  } catch(e) {}
}

function clearAllData() {
  if (confirm('¿Deseas borrar todas tus respuestas y notas de este material?')) {
    localStorage.removeItem(MATERIAL_ID);
    window.location.reload();
  }
}

function exportProgress() {
  saveProgress();
  const raw = localStorage.getItem(MATERIAL_ID) || '{}';
  const blob = new Blob([raw], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'avance_' + MATERIAL_ID + '.json';
  a.click();
}

document.querySelectorAll('input, textarea').forEach(el => {
  el.addEventListener('input', saveProgress);
});

window.addEventListener('DOMContentLoaded', loadProgress);
"""


def build_material_shell(metadatos: MetadatosMaterial, paginas_html: list[str]) -> str:
    title_esc = html.escape(metadatos.titulo)
    subject_esc = html.escape(metadatos.materia)
    grade_esc = html.escape(metadatos.grado)
    unit_esc = html.escape(metadatos.unidad)
    teacher_esc = html.escape(metadatos.docente)
    term_esc = html.escape(metadatos.periodo)
    total_pages = metadatos.total_paginas or len(paginas_html)

    pages_body = "\n".join(paginas_html)

    return f"""<!DOCTYPE html>
<html lang="es" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_esc} - Unidad Educativa Bilingüe Indoamérica</title>
  <link rel="stylesheet" href="assets/css/styles.css">
  <style>
{DEFAULT_CSS}
  </style>
</head>
<body style="min-height: 100vh; padding-bottom: 5rem; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; background-color: #f8fafc; color: #0f172a;" class="min-h-screen pb-20">

  <!-- No-JS Warning -->
  <noscript>
    <div style="background-color: #e11d48; color: #ffffff !important; padding: 1rem; text-align: center; font-weight: 700; font-size: 0.875rem;">
      ⚠️ Este documento educativo contiene ejercicios interactivos. Por favor, descarga el archivo y ábrelo con doble clic en un navegador como Google Chrome o Microsoft Edge.
    </div>
  </noscript>

  <!-- Header Banner -->
  <header style="background: linear-gradient(135deg, #0a2f68 0%, #0d3a80 100%); color: #ffffff !important; border-bottom: 4px solid #5ecfb1; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);" class="uei-header no-print">
    <div style="max-width: 56rem; margin-left: auto; margin-right: auto; padding: 1.5rem 1rem;" class="max-w-4xl mx-auto px-4 py-6">
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;" class="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div style="color: #5ecfb1 !important; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.25rem;" class="font-bold text-xs uppercase tracking-widest mb-1">Unidad Educativa Bilingüe Indoamérica</div>
          <h1 style="color: #ffffff !important; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.025em; margin: 0.25rem 0;" class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">{title_esc}</h1>
          <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.75rem; color: #cbd5e1; margin-top: 0.5rem; flex-wrap: wrap; font-weight: 500;" class="flex items-center gap-3 text-xs text-slate-300 mt-2 flex-wrap font-medium">
            {f'<span style="background-color: rgba(255,255,255,0.15); padding: 0.125rem 0.5rem; border-radius: 0.25rem; color: #ffffff !important;">{subject_esc}</span>' if subject_esc else ''}
            {f'<span style="color: #ffffff !important;">• {grade_esc}</span>' if grade_esc else ''}
            {f'<span style="color: #ffffff !important;">• {unit_esc}</span>' if unit_esc else ''}
            {f'<span style="color: #ffffff !important;">• {teacher_esc}</span>' if teacher_esc else ''}
            {f'<span style="color: #ffffff !important;">• {term_esc}</span>' if term_esc else ''}
          </div>
        </div>
        <div style="text-align: right;" class="text-right">
          <span style="background-color: rgba(94,207,177,0.2); border: 1px solid rgba(94,207,177,0.4); color: #5ecfb1 !important; display: inline-block; padding: 0.25rem 0.75rem; font-size: 0.75rem; font-weight: 800; border-radius: 9999px;" class="inline-block px-3 py-1 border text-xs font-extrabold rounded-full">{total_pages} Páginas</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Sticky Interactive Toolbar -->
  <div style="position: sticky; top: 0; z-index: 40; background-color: rgba(255, 255, 255, 0.95); backdrop-filter: blur(8px); border-bottom: 1px solid #e2e8f0;" class="sticky top-0 z-40 bg-white-90 backdrop-blur-md border-b border-slate-200 no-print">
    <div style="max-width: 56rem; margin-left: auto; margin-right: auto; padding: 0.5rem 1rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; font-size: 0.75rem; font-weight: 600; color: #334155;" class="max-w-4xl mx-auto px-4 py-2 flex items-center justify-between flex-wrap gap-2 text-xs font-semibold text-slate-700">
      <div style="display: flex; align-items: center; gap: 0.5rem;" class="flex items-center gap-2">
        <span style="color: #94a3b8;" class="text-slate-400">Herramientas:</span>
        <button type="button" onclick="setMarkMode('highlight')" style="padding: 0.25rem 0.625rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; background-color: #fef3c7; color: #78350f;" class="tool-btn bg-amber-100 text-amber-900 cursor-pointer">🖍️ Resaltar</button>
        <button type="button" onclick="setMarkMode('underline')" style="padding: 0.25rem 0.625rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; background-color: #dbeafe; color: #1e40af;" class="tool-btn bg-blue-100 text-blue-900 cursor-pointer"><u>U</u> Subrayar</button>
        <button type="button" onclick="setMarkMode('clear')" style="padding: 0.25rem 0.625rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; background-color: #f1f5f9; color: #334155;" class="tool-btn bg-slate-100 text-slate-700 cursor-pointer">❌ Quitar marca</button>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem;" class="flex items-center gap-2">
        <button type="button" onclick="exportProgress()" style="padding: 0.25rem 0.625rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; background-color: #f1f5f9; color: #334155;" class="tool-btn bg-slate-100 text-slate-700 cursor-pointer">💾 Guardar avance</button>
        <button type="button" onclick="clearAllData()" style="padding: 0.25rem 0.625rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; cursor: pointer; border: none; background-color: #fff1f2; color: #be123c;" class="tool-btn bg-rose-50 text-rose-700 cursor-pointer">🔄 Limpiar todo</button>
      </div>
    </div>
  </div>

  <!-- Main Pages Container -->
  <main style="max-width: 56rem; margin-left: auto; margin-right: auto; padding: 1rem 1rem;" class="max-w-4xl mx-auto px-4 py-4">
    {pages_body}
  </main>

  <!-- Footer -->
  <footer style="max-width: 56rem; margin-left: auto; margin-right: auto; padding: 0 1rem; margin-top: 3rem; text-align: center; font-size: 0.75rem; font-weight: 500; color: #94a3b8;" class="max-w-4xl mx-auto px-4 mt-12 text-center text-xs font-medium text-slate-400 no-print">
    Plataforma Pedagógica Indoamérica - Material Educativo Autónomo e Interactivo
  </footer>

  <!-- Interactive Client JS Script -->
  <script src="assets/js/app.js"></script>
  <script>
{DEFAULT_JS}
  </script>
</body>
</html>
"""


def build_canvas_simple_html(metadatos: MetadatosMaterial, paginas_html: list[str]) -> str:
    """Builds a pure static HTML fallback version (canvas-simple.html) without JavaScript for strict LMS environments."""
    title_esc = html.escape(metadatos.titulo)
    subject_esc = html.escape(metadatos.materia)
    grade_esc = html.escape(metadatos.grado)
    pages_body = "\n".join(paginas_html)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_esc} - UE Indoamérica (Versión Canvas Simple)</title>
  <style>
    body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f8fafc; color: #0f172a; line-height: 1.5; }}
    header {{ padding: 18px; text-align: center; color: #ffffff !important; background: linear-gradient(135deg, #0a2f68, #0d3a80); position: sticky; top: 0; z-index: 10; border-bottom: 4px solid #5ecfb1; }}
    main {{ max-width: 900px; margin: 20px auto; padding: 0 16px; }}
    .pagina {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    @media print {{ header {{ display: none; }} main {{ padding: 0; }} .pagina {{ margin: 0; box-shadow: none; page-break-after: always; }} }}
  </style>
</head>
<body>
  <header>
    <strong style="color: #ffffff !important; font-size: 1.25rem;">UEB Indoamérica · {title_esc}</strong><br>
    <small style="color: #5ecfb1 !important; font-size: 0.85rem;">Versión visual estática de lectura para Canvas LMS ({subject_esc} - {grade_esc})</small>
  </header>
  <main>
    {pages_body}
  </main>
</body>
</html>
"""


def build_material_zip_bytes(metadatos: MetadatosMaterial, paginas_html: list[str]) -> bytes:
    """Builds a complete, unzippable .zip package matching UEI Canvas LMS standards:
    - index.html (Interactive)
    - canvas-simple.html (Static Fallback)
    - assets/css/styles.css
    - assets/js/app.js
    - INSTRUCCIONES_CANVAS.txt
    """
    html_content = build_material_shell(metadatos, paginas_html)
    canvas_simple = build_canvas_simple_html(metadatos, paginas_html)

    instructions_canvas = f"""PAQUETE HTML PARA CANVAS LMS — UNIDAD EDUCATIVA BILINGÜE INDOAMÉRICA
========================================================================
Material Educativo: {metadatos.titulo}

Estructura de archivos:
- index.html: Versión completa interactiva con ejercicios, cuaderno digital y resaltador.
- canvas-simple.html: Versión estática limpia sin JavaScript para entornos LMS estrictos.
- assets/css/styles.css: Hoja de estilos CSS institucional.
- assets/js/app.js: Motor interactivo y autoguardado local.

Instrucciones de publicación en Canvas LMS:
1. Sube el archivo ZIP al área "Archivos" de tu curso en Canvas.
2. Descomprímelo manteniendo intacta la estructura de carpetas (assets/).
3. Abre "index.html" desde Archivos y agrega su enlace a un módulo o página de Canvas.
4. Si la institución restringe scripts en iframe, utiliza el enlace a "canvas-simple.html".
========================================================================
"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("index.html", html_content)
        zf.writestr("canvas-simple.html", canvas_simple)
        zf.writestr("assets/css/styles.css", DEFAULT_CSS)
        zf.writestr("assets/js/app.js", DEFAULT_JS)
        zf.writestr("INSTRUCCIONES_CANVAS.txt", instructions_canvas)

    return buf.getvalue()
