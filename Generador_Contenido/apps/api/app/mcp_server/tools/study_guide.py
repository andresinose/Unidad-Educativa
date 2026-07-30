"""build_study_guide — interactive study guide and cheat sheet tool.

Renders structured study sections, key takeaways, and study tips in self-contained HTML/CSS.
"""
from __future__ import annotations

import html
from pydantic import BaseModel, Field


class StudyGuideSection(BaseModel):
    heading: str
    bullets: list[str] = Field(min_length=1, max_length=6)
    key_takeaway: str = ""


class StudyGuideSchema(BaseModel):
    title: str = "Ficha de Estudio y Repaso"
    summary: str = ""
    sections: list[StudyGuideSection] = Field(min_length=1, max_length=6)


def build_study_guide(schema: StudyGuideSchema) -> str:
    uid = f"sg_{abs(hash((schema.title, len(schema.sections)))) % 100000}"

    sections_html = []
    for sec in schema.sections:
        bullets_items = "".join(f"<li>{html.escape(b)}</li>" for b in sec.bullets)
        takeaway_html = (
            f'<div class="uei-sg-takeaway">💡 <strong>Idea Clave:</strong> {html.escape(sec.key_takeaway)}</div>'
            if sec.key_takeaway else ""
        )
        sections_html.append(f"""
        <div class="uei-sg-section">
          <h4 class="uei-sg-heading">{html.escape(sec.heading)}</h4>
          <ul class="uei-sg-bullets">{bullets_items}</ul>
          {takeaway_html}
        </div>
        """)

    return f"""
<div class="uei-studyguide" id="{uid}">
  <div class="uei-sg-header">
    <span class="uei-sg-badge">📌 Material de Estudio</span>
    <h3 class="uei-sg-title">{html.escape(schema.title)}</h3>
    {f'<p class="uei-sg-summary">{html.escape(schema.summary)}</p>' if schema.summary else ''}
  </div>

  <div class="uei-sg-body">
    {"".join(sections_html)}
  </div>
</div>

<style>
  .uei-studyguide {{ font-family: system-ui, -apple-system, sans-serif; max-width: 750px; margin: 0 auto; padding: 24px; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
  .uei-sg-header {{ border-bottom: 2px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 20px; }}
  .uei-sg-badge {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; padding: 4px 10px; border-radius: 20px; background: #e0e7ff; color: #3730a3; letter-spacing: 0.5px; }}
  .uei-sg-title {{ margin: 10px 0 6px; color: #1e293b; font-size: 1.5rem; }}
  .uei-sg-summary {{ color: #475569; font-size: 1rem; margin: 0; line-height: 1.5; }}
  
  .uei-sg-body {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
  .uei-sg-section {{ background: #f8fafc; border-radius: 12px; padding: 18px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between; }}
  .uei-sg-heading {{ margin-top: 0; margin-bottom: 12px; color: #0f172a; font-size: 1.1rem; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; }}
  .uei-sg-bullets {{ margin: 0 0 12px; padding-left: 20px; color: #334155; line-height: 1.6; font-size: 0.95rem; }}
  .uei-sg-takeaway {{ background: #fef3c7; border: 1px solid #fde68a; color: #92400e; padding: 10px 14px; border-radius: 8px; font-size: 0.88rem; margin-top: auto; }}
</style>
""".strip()
