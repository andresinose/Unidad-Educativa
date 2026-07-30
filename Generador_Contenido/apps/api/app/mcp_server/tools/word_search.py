"""build_word_search — interactive word search puzzle tool.

Generates a grid-based word search puzzle with self-contained HTML/CSS/JS.
Students can click cells to select letters and find key terms from the week's topic.
"""
from __future__ import annotations

import html
import json
import random
import string
from pydantic import BaseModel, Field


class WordSearchItem(BaseModel):
    word: str
    clue: str = ""


class WordSearchSchema(BaseModel):
    title: str = "Sopa de Letras"
    instructions: str = "Encuentra las palabras clave en la sopa de letras haciendo clic en las celdas."
    words: list[str] = Field(min_length=3, max_length=15)
    grid_size: int = 12


def _clean_word(w: str) -> str:
    """Removes accents and non-alpha chars, converts to uppercase."""
    import unicodedata
    w = unicodedata.normalize('NFD', w)
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return ''.join(c for c in w.upper() if c in string.ascii_uppercase)


def _generate_grid(words: list[str], size: int = 12) -> tuple[list[list[str]], list[str]]:
    cleaned_words = [_clean_word(w) for w in words if _clean_word(w)]
    max_len = max((len(w) for w in cleaned_words), default=8)
    actual_size = max(size, max_len + 2)

    grid = [["" for _ in range(actual_size)] for _ in range(actual_size)]
    placed_words: list[str] = []

    # Directions: (dx, dy)
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for clean in cleaned_words:
        if not clean or len(clean) > actual_size:
            continue
        
        placed = False
        attempts = 0
        while not placed and attempts < 150:
            attempts += 1
            dx, dy = random.choice(directions)
            
            # Pick starting pos
            if dx == 1:
                start_x = random.randint(0, actual_size - len(clean))
            else:
                start_x = random.randint(0, actual_size - 1)

            if dy == 1:
                start_y = random.randint(0, actual_size - len(clean))
            elif dy == -1:
                start_y = random.randint(len(clean) - 1, actual_size - 1)
            else:
                start_y = random.randint(0, actual_size - 1)

            # Check overlap
            can_place = True
            for i in range(len(clean)):
                nx = start_x + i * dx
                ny = start_y + i * dy
                cell = grid[ny][nx]
                if cell != "" and cell != clean[i]:
                    can_place = False
                    break

            if can_place:
                for i in range(len(clean)):
                    nx = start_x + i * dx
                    ny = start_y + i * dy
                    grid[ny][nx] = clean[i]
                placed = True
                placed_words.append(clean)

    # Fill empty cells with random letters
    for r in range(actual_size):
        for c in range(actual_size):
            if grid[r][c] == "":
                grid[r][c] = random.choice(string.ascii_uppercase)

    return grid, placed_words


def build_word_search(schema: WordSearchSchema) -> str:
    grid, placed_words = _generate_grid(schema.words, size=schema.grid_size)
    actual_size = len(grid)
    uid = f"ws_{abs(hash((schema.title, len(placed_words)))) % 100000}"

    words_json = json.dumps(placed_words, ensure_ascii=False)

    # Pre-render grid cells in static HTML so React dangerouslySetInnerHTML displays them IMMEDIATELY!
    grid_cells_html = []
    for r in range(actual_size):
        for c in range(actual_size):
            letter = grid[r][c]
            grid_cells_html.append(
                f'<div class="uei-ws-cell" data-r="{r}" data-c="{c}" data-letter="{html.escape(letter)}">{html.escape(letter)}</div>'
            )

    # Pre-render word list in static HTML
    word_items_html = []
    for w in placed_words:
        word_items_html.append(
            f'<li class="uei-ws-item" id="{uid}_word_{w}">{html.escape(w)}</li>'
        )

    grid_markup = "\n".join(grid_cells_html)
    list_markup = "\n".join(word_items_html)

    return f"""
<div class="uei-wordsearch" id="{uid}">
  <h3 class="uei-ws-title">{html.escape(schema.title)}</h3>
  <p class="uei-ws-instructions">{html.escape(schema.instructions)}</p>
  
  <div class="uei-ws-container">
    <div class="uei-ws-grid-wrapper">
      <div class="uei-ws-grid" id="{uid}_grid" style="grid-template-columns: repeat({actual_size}, minmax(26px, 32px));">
{grid_markup}
      </div>
    </div>
    <div class="uei-ws-sidebar">
      <h4>Palabras a buscar (<span id="{uid}_found_count">0</span>/{len(placed_words)})</h4>
      <ul class="uei-ws-list" id="{uid}_list">
{list_markup}
      </ul>
    </div>
  </div>
  <div class="uei-ws-status" id="{uid}_status"></div>
</div>

<style>
  .uei-wordsearch {{ font-family: system-ui, -apple-system, sans-serif; max-width: 850px; margin: 0 auto; padding: 24px; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; box-sizing: border-box; }}
  .uei-ws-title {{ margin-top: 0; color: #1e293b; font-size: 1.4rem; }}
  .uei-ws-instructions {{ color: #64748b; font-size: 0.95rem; margin-bottom: 20px; }}
  .uei-ws-container {{ display: flex; flex-direction: row; flex-wrap: wrap; gap: 24px; align-items: flex-start; justify-content: flex-start; width: 100%; }}
  .uei-ws-grid-wrapper {{ overflow-x: auto; max-width: 100%; padding-bottom: 8px; }}
  .uei-ws-grid {{ display: inline-grid; gap: 4px; background: #f8fafc; padding: 12px; border-radius: 12px; border: 2px solid #cbd5e1; user-select: none; }}
  .uei-ws-cell {{ width: 32px; height: 32px; min-width: 32px; min-height: 32px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; color: #334155; background: #ffffff; border-radius: 6px; border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.15s ease; box-sizing: border-box; }}
  .uei-ws-cell:hover {{ background: #e0f2fe; color: #0284c7; border-color: #38bdf8; }}
  .uei-ws-cell.selected {{ background: #3b82f6; color: #ffffff; border-color: #2563eb; transform: scale(0.95); }}
  .uei-ws-cell.found {{ background: #22c55e; color: #ffffff; border-color: #16a34a; }}
  .uei-ws-sidebar {{ flex: 1; min-width: 220px; background: #f1f5f9; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; }}
  .uei-ws-sidebar h4 {{ margin-top: 0; color: #1e293b; font-size: 1rem; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }}
  .uei-ws-list {{ list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; max-height: 380px; overflow-y: auto; }}
  .uei-ws-item {{ padding: 6px 12px; background: #ffffff; border-radius: 6px; font-weight: 600; font-size: 0.88rem; color: #475569; border: 1px solid #cbd5e1; transition: all 0.2s ease; }}
  .uei-ws-item.done {{ background: #dcfce7; color: #166534; border-color: #86efac; text-decoration: line-through; opacity: 0.8; }}
  .uei-ws-status {{ margin-top: 16px; font-weight: 700; color: #16a34a; text-align: center; font-size: 1.1rem; }}
</style>

<script>
(function() {{
  var container = document.getElementById("{uid}");
  if (!container) return;
  var targetWords = JSON.parse({words_json});
  var statusEl = document.getElementById("{uid}_status");
  var foundCountEl = document.getElementById("{uid}_found_count");

  var selectedCells = [];
  var foundWords = [];

  var cells = container.querySelectorAll(".uei-ws-cell");
  cells.forEach(function(cell) {{
    cell.addEventListener("click", function() {{
      var r = cell.dataset.r;
      var c = cell.dataset.c;
      var letter = cell.dataset.letter;
      handleCellClick(cell, r, c, letter);
    }});
  }});

  function handleCellClick(cell, r, c, letter) {{
    if (cell.classList.contains("found")) return;
    
    var idx = selectedCells.findIndex(function(item) {{ return item.r === r && item.c === c; }});
    if (idx >= 0) {{
      cell.classList.remove("selected");
      selectedCells.splice(idx, 1);
    }} else {{
      cell.classList.add("selected");
      selectedCells.push({{ r: r, c: c, letter: letter, el: cell }});
    }}

    checkSelectedWord();
  }}

  function checkSelectedWord() {{
    var word = selectedCells.map(function(item) {{ return item.letter; }}).join("");
    var revWord = word.split("").reverse().join("");

    var matched = targetWords.find(function(w) {{ return (w === word || w === revWord) && !foundWords.includes(w); }});
    if (matched) {{
      foundWords.push(matched);
      selectedCells.forEach(function(item) {{
        item.el.classList.remove("selected");
        item.el.classList.add("found");
      }});
      selectedCells = [];

      var itemEl = document.getElementById("{uid}_word_" + matched);
      if (itemEl) itemEl.classList.add("done");

      foundCountEl.textContent = foundWords.length;
      if (foundWords.length === targetWords.length) {{
        statusEl.textContent = "🎉 ¡Felicidades! Has encontrado todas las palabras.";
      }}
    }}
  }}
}})();
</script>
""".strip()
