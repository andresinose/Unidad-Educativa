from __future__ import annotations

import html
import re
from typing import Literal
from pydantic import BaseModel, Field


def _normalize_word(w: str) -> str:
    """Normaliza una palabra a mayúsculas y quita acentos/caracteres especiales."""
    w = w.upper().strip()
    replacements = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "Ü": "U", "Ñ": "N"
    }
    for orig, repl in replacements.items():
        w = w.replace(orig, repl)
    return re.sub(r"[^A-Z]", "", w)


class CrosswordItem(BaseModel):
    word: str = Field(description="Palabra solución (ej. ALGEBRA)")
    clue: str = Field(description="Pista o definición para adivinar la palabra")


class CrosswordSchema(BaseModel):
    title: str = Field(default="Crucigrama Didáctico", description="Título principal de la actividad")
    instructions: str = Field(
        default="Lee las pistas y completa el crucigrama con las palabras correspondientes.",
        description="Instrucciones para el estudiante",
    )
    items: list[CrosswordItem] = Field(
        default_factory=list,
        description="Lista de palabras y sus pistas (entre 4 y 15 palabras)",
    )


def _generate_crossword_layout(items: list[CrosswordItem], max_size: int = 15):
    """Algoritmo de colocación de crucigrama 2D por intersección."""
    norm_items = []
    for item in items:
        clean = _normalize_word(item.word)
        if len(clean) >= 2:
            norm_items.append((clean, item.clue))

    if not norm_items:
        return [], []

    # Ordenar por longitud descendente
    norm_items.sort(key=lambda x: len(x[0]), reverse=True)

    grid = [["" for _ in range(max_size)] for _ in range(max_size)]
    placed = []  # dict: word, clue, row, col, direction ('across' | 'down')

    def can_place(word: str, r: int, c: int, direction: str) -> bool:
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        nr, nc = len(grid), len(grid[0])

        # Verificar límites
        if r < 0 or c < 0 or r + dr * (len(word) - 1) >= nr or c + dc * (len(word) - 1) >= nc:
            return False

        # Celda previa (debe ser vacía)
        pr, pc = r - dr, c - dc
        if 0 <= pr < nr and 0 <= pc < nc and grid[pr][pc] != "":
            return False

        # Celda posterior (debe ser vacía)
        post_r, post_c = r + dr * len(word), c + dc * len(word)
        if 0 <= post_r < nr and 0 <= post_c < nc and grid[post_r][post_c] != "":
            return False

        has_intersection = len(placed) == 0  # Primera palabra no necesita intersección

        for i, ch in enumerate(word):
            curr_r, curr_c = r + dr * i, c + dc * i
            existing = grid[curr_r][curr_c]

            if existing != "":
                if existing != ch:
                    return False
                has_intersection = True
            else:
                # Si la celda adyacente perpendicular está ocupada, no se puede colocar (a menos que cruce)
                perp_r, perp_c = (1, 0) if direction == "across" else (0, 1)
                for side in (-1, 1):
                    adj_r = curr_r + perp_r * side
                    adj_c = curr_c + perp_c * side
                    if 0 <= adj_r < nr and 0 <= adj_c < nc and grid[adj_r][adj_c] != "":
                        return False

        return has_intersection

    def do_place(word: str, clue: str, r: int, c: int, direction: str):
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        for i, ch in enumerate(word):
            grid[r + dr * i][c + dc * i] = ch
        placed.append({"word": word, "clue": clue, "row": r, "col": c, "direction": direction})

    # Colocar la primera palabra en el centro
    first_w, first_clue = norm_items[0]
    start_r = max_size // 2
    start_c = max(0, (max_size - len(first_w)) // 2)
    do_place(first_w, first_clue, start_r, start_c, "across")

    # Colocar el resto de palabras buscando intersección
    for word, clue in norm_items[1:]:
        is_placed = False
        for p in list(placed):
            p_word, p_r, p_c, p_dir = p["word"], p["row"], p["col"], p["direction"]
            p_dr, p_dc = (0, 1) if p_dir == "across" else (1, 0)

            for i, ch_p in enumerate(p_word):
                for j, ch_w in enumerate(word):
                    if ch_p == ch_w:
                        target_dir = "down" if p_dir == "across" else "across"
                        target_dr, target_dc = (0, 1) if target_dir == "across" else (1, 0)

                        curr_p_r = p_r + p_dr * i
                        curr_p_c = p_c + p_dc * i

                        target_r = curr_p_r - target_dr * j
                        target_c = curr_p_c - target_dc * j

                        if can_place(word, target_r, target_c, target_dir):
                            do_place(word, clue, target_r, target_c, target_dir)
                            is_placed = True
                            break
                if is_placed:
                    break
            if is_placed:
                break

    if not placed:
        return [], []

    # Recortar grilla al tamaño mínimo utilizado
    min_r = min(p["row"] for p in placed)
    max_r = max(p["row"] + (len(p["word"]) - 1 if p["direction"] == "down" else 0) for p in placed)
    min_c = min(p["col"] for p in placed)
    max_c = max(p["col"] + (len(p["word"]) - 1 if p["direction"] == "across" else 0) for p in placed)

    trimmed_rows = max_r - min_r + 1
    trimmed_cols = max_c - min_c + 1

    trimmed_grid = [["" for _ in range(trimmed_cols)] for _ in range(trimmed_rows)]
    for r in range(trimmed_rows):
        for c in range(trimmed_cols):
            trimmed_grid[r][c] = grid[min_r + r][min_c + c]

    # Asignar números a las celdas iniciales en orden de lectura
    numbered_positions = {}  # (r, c) -> number
    curr_num = 1

    # Reajustar coordenadas de colocadas y numerar
    for p in placed:
        p["row"] -= min_r
        p["col"] -= min_c

    placed.sort(key=lambda p: (p["row"], p["col"]))

    for p in placed:
        pos = (p["row"], p["col"])
        if pos not in numbered_positions:
            numbered_positions[pos] = curr_num
            curr_num += 1
        p["num"] = numbered_positions[pos]

    return trimmed_grid, placed


def build_crossword(data: CrosswordSchema) -> str:
    """Renderiza un crucigrama interactivo autónomo en HTML/CSS/JS."""
    title_esc = html.escape(data.title)
    instructions_esc = html.escape(data.instructions)

    grid, placed = _generate_crossword_layout(data.items)

    if not grid or not placed:
        return f"""<div style="padding:20px; text-align:center; color:#e11d48; background:#fff1f2; border-radius:8px;">
            ⚠️ No se pudo generar la grilla del crucigrama con las palabras proporcionadas.
        </div>"""

    rows = len(grid)
    cols = len(grid[0])

    # Mapa de números en celdas (row, col) -> num
    cell_nums = {}
    for p in placed:
        cell_nums[(p["row"], p["col"])] = p["num"]

    across_clues = [p for p in placed if p["direction"] == "across"]
    down_clues = [p for p in placed if p["direction"] == "down"]

    across_clues.sort(key=lambda x: x["num"])
    down_clues.sort(key=lambda x: x["num"])

    # Generar celdas HTML
    grid_cells_html = []
    for r in range(rows):
        for c in range(cols):
            ch = grid[r][c]
            num = cell_nums.get((r, c), "")
            if ch == "":
                grid_cells_html.append('<div class="cw-cell empty"></div>')
            else:
                num_tag = f'<span class="cw-num">{num}</span>' if num else ''
                grid_cells_html.append(
                    f'<div class="cw-cell active">{num_tag}'
                    f'<input type="text" maxlength="1" data-answer="{ch}" autocomplete="off" capitalize="off" />'
                    f'</div>'
                )

    grid_body = "".join(grid_cells_html)

    def render_clues_list(clue_list):
        items = []
        for p in clue_list:
            n = p["num"]
            c_esc = html.escape(p["clue"])
            items.append(f'<li><strong>{n}.</strong> {c_esc}</li>')
        return "".join(items)

    across_html = render_clues_list(across_clues)
    down_html = render_clues_list(down_clues)

    return f"""
<div class="cw-container">
    <h3 class="cw-title">{title_esc}</h3>
    <p class="cw-instructions">{instructions_esc}</p>
    
    <div class="cw-layout">
        <div class="cw-grid-wrap">
            <div class="cw-grid" style="grid-template-columns: repeat({cols}, 1fr); grid-template-rows: repeat({rows}, 1fr);">
                {grid_body}
            </div>
            <div class="cw-actions">
                <button type="button" class="cw-btn-check" onclick="checkCrossword(this)">Comprobar Respuestas</button>
                <span class="cw-feedback"></span>
            </div>
        </div>
        
        <div class="cw-clues-wrap">
            <div class="cw-clues-block">
                <h4>Horizontales</h4>
                <ul>{across_html}</ul>
            </div>
            <div class="cw-clues-block">
                <h4>Verticales</h4>
                <ul>{down_html}</ul>
            </div>
        </div>
    </div>
</div>

<style>
.cw-container {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    max-width: 900px;
    margin: 0 auto;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}}
.cw-title {{
    color: #0a2f68;
    margin: 0 0 8px 0;
    font-size: 1.35rem;
    font-weight: 700;
}}
.cw-instructions {{
    color: #475569;
    font-size: 0.95rem;
    margin-bottom: 20px;
}}
.cw-layout {{
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    align-items: flex-start;
}}
.cw-grid-wrap {{
    flex: 1 1 340px;
    display: flex;
    flex-direction: column;
    align-items: center;
}}
.cw-grid {{
    display: grid;
    gap: 2px;
    background: #0a2f68;
    padding: 3px;
    border-radius: 6px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}}
.cw-cell {{
    width: 32px;
    height: 32px;
    position: relative;
}}
.cw-cell.empty {{
    background: #1e293b;
}}
.cw-cell.active {{
    background: #ffffff;
}}
.cw-num {{
    position: absolute;
    top: 2px;
    left: 3px;
    font-size: 9px;
    font-weight: 700;
    color: #0a2f68;
    pointer-events: none;
    line-height: 1;
}}
.cw-cell input {{
    width: 100%;
    height: 100%;
    border: none;
    text-align: center;
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    background: transparent;
    outline: none;
}}
.cw-cell input.correct {{
    background: #dcfce7;
    color: #166534;
}}
.cw-cell input.incorrect {{
    background: #ffe4e6;
    color: #9f1239;
}}
.cw-actions {{
    margin-top: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.cw-btn-check {{
    background: #059669;
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}}
.cw-btn-check:hover {{
    background: #047857;
}}
.cw-feedback {{
    font-size: 0.9rem;
    font-weight: 600;
}}
.cw-clues-wrap {{
    flex: 1 1 280px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}}
.cw-clues-block h4 {{
    margin: 0 0 8px 0;
    color: #0a2f68;
    font-size: 1rem;
    border-bottom: 2px solid #5ecfb1;
    padding-bottom: 4px;
}}
.cw-clues-block ul {{
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}}
.cw-clues-block li {{
    font-size: 0.88rem;
    color: #334155;
    line-height: 1.4;
}}
</style>

<script>
function checkCrossword(btn) {{
    const wrap = btn.closest('.cw-container');
    const inputs = wrap.querySelectorAll('.cw-cell.active input');
    const feedback = wrap.querySelector('.cw-feedback');
    let correctCount = 0;
    let total = inputs.length;

    inputs.forEach(input => {{
        const expected = input.getAttribute('data-answer') || '';
        const val = input.value.trim().toUpperCase();
        if (val === expected) {{
            input.classList.remove('incorrect');
            input.classList.add('correct');
            correctCount++;
        }} else {{
            input.classList.remove('correct');
            input.classList.add('incorrect');
        }}
    }});

    if (correctCount === total) {{
        feedback.style.color = '#059669';
        feedback.textContent = '¡Excelente! Todo correcto. 🎉';
    }} else {{
        feedback.style.color = '#e11d48';
        feedback.textContent = `Aciertos: ${{correctCount}} / ${{total}}. ¡Revisa los marcados en rojo!`;
    }}
}}
</script>
"""
