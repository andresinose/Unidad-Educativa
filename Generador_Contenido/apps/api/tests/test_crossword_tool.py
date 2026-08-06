from app.mcp_server.tools.crossword import CrosswordItem, CrosswordSchema, build_crossword, _normalize_word, _generate_crossword_layout


def test_normalize_word():
    assert _normalize_word("Álgebra") == "ALGEBRA"
    assert _normalize_word("Ecuación 123!") == "ECUACION"
    assert _normalize_word("  geometría  ") == "GEOMETRIA"


def test_generate_crossword_layout():
    items = [
        CrosswordItem(word="ALGEBRA", clue="Rama de la matemática que utiliza símbolos y letras"),
        CrosswordItem(word="ECUACION", clue="Igualdad con una o varias incógnitas"),
        CrosswordItem(word="GEOMETRIA", clue="Estudio de las propiedades de las figuras"),
        CrosswordItem(word="MATEMATICA", clue="Ciencia deductiva"),
    ]
    grid, placed = _generate_crossword_layout(items)
    assert len(grid) > 0
    assert len(placed) >= 2
    for p in placed:
        assert p["word"] in ["ALGEBRA", "ECUACION", "GEOMETRIA", "MATEMATICA"]
        assert "row" in p and "col" in p and "direction" in p


def test_build_crossword_html_escaping():
    schema = CrosswordSchema(
        title="<script>alert(1)</script> Crucigrama",
        instructions="<b>Sigue las instrucciones</b>",
        items=[
            CrosswordItem(word="SUMA", clue="Operación <básica> de adición"),
            CrosswordItem(word="RESTA", clue="Operación & sustracción"),
        ],
    )
    html_out = build_crossword(schema)
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out
    assert "SUMA" in html_out or 'data-answer="S"' in html_out
    assert "cw-container" in html_out
    assert "checkCrossword" in html_out
