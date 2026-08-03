"""Tests for material_builder module: PyMuPDF rasterization, block rendering, shell assembly, and conversion pipeline."""
from __future__ import annotations

import fitz  # PyMuPDF
from app.services.material_builder.blocks import (
    BloqueCaja,
    BloqueEjercicioRelleno,
    BloqueParrafo,
    BloqueTituloSeccion,
    BloqueZonaTrabajo,
    EjercicioItem,
    MetadatosMaterial,
    PaginaTranscrita,
)
from app.services.material_builder.converter import convert_pdf_to_interactive_html
from app.services.material_builder.renderer import render_pagina
from app.services.material_builder.shell import build_material_shell


def _create_synthetic_pdf_bytes(num_pages: int = 2) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 100), f"Página Educativa Sintética #{i+1}", fontsize=20)
        page.insert_text((50, 150), f"Ejercicio 1: ¿Cuánto es {i+1} + {i+1}?", fontsize=14)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_renderer_escapes_html_and_renders_blocks():
    pagina = PaginaTranscrita(
        numero_pagina=1,
        encabezado="Encabezado Test",
        bloques=[
            BloqueTituloSeccion(texto="Unidad <1> & Intro"),
            BloqueParrafo(texto="Texto con <b>etiquetas</b>"),
            BloqueCaja(estilo="azul", titulo="Caja Nota", contenido="Contenido de caja"),
            BloqueEjercicioRelleno(
                instrucciones="Responde:",
                items=[
                    EjercicioItem(pregunta="¿2+2?", tipo="cerrada", opciones=["3", "4"], respuesta="4"),
                ],
            ),
            BloqueZonaTrabajo(instrucciones="Dibuja tu respuesta:"),
        ],
    )

    rendered_html = render_pagina(pagina)
    assert "Unidad &lt;1&gt; &amp; Intro" in rendered_html
    assert "&lt;b&gt;etiquetas&lt;/b&gt;" in rendered_html
    assert "pg1-e1" in rendered_html
    assert "pg1-z1" in rendered_html


def test_shell_assembly():
    meta = MetadatosMaterial(titulo="Matemática 10mo", materia="Matemática", total_paginas=2)
    pages = ["<section class='pagina'>Pág 1</section>", "<section class='pagina'>Pág 2</section>"]
    shell = build_material_shell(meta, pages)

    assert "Matemática 10mo" in shell
    assert "Unidad Educativa Bilingüe Indoamérica" in shell
    assert "localStorage" in shell
    assert "<noscript>" in shell


def test_mock_pdf_converter_pipeline():
    pdf_bytes = _create_synthetic_pdf_bytes(num_pages=2)

    def mock_transcriptor(png_bytes: bytes, page_num: int) -> PaginaTranscrita:
        return PaginaTranscrita(
            numero_pagina=page_num,
            encabezado=f"Simulada Pág {page_num}",
            bloques=[BloqueParrafo(texto=f"Contenido de página {page_num}")],
        )

    def mock_meta(png_bytes: bytes, filename: str) -> MetadatosMaterial:
        return MetadatosMaterial(titulo="Libro de Prueba", materia="Ciencias")

    final_html, zip_bytes, meta = convert_pdf_to_interactive_html(
        pdf_bytes=pdf_bytes,
        original_filename="test.pdf",
        transcriptor=mock_transcriptor,
        metadatos_fn=mock_meta,
    )

    assert meta.titulo == "Libro de Prueba"
    assert meta.total_paginas == 2
    assert "Contenido de página 1" in final_html
    assert "Contenido de página 2" in final_html
    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 100


def test_clean_raw_input_dict_handles_stringified_json():
    from app.services.material_builder.converter import _clean_raw_input_dict
    raw = {
        "numero_pagina": 1,
        "bloques": '[\n  {"tipo": "parrafo", "texto": "Hola mundo"}\n]'
    }
    cleaned = _clean_raw_input_dict(raw)
    parsed = PaginaTranscrita.model_validate(cleaned)
    assert parsed.numero_pagina == 1
    assert len(parsed.bloques) == 1
    assert parsed.bloques[0].texto == "Hola mundo"

