"""build_interactive_activity — the primary, dependency-free resource type.

Renders a self-check quiz (question + options + immediate feedback) as a
single self-contained HTML fragment: inline CSS, inline vanilla JS, no
external requests. This is what makes the exported resource genuinely
reusable outside the app (drop it in Canvas, a static site, anywhere).
"""
from __future__ import annotations

import html
import json

from pydantic import BaseModel, Field, field_validator


class QuizItem(BaseModel):
    question: str
    options: list[str] = Field(min_length=2, max_length=6)
    correct_index: int
    explanation: str = ""

    @field_validator("correct_index")
    @classmethod
    def _index_in_range(cls, v: int, info):
        options = info.data.get("options") or []
        if options and not (0 <= v < len(options)):
            raise ValueError("correct_index fuera de rango de options")
        return v


class InteractiveActivitySchema(BaseModel):
    title: str
    instructions: str = ""
    items: list[QuizItem] = Field(min_length=1, max_length=20)


def build_interactive_activity(schema: InteractiveActivitySchema) -> str:
    """Returns a self-contained HTML fragment (no <html>/<head>/<body>)."""
    items_data = [
        {
            "q": it.question,
            "options": it.options,
            "correct": it.correct_index,
            "explanation": it.explanation,
        }
        for it in schema.items
    ]
    # json.dumps output is embedded inside a <script> tag; escaping '</' prevents
    # it from being interpreted as a premature closing tag by an HTML parser.
    items_json = json.dumps(items_data, ensure_ascii=False).replace("</", "<\\/")
    uid = f"act_{abs(hash((schema.title, len(items_data)))) % 100000}"

    return f"""
<div class="uei-activity" id="{uid}">
  <h3 class="uei-activity-title">{html.escape(schema.title)}</h3>
  {f'<p class="uei-activity-instructions">{html.escape(schema.instructions)}</p>' if schema.instructions else ''}
  <form class="uei-activity-form" id="{uid}_form"></form>
  <button type="button" class="uei-activity-check" id="{uid}_check">Comprobar</button>
  <div class="uei-activity-score" id="{uid}_score" aria-live="polite"></div>
</div>
<style>
  .uei-activity {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; }}
  .uei-activity-title {{ margin-bottom: 4px; }}
  .uei-activity-instructions {{ color: #444; margin-top: 0; }}
  .uei-activity-question {{ margin: 18px 0; padding: 14px; border: 1px solid #ddd; border-radius: 10px; }}
  .uei-activity-question p {{ font-weight: 600; margin-top: 0; }}
  .uei-activity-question label {{ display: block; padding: 6px 8px; border-radius: 6px; cursor: pointer; }}
  .uei-activity-question label:hover {{ background: #f2f2f2; }}
  .uei-activity-question.correct {{ border-color: #2e7d32; background: #f1f8f1; }}
  .uei-activity-question.incorrect {{ border-color: #c62828; background: #fdf1f1; }}
  .uei-activity-explanation {{ margin-top: 8px; font-size: 0.92em; color: #333; display: none; }}
  .uei-activity-question.checked .uei-activity-explanation {{ display: block; }}
  .uei-activity-check {{ margin-top: 8px; padding: 10px 18px; border-radius: 8px; border: none;
    background: #1a73c1; color: #fff; font-weight: 600; cursor: pointer; }}
  .uei-activity-score {{ margin-top: 12px; font-weight: 600; }}
</style>
<script>
(function() {{
  var data = JSON.parse({json.dumps(items_json)});
  var form = document.getElementById("{uid}_form");
  data.forEach(function(item, i) {{
    var block = document.createElement("div");
    block.className = "uei-activity-question";
    block.dataset.index = i;
    var q = document.createElement("p");
    q.textContent = (i + 1) + ". " + item.q;
    block.appendChild(q);
    item.options.forEach(function(opt, j) {{
      var label = document.createElement("label");
      var input = document.createElement("input");
      input.type = "radio";
      input.name = "{uid}_q" + i;
      input.value = j;
      label.appendChild(input);
      label.appendChild(document.createTextNode(" " + opt));
      block.appendChild(label);
    }});
    var expl = document.createElement("div");
    expl.className = "uei-activity-explanation";
    expl.textContent = item.explanation || "";
    block.appendChild(expl);
    form.appendChild(block);
  }});

  document.getElementById("{uid}_check").addEventListener("click", function() {{
    var correctCount = 0;
    data.forEach(function(item, i) {{
      var block = form.querySelector('[data-index="' + i + '"]');
      var chosen = form.querySelector('input[name="{uid}_q' + i + '"]:checked');
      block.classList.add("checked");
      block.classList.remove("correct", "incorrect");
      if (chosen && parseInt(chosen.value, 10) === item.correct) {{
        block.classList.add("correct");
        correctCount++;
      }} else {{
        block.classList.add("incorrect");
      }}
    }});
    document.getElementById("{uid}_score").textContent =
      "Resultado: " + correctCount + " de " + data.length + " correctas.";
  }});
}})();
</script>
""".strip()
