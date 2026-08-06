from app.mcp_server.tools.logic_puzzle import LogicPuzzlePair, LogicPuzzleSchema, build_logic_puzzle


def test_build_logic_puzzle_relacionar():
    schema = LogicPuzzleSchema(
        mode="relacionar",
        title="Emparejar Conceptos",
        instructions="Une cada término con su definición.",
        pairs=[
            LogicPuzzlePair(left="Triángulo", right="Figura de 3 lados"),
            LogicPuzzlePair(left="Cuadrado", right="Figura de 4 lados iguales"),
        ],
    )
    html_out = build_logic_puzzle(schema)
    assert "Emparejar Conceptos" in html_out
    assert "Triángulo" in html_out
    assert "Figura de 3 lados" in html_out
    assert "checkMatching" in html_out
    assert "lp-match-item" in html_out


def test_build_logic_puzzle_ordenar():
    schema = LogicPuzzleSchema(
        mode="ordenar",
        title="Orden de Operaciones",
        instructions="Ordena los pasos para resolver una ecuación.",
        sequence=[
            "1. Eliminar paréntesis",
            "2. Resolver potencias y raíces",
            "3. Multiplicar y dividir",
            "4. Sumar y restar",
        ],
    )
    html_out = build_logic_puzzle(schema)
    assert "Orden de Operaciones" in html_out
    assert "1. Eliminar paréntesis" in html_out
    assert "moveItemUp" in html_out
    assert "checkOrdering" in html_out
