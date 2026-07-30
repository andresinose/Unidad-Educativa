"""build_flashcards — 3D interactive flashcard collection tool.

Renders 3D flip cards with self-contained HTML and Pure CSS toggles.
No JavaScript required for rendering or flipping — 100% compatible with React dangerouslySetInnerHTML and Canvas LMS.
"""
from __future__ import annotations

import html
from pydantic import BaseModel, Field


class FlashcardItem(BaseModel):
    front: str
    back: str
    category: str = "Concepto"


class FlashcardsSchema(BaseModel):
    title: str = "Tarjetas de Memoria y Estudio"
    instructions: str = "Haz clic en una tarjeta para girarla y revisar la explicación."
    cards: list[FlashcardItem] = Field(min_length=1, max_length=15)


def build_flashcards(schema: FlashcardsSchema) -> str:
    uid = f"fc_{abs(hash((schema.title, len(schema.cards)))) % 100000}"

    cards_html = []
    for i, c in enumerate(schema.cards):
        chk_id = f"{uid}_chk_{i}"
        category_label = html.escape(c.category or f"Tarjeta {i+1}")
        front_text = html.escape(c.front)
        back_text = html.escape(c.back)

        cards_html.append(f"""
    <div class="uei-fc-card-wrapper">
      <input type="checkbox" id="{chk_id}" class="uei-fc-toggle-chk" style="display:none;" />
      <label for="{chk_id}" class="uei-fc-card-label">
        <div class="uei-fc-inner">
          <div class="uei-fc-front">
            <div class="uei-fc-top-bar">
              <span class="uei-fc-badge">{category_label}</span>
              <span class="uei-fc-num">#{i+1}</span>
            </div>
            <div class="uei-fc-body-text">{front_text}</div>
            <div class="uei-fc-hint">👆 Haz clic para girar y ver la respuesta</div>
          </div>
          <div class="uei-fc-back">
            <div class="uei-fc-top-bar">
              <span class="uei-fc-badge back">Explicación / Respuesta</span>
              <span class="uei-fc-num">#{i+1}</span>
            </div>
            <div class="uei-fc-body-text">{back_text}</div>
            <div class="uei-fc-hint">🔄 Haz clic para volver al frente</div>
          </div>
        </div>
      </label>
    </div>
        """.strip())

    grid_markup = "\n".join(cards_html)

    return f"""
<div class="uei-flashcards" id="{uid}">
  <div class="uei-fc-header">
    <span class="uei-fc-main-badge">🃏 Tarjetas de Estudio ({len(schema.cards)})</span>
    <h3 class="uei-fc-title">{html.escape(schema.title)}</h3>
    <p class="uei-fc-instructions">{html.escape(schema.instructions)}</p>
  </div>

  <div class="uei-fc-grid">
{grid_markup}
  </div>
</div>

<style>
  .uei-flashcards {{ font-family: system-ui, -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 24px; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; box-sizing: border-box; }}
  .uei-fc-header {{ margin-bottom: 24px; border-bottom: 2px solid #f1f5f9; padding-bottom: 16px; }}
  .uei-fc-main-badge {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 4px 12px; border-radius: 20px; background: #eff6ff; color: #1d4ed8; letter-spacing: 0.5px; border: 1px solid #bfdbfe; }}
  .uei-fc-title {{ margin: 10px 0 6px; color: #1e293b; font-size: 1.5rem; }}
  .uei-fc-instructions {{ color: #64748b; font-size: 0.95rem; margin: 0; }}
  
  .uei-fc-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
  
  .uei-fc-card-wrapper {{ width: 100%; min-height: 240px; perspective: 1000px; }}
  .uei-fc-card-label {{ display: block; width: 100%; height: 100%; min-height: 240px; cursor: pointer; user-select: none; }}
  
  .uei-fc-inner {{ width: 100%; height: 100%; min-height: 240px; position: relative; transform-style: preserve-3d; transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); border-radius: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); }}
  
  /* Pure CSS Toggle: Checked = Flipped */
  .uei-fc-toggle-chk:checked + .uei-fc-card-label .uei-fc-inner {{ transform: rotateY(180deg); }}
  
  .uei-fc-front, .uei-fc-back {{ position: absolute; width: 100%; height: 100%; min-height: 240px; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 16px; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; border: 2px solid #e2e8f0; }}
  
  .uei-fc-front {{ background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border-color: #cbd5e1; color: #1e293b; }}
  .uei-fc-front:hover {{ border-color: #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.15); }}
  
  .uei-fc-back {{ background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%); border-color: #86efac; color: #14532d; transform: rotateY(180deg); }}
  .uei-fc-back:hover {{ border-color: #22c55e; box-shadow: 0 10px 25px rgba(34, 197, 94, 0.15); }}
  
  .uei-fc-top-bar {{ display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; }}
  .uei-fc-badge {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase; padding: 4px 10px; border-radius: 12px; background: #3b82f6; color: #ffffff; letter-spacing: 0.5px; }}
  .uei-fc-badge.back {{ background: #16a34a; }}
  .uei-fc-num {{ font-size: 0.8rem; font-weight: 700; color: #94a3b8; }}
  
  .uei-fc-body-text {{ font-size: 1.05rem; font-weight: 600; line-height: 1.5; margin: auto 0; text-align: center; word-break: break-word; }}
  .uei-fc-hint {{ font-size: 0.78rem; color: #94a3b8; font-weight: 600; text-align: center; margin-top: 12px; border-top: 1px dashed #e2e8f0; padding-top: 8px; }}
</style>
""".strip()
