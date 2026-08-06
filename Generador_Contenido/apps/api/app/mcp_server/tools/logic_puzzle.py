from __future__ import annotations

import html
import random
from typing import Literal
from pydantic import BaseModel, Field


class LogicPuzzlePair(BaseModel):
    left: str = Field(description="Concepto, pregunta o elemento de la izquierda")
    right: str = Field(description="Respuesta, definición o pareja correspondiente de la derecha")


class LogicPuzzleSchema(BaseModel):
    mode: Literal["relacionar", "ordenar"] = Field(
        default="relacionar",
        description="Modo de la actividad de lógica: 'relacionar' para emparejar columnas o 'ordenar' para secuencias paso a paso",
    )
    title: str = Field(default="Rompecabezas de Lógica y Relación", description="Título de la actividad")
    instructions: str = Field(
        default="Empareja los conceptos correctamente o clasifica los pasos según corresponda.",
        description="Instrucciones para el estudiante",
    )
    pairs: list[LogicPuzzlePair] = Field(
        default_factory=list,
        description="Lista de pares para emparejar (requerido si mode='relacionar')",
    )
    sequence: list[str] = Field(
        default_factory=list,
        description="Pasos o secuencia en orden correcto (requerido si mode='ordenar')",
    )


def build_logic_puzzle(data: LogicPuzzleSchema) -> str:
    """Renderiza un rompecabezas de lógica interactivo en HTML/CSS/JS autónomo."""
    title_esc = html.escape(data.title)
    instructions_esc = html.escape(data.instructions)

    if data.mode == "ordenar":
        seq = [s.strip() for s in data.sequence if s.strip()]
        if not seq:
            return f"""<div style="padding:20px; text-align:center; color:#e11d48; background:#fff1f2; border-radius:8px;">
                ⚠️ No se proporcionó una secuencia válida para ordenar.
            </div>"""

        # Barajar secuencia para la vista inicial
        shuffled = list(seq)
        if len(shuffled) > 1:
            # Asegurar que la secuencia barajada no sea idéntica a la respuesta a menos que tenga 1 item
            for _ in range(5):
                random.shuffle(shuffled)
                if shuffled != seq:
                    break

        items_html = []
        for idx, text in enumerate(shuffled):
            t_esc = html.escape(text)
            items_html.append(f"""
            <li class="lp-seq-item" data-correct-idx="{seq.index(text)}">
                <span class="lp-seq-text">{t_esc}</span>
                <div class="lp-seq-btns">
                    <button type="button" onclick="moveItemUp(this)">▲</button>
                    <button type="button" onclick="moveItemDown(this)">▼</button>
                </div>
            </li>
            """)

        body_content = f"""
        <div class="lp-order-wrap">
            <ul class="lp-seq-list">
                {"".join(items_html)}
            </ul>
            <div class="lp-actions">
                <button type="button" class="lp-btn-check" onclick="checkOrdering(this)">Comprobar Orden</button>
                <span class="lp-feedback"></span>
            </div>
        </div>
        """

    else:
        # Modo 'relacionar'
        valid_pairs = [p for p in data.pairs if p.left.strip() and p.right.strip()]
        if not valid_pairs:
            return f"""<div style="padding:20px; text-align:center; color:#e11d48; background:#fff1f2; border-radius:8px;">
                ⚠️ No se proporcionaron pares válidos para relacionar.
            </div>"""

        left_items = [p.left for p in valid_pairs]
        right_items = [p.right for p in valid_pairs]

        # Barajar columna derecha
        shuffled_right = list(right_items)
        random.shuffle(shuffled_right)

        left_cols_html = []
        for idx, l_text in enumerate(left_items):
            l_esc = html.escape(l_text)
            # Encontrar el índice original en right_items
            pair_idx = idx
            left_cols_html.append(f"""
            <div class="lp-match-item left" data-pair="{pair_idx}" onclick="selectLeft(this)">
                {l_esc}
            </div>
            """)

        right_cols_html = []
        for r_text in shuffled_right:
            r_esc = html.escape(r_text)
            orig_pair_idx = right_items.index(r_text)
            right_cols_html.append(f"""
            <div class="lp-match-item right" data-pair="{orig_pair_idx}" onclick="selectRight(this)">
                {r_esc}
            </div>
            """)

        body_content = f"""
        <div class="lp-match-wrap">
            <div class="lp-column">
                <h4>Columna A</h4>
                {"".join(left_cols_html)}
            </div>
            <div class="lp-column">
                <h4>Columna B</h4>
                {"".join(right_cols_html)}
            </div>
        </div>
        <div class="lp-actions" style="margin-top:20px;">
            <button type="button" class="lp-btn-check" onclick="checkMatching(this)">Comprobar Parejas</button>
            <span class="lp-feedback"></span>
        </div>
        """

    return f"""
<div class="lp-container">
    <h3 class="lp-title">{title_esc}</h3>
    <p class="lp-instructions">{instructions_esc}</p>
    {body_content}
</div>

<style>
.lp-container {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    max-width: 850px;
    margin: 0 auto;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}}
.lp-title {{
    color: #0a2f68;
    margin: 0 0 8px 0;
    font-size: 1.35rem;
    font-weight: 700;
}}
.lp-instructions {{
    color: #475569;
    font-size: 0.95rem;
    margin-bottom: 20px;
}}
.lp-match-wrap {{
    display: flex;
    gap: 24px;
}}
.lp-column {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.lp-column h4 {{
    margin: 0 0 6px 0;
    color: #0a2f68;
    font-size: 1rem;
    border-bottom: 2px solid #5ecfb1;
    padding-bottom: 4px;
}}
.lp-match-item {{
    padding: 12px 16px;
    background: #f8fafc;
    border: 2px solid #cbd5e1;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.92rem;
    color: #1e293b;
    font-weight: 500;
    transition: all 0.2s;
    user-select: none;
}}
.lp-match-item:hover {{
    border-color: #0a2f68;
    background: #f1f5f9;
}}
.lp-match-item.selected {{
    border-color: #2563eb;
    background: #eff6ff;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
}}
.lp-match-item.matched {{
    border-color: #059669;
    background: #ecfdf5;
    color: #065f46;
}}
.lp-match-item.incorrect {{
    border-color: #e11d48;
    background: #fff1f2;
    color: #881337;
}}
.lp-seq-list {{
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}}
.lp-seq-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
}}
.lp-seq-item.correct {{
    border-color: #059669;
    background: #ecfdf5;
}}
.lp-seq-item.incorrect {{
    border-color: #e11d48;
    background: #fff1f2;
}}
.lp-seq-text {{
    font-size: 0.95rem;
    color: #1e293b;
    font-weight: 500;
}}
.lp-seq-btns {{
    display: flex;
    gap: 4px;
}}
.lp-seq-btns button {{
    background: #e2e8f0;
    border: none;
    border-radius: 4px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-size: 0.75rem;
    color: #0f172a;
    font-weight: bold;
}}
.lp-seq-btns button:hover {{
    background: #cbd5e1;
}}
.lp-actions {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.lp-btn-check {{
    background: #059669;
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}}
.lp-btn-check:hover {{
    background: #047857;
}}
.lp-feedback {{
    font-size: 0.9rem;
    font-weight: 600;
}}
</style>

<script>
let selectedLeft = null;
let matches = new Map(); // leftElement -> rightElement

function selectLeft(el) {{
    const container = el.closest('.lp-container');
    container.querySelectorAll('.lp-match-item.left').forEach(i => i.classList.remove('selected'));
    el.classList.add('selected');
    selectedLeft = el;
}}

function selectRight(el) {{
    if (!selectedLeft) return;
    const container = el.closest('.lp-container');
    
    // Si la derecha ya estaba emparejada con otro, remover
    matches.forEach((r, l) => {{
        if (r === el) matches.delete(l);
    }});

    matches.set(selectedLeft, el);

    // Marcar visualmente
    selectedLeft.classList.remove('selected');
    selectedLeft.classList.add('matched');
    el.classList.add('matched');
    selectedLeft = null;
}}

function checkMatching(btn) {{
    const container = btn.closest('.lp-container');
    const leftItems = container.querySelectorAll('.lp-match-item.left');
    const feedback = container.querySelector('.lp-feedback');
    
    let correctCount = 0;
    let total = leftItems.length;

    leftItems.forEach(leftEl => {{
        const pairId = leftEl.getAttribute('data-pair');
        const matchedRight = matches.get(leftEl);

        leftEl.classList.remove('matched', 'incorrect');
        if (matchedRight) matchedRight.classList.remove('matched', 'incorrect');

        if (matchedRight && matchedRight.getAttribute('data-pair') === pairId) {{
            leftEl.classList.add('matched');
            matchedRight.classList.add('matched');
            correctCount++;
        }} else {{
            leftEl.classList.add('incorrect');
            if (matchedRight) matchedRight.classList.add('incorrect');
        }}
    }});

    if (correctCount === total) {{
        feedback.style.color = '#059669';
        feedback.textContent = '¡Excelente! Todos los pares son correctos. 🎉';
    }} else {{
        feedback.style.color = '#e11d48';
        feedback.textContent = `Pares correctos: ${{correctCount}} / ${{total}}. ¡Revisa los marcados en rojo!`;
    }}
}}

function moveItemUp(btn) {{
    const item = btn.closest('.lp-seq-item');
    const prev = item.previousElementSibling;
    if (prev) {{
        item.parentNode.insertBefore(item, prev);
    }}
}}

function moveItemDown(btn) {{
    const item = btn.closest('.lp-seq-item');
    const next = item.nextElementSibling;
    if (next) {{
        item.parentNode.insertBefore(next, item);
    }}
}}

function checkOrdering(btn) {{
    const container = btn.closest('.lp-container');
    const items = container.querySelectorAll('.lp-seq-item');
    const feedback = container.querySelector('.lp-feedback');
    let correctCount = 0;

    items.forEach((item, index) => {{
        const correctIdx = parseInt(item.getAttribute('data-correct-idx'), 10);
        item.classList.remove('correct', 'incorrect');
        if (correctIdx === index) {{
            item.classList.add('correct');
            correctCount++;
        }} else {{
            item.classList.add('incorrect');
        }}
    }});

    if (correctCount === items.length) {{
        feedback.style.color = '#059669';
        feedback.textContent = '¡Excelente! La secuencia está en el orden correcto. 🎉';
    }} else {{
        feedback.style.color = '#e11d48';
        feedback.textContent = `Pasos en posición correcta: ${{correctCount}} / ${{items.length}}.`;
    }}
}}
</script>
"""
