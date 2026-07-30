import pytest
from pydantic import ValidationError

from app.mcp_server.tools.activity_builder import InteractiveActivitySchema, build_interactive_activity
from app.mcp_server.tools.diagram import DiagramSchema, render_diagram


def _quiz_schema() -> InteractiveActivitySchema:
    return InteractiveActivitySchema(
        title="Comprueba: números enteros",
        instructions="Selecciona la respuesta correcta.",
        items=[
            {
                "question": "¿Cuál es el opuesto de -5?",
                "options": ["5", "-5", "0", "10"],
                "correct_index": 0,
                "explanation": "El opuesto de -5 es 5.",
            }
        ],
    )


def test_build_interactive_activity_is_self_contained():
    html = build_interactive_activity(_quiz_schema())
    assert "<script>" in html and "<style>" in html
    assert "<html" not in html and "<head" not in html  # a fragment, not a full document
    assert "Comprueba: n" in html


def test_build_interactive_activity_title_is_escaped_in_markup():
    """The title is interpolated directly into HTML markup (<h3>), so it must
    be html.escape()'d there — unlike question/option text, which only ever
    reaches the DOM via textContent (see test below) and is safe unescaped."""
    schema = InteractiveActivitySchema(title="<img src=x onerror=alert(1)>", items=[_quiz_schema().items[0]])
    html = build_interactive_activity(schema)
    assert "<img src=x onerror" not in html.split("<script>")[0]
    assert "&lt;img" in html


def test_question_text_only_reaches_dom_via_textcontent_not_innerhtml():
    """Question/option text is JSON-embedded and assigned with textContent /
    createTextNode in the generated script, never innerHTML — so it renders
    as inert text at runtime no matter what characters it contains, without
    needing (and without doing) HTML-escaping on that path."""
    schema = InteractiveActivitySchema(
        title="t",
        items=[{"question": "<img src=x onerror=alert(1)>", "options": ["a", "b"], "correct_index": 0}],
    )
    html = build_interactive_activity(schema)
    assert ".innerHTML" not in html
    assert "q.textContent =" in html
    assert "createTextNode" in html
    # The raw payload only appears inside the JSON blob fed to JSON.parse — never
    # as a sibling of a real '<img' tag outside of <script>.
    assert "<img src=x onerror" not in html.split("<script>")[0]


def test_correct_index_out_of_range_rejected():
    with pytest.raises(ValidationError):
        InteractiveActivitySchema(
            title="t", items=[{"question": "q", "options": ["a", "b"], "correct_index": 5}]
        )


def test_render_diagram_produces_valid_svg_with_nodes_and_edges():
    schema = DiagramSchema(
        title="Del entero al valor absoluto",
        nodes=[{"id": "a", "label": "Número entero"}, {"id": "b", "label": "Valor absoluto"}],
        edges=[{"source": "a", "target": "b", "label": "define"}],
    )
    svg = render_diagram(schema)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "Número entero" in svg
    assert "Valor absoluto" in svg
    assert "marker-end" in svg  # arrowhead on the edge


def test_render_diagram_escapes_labels():
    schema = DiagramSchema(
        title="t",
        nodes=[{"id": "a", "label": "<script>alert(1)</script>"}],
        edges=[],
    )
    svg = render_diagram(schema)
    assert "<script>alert" not in svg
    assert "&lt;script&gt;" in svg


def test_build_word_search_generates_interactive_grid():
    from app.mcp_server.tools.word_search import WordSearchSchema, build_word_search
    schema = WordSearchSchema(
        title="Sopa de Operaciones",
        words=["SUMA", "RESTA", "MULTIPLICACION"],
        grid_size=10
    )
    html = build_word_search(schema)
    assert "<script>" in html and "<style>" in html
    assert "Sopa de Operaciones" in html
    assert "SUMA" in html
    assert "uei-ws-grid" in html


def test_build_flashcards_generates_3d_flip_cards():
    from app.mcp_server.tools.flashcards import FlashcardsSchema, build_flashcards
    schema = FlashcardsSchema(
        title="Fichas de Álgebra",
        cards=[{"front": "¿Qué es X?", "back": "Es la incógnita.", "category": "Concepto"}]
    )
    html = build_flashcards(schema)
    assert "<style>" in html
    assert "Fichas de Álgebra" in html
    assert "¿Qué es X?" in html
    assert "rotateY(180deg)" in html


def test_build_study_guide_generates_structured_sections():
    from app.mcp_server.tools.study_guide import StudyGuideSchema, build_study_guide
    schema = StudyGuideSchema(
        title="Guía de Enteros",
        summary="Resumen de adición",
        sections=[{"heading": "Regla 1", "bullets": ["Positivos + Positivos = Positivo"], "key_takeaway": "Conservar signo"}]
    )
    html = build_study_guide(schema)
    assert "Guía de Enteros" in html
    assert "Regla 1" in html
    assert "Conservar signo" in html
