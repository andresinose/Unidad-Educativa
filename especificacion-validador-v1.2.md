# Validador Pedagógico — Especificación Técnica v1.2

> **Propósito de este documento.** Especificación completa y agnóstica al
> framework para implementar el Módulo de Validación (Fase 1) del aplicativo.
> Todo está expresado en contratos JSON, reglas de negocio y pseudocódigo:
> puede codificarse en cualquier stack (Node/Express, Laravel, Django,
> Spring, .NET, etc.). Donde se menciona una librería es solo referencia de
> capacidad, no una imposición.

---

## 1. Visión general

### 1.1 Qué hace el aplicativo

Un docente de educación primaria/secundaria sube **dos archivos**:

1. **Sílabo** (microplanificación curricular) — Word `.docx`, formato
   institucional tipo VRPA con matriz semanal.
2. **Material pedagógico** — PDF (o docx) con lecciones desarrolladas por
   semana.

El sistema cruza ambos documentos **semana por semana** y emite un veredicto:

| Veredicto | Significado |
|---|---|
| `CUMPLE` | La semana está desarrollada y cubre ≥ 80% de sus subtemas |
| `CUMPLE_PARCIAL` | Desarrollada, cobertura entre 50% y 79% |
| `NO_CUMPLE` | No desarrollada, o cobertura < 50% |

Los resultados se muestran **solo en pantalla** (no se genera reporte
descargable). Las semanas con veredicto `CUMPLE` **habilitan** el generador
de herramientas didácticas (Módulo 3); las demás quedan **bloqueadas**.

### 1.2 Filosofía del veredicto: "presencia sobre estructura"

Regla acordada con el usuario, es la decisión de diseño más importante:

- **La existencia manda, la estructura informa.** Si la semana está
  planificada en el sílabo Y desarrollada en el material, las diferencias de
  estructura o nomenclatura (ej. el sílabo dice "hoja de trabajo" y el
  material lo llama "taller integrador") **NO penalizan** el veredicto:
  se reportan como *notas informativas* de estilo neutro.
- **Solo la ausencia penaliza:** semana sin desarrollo → `NO_CUMPLE`.
- **Excepción (salvaguarda de contenido):** una semana desarrollada pero con
  contenido que no corresponde al planificado sí penaliza, a través de la
  **cobertura de subtemas** (sección 5). Esto evita que un material con 7
  semanas de cualquier cosa pase la validación.
- **Errores ortográficos se ignoran siempre.** El matching es semántico:
  "Fraciones equibalentes" ≡ "Fracciones equivalentes" ≡ "Equivalencia de
  fracciones".

### 1.3 Regla de oro: mencionado ≠ desarrollado

Aplica a dos escalas:

- **Semanas:** una semana que aparece en el índice/"Ruta del Parcial" del
  material pero sin lecciones NO cuenta como cubierta.
- **Subtemas:** un subtema que aparece en la ruta de aprendizaje o en la
  tabla de síntesis pero sin período/sección de desarrollo cuenta como
  `MENCIONADO`, no como `CUBIERTO`.

### 1.4 Propiedades del sistema

- **Stateless:** los archivos se procesan y descartan. Sin cuentas, sin
  historial, sin base de datos para la validación.
- **Anónimo:** sube → valida → ve el resultado.
- **Motor híbrido:** determinista primero (rápido, gratuito), juez LLM
  después solo para casos ambiguos (máx. 2 llamadas por validación).
- **Modo degradado:** sin API key del LLM, el sistema funciona con las
  heurísticas deterministas.

---

## 2. Arquitectura lógica

```
┌─────────────┐   multipart    ┌──────────────────────────────────────────┐
│  FRONTEND    │  2 archivos    │  BACKEND (API stateless)                  │
│  1 pantalla  │ ─────────────► │                                           │
│              │                │  A. Validación de archivos (magic bytes)  │
│  - 2 zonas   │                │  B. Extracción de texto (docx / pdf)      │
│    de carga  │                │  C. Parsers estructurales                 │
│  - botón     │                │     C1. silabo_parser                     │
│    Validar   │                │     C2. material_parser                   │
│  - sello de  │                │  D. Descomposición de subtemas (LLM/det)  │
│    veredicto │ ◄───────────── │  E. Motor de matriz de trazabilidad       │
│  - matriz    │   JSON         │  F. Verificador de coherencia transversal │
│    semanal   │  resultado     │  G. Agregador de veredictos + compuerta   │
│  - compuerta │                │  H. Juez LLM (solo casos ambiguos)        │
│    Módulo 3  │                └──────────────────────────────────────────┘
└─────────────┘
```

Componentes D–H son lógica pura (sin I/O de archivos): implementarlos como
funciones/servicios testeables de forma aislada.

---

## 3. Entrada: formatos y estructura de los documentos

### 3.1 Validación de archivos

- Aceptar por **magic bytes**, nunca por extensión:
  - `.docx` → empieza con `50 4B 03 04` ("PK\x03\x04", es un ZIP).
  - `.pdf` → empieza con `25 50 44 46` ("%PDF").
- El **sílabo debe ser `.docx`** (su estructura son tablas de Word).
  El material puede ser `.pdf` o `.docx`.
- **PDF escaneado (imagen sin capa de texto):** rechazar con error claro
  ("El PDF no contiene texto seleccionable; suba la versión digital").
  Detección: extraer texto de la primera página; si < 50 caracteres,
  es escaneado. OCR queda como mejora futura, fuera de alcance v1.2.
- Errores HTTP recomendados: `415` formato no soportado, `422` estructura
  no reconocida (sin semanas detectables).

### 3.2 Estructura del SÍLABO (formato institucional VRPA)

Documento Word compuesto de **tablas**. Elementos a extraer:

**a) Datos informativos** (pares etiqueta→valor en filas de tabla):

| Etiqueta en el documento | Campo destino |
|---|---|
| `Asignatura` | `asignatura` |
| `Nombre del docente` | `docente` |
| `Grado/Curso` | `grado` |
| `Nombre de la Unidad N` | `unidad` |
| `N° de periodos semanales` | `periodos_semanales` |
| `Fecha de Inicio` | `fecha_inicio` (formato `DD/MM/AAAA`) |
| `Fecha de finalización` | `fecha_fin` |

**b) Marcadores de semana:** filas cortas cuyo texto matchea el patrón
(insensible a mayúsculas y variantes del símbolo de grado):

```
regex: SEMANA\s*N\s*[°ºo]?\s*(\d+)
condición extra: longitud de la fila < 40 caracteres
                 (evita falsos positivos en texto corrido)
```

Las semanas pueden empezar en **0** (semana de diagnóstico). El número de
semana es el capturado, no un contador.

**c) Fila principal de cada semana** — primera fila con ≥ 5 columnas con
contenido tras el marcador. Columnas en orden:

| # | Columna | Extracción |
|---|---|---|
| 1 | Competencia general / Elemento de competencia | códigos + descripciones |
| 2 | Competencia específica | contiene `Tema: ...` + códigos específicos |
| 3 | Estrategia/Actividad metodológica | 4 fases (ver abajo) |
| 4 | Recursos | texto libre (guardar, uso informativo) |
| 5 | Nivel de logro | texto libre (informativo) |
| 6 | Técnica – Instrumento de evaluación | texto (alimenta notas informativas) |

- **Tema:** dentro de la columna 2, tras el prefijo literal `Tema:` y hasta
  el primer código de competencia o fin de celda.
  ```
  regex: Tema\s*:\s*(.+?)(?=(?:\d+\s*\.\s*[A-ZÁÉÍÓÚ]{2,}[\.\s])|$)   [DOTALL]
  ```
- **Códigos de competencia** (formato MinEduc/MCCA):
  ```
  regex: \d+\s*\.\s*[A-Z]{2,4}(?:\.[A-Z0-9]{1,6})+\.?
  ejemplos: 8.SUP.A.R.L.M.1  (general)
            8.SUP.A.R.L.M.1.1  (elemento)
            8.SUP.A.R.L.M.1.1.1  (específica — código con ≥ 6 segmentos)
  ```
  Normalizar quitando espacios internos: `8. SUP.A.R.L.M.1.1.1.` →
  `8.SUP.A.R.L.M.1.1.1`.
- **Fases de la estrategia** — dividir la columna 3 por los marcadores
  `Activación:`, `Anticipación:`, `Construcción:`, `Consolidación:`
  (cada fase = texto hasta el siguiente marcador).

**d) Bloques de ADAPTACIÓN CURRICULAR — trampa crítica del formato.**
Tras la fila principal de cada semana aparecen filas marcadoras
`ADAPTACIÓN CURRICULAR` seguidas de una fila por estudiante con necesidades
educativas especiales (en el documento real: 3 estudiantes × 7 semanas = 21
filas). Estas filas **repiten el mismo tema** de la semana.
**Regla:** detectarlas (marcador de longitud < 60 caracteres) y **excluirlas**
del parsing principal; solo contarlas en `adaptaciones: int`. Un parser
ingenuo contaría 28 "semanas" en vez de 7.

**e) Celdas fusionadas de Word:** al iterar celdas de una fila, las celdas
fusionadas se repiten. Deduplicar por identidad del elemento XML subyacente
(o por referencia/puntero según la librería usada).

### 3.3 Estructura del MATERIAL PEDAGÓGICO

Documento PDF por lecciones semanales. Elementos a extraer:

**a) Portada:** título (`MATERIAL PEDAGÓGICO`), asignatura (línea
siguiente), unidad, rango de fechas global
(`regex: Fechas?\s+(\d{2}/\d{2}/\d{4}\s+al\s+\d{2}/\d{2}/\d{4})`).

**b) "Ruta del Parcial" (índice global):** tabla al inicio que lista TODAS
las semanas con su aprendizaje central. De aquí salen las
**semanas mencionadas** (`regex: Semana\s*\n?\s*(\d+)` dentro del bloque
entre "RUTA DEL PARCIAL" y el primer "Datos informativos").

**c) Bloques "Datos informativos" (una vez por semana desarrollada):**

| Campo del bloque | Regex de extracción (multilínea) |
|---|---|
| Número de semana | `Semana(?:\s+y\s+lecci[óo]n)?\s+Semana\s+(\d+)` o línea `^Semana (\d+)$` — ambas variantes existen en el documento real |
| Tema | `^Tema\s+(.+?)$` |
| Fechas | `^Fechas?\s+(.+?)$` (formato `DD/MM/AAAA al DD/MM/AAAA`) |
| Períodos | `^Per[íi]odos?\s+(\d+)` |
| Objetivo | `^Objetivo\s+(.+?)(?=^Competencia|\Z)` [DOTALL] |
| Códigos de competencia | mismo regex de la sección 3.2 |

La página donde aparece el bloque marca el **inicio de la semana**; el fin
es el inicio de la siguiente (o el fin del documento).

**d) Índice interno de la semana — tres fuentes de evidencia de subtemas**
(en orden de fiabilidad):

| Fuente | Patrón de detección | Qué aporta |
|---|---|---|
| **Períodos** | `Per[íi]odo\s+(\d+)\s*[—–-]\s*(.+)` | Contenedor natural de subtemas: cada período (1–6) desarrolla uno. LA fuente de "desarrollo real". |
| **Ruta de aprendizaje** | bloque titulado "Ruta de aprendizaje" con ítems numerados `\d\.\s*(.+)` | Índice declarado por el material |
| **Tabla SÍNTESIS** | sección `SÍNTESIS` al cierre: pares `Concepto  Descripción` | Conceptos consolidados de la semana |

**e) Secciones/evidencias de actividades** (alimentan notas informativas):
buscar presencia (case-insensitive) de: `EXPLORA Y CONECTA`,
`ACTIVIDAD GUIADA`, `TALLER`, `PRÁCTICA PROGRESIVA`,
`COMPRUEBA TU APRENDIZAJE`, `AUTOEVALUACIÓN`, `PRUEBA`, `SÍNTESIS`,
`REFUERZO`, `GUÍA`, `HOJA`.

---

## 4. Contratos de datos (JSON Schema informal)

Todos los nombres en español, en `snake_case`. Estos contratos son el API
interno entre componentes y el contrato de respuesta del endpoint.

### 4.1 Estructuras extraídas

```jsonc
// SilaboEstructurado
{
  "asignatura": "Matemática",
  "docente": "Ing. Luis Ortiz MSc.",
  "grado": "Octavo",
  "unidad": "Números enteros",
  "fecha_inicio": "01/09/2026",
  "fecha_fin": "16/10/2026",
  "periodos_semanales": "6",
  "semanas": [
    {
      "numero": 0,
      "tema": "Diagnóstico y nivelación de aprendizajes requeridos: ...",
      "subtemas": ["diagnóstico y nivelación", "operaciones combinadas con números naturales", "criterios de divisibilidad", "resolución de problemas"],
      "competencias_generales": ["8.MED.A.R.L.M.6 Aprendizajes para el ...", "..."],
      "competencias_especificas": ["8.MED.A.R.L.M.6.1.1 Aplica algoritmos ...", "..."],
      "estrategias": {
        "Activación": "El docente propone en la pizarra ...",
        "Anticipación": "...",
        "Construcción": "...",
        "Consolidación": "..."
      },
      "tecnica_instrumento": "Técnica: Evaluación diagnóstica ... Instrumento: Prueba diagnóstica ...",
      "adaptaciones": 3
    }
  ]
}
```

```jsonc
// MaterialEstructurado
{
  "titulo": "MATERIAL PEDAGÓGICO",
  "asignatura": "Matemática",
  "unidad": "Números enteros",
  "fechas": "01/09/2026 al 16/10/2026",
  "semanas_mencionadas": [0, 1, 2, 3, 4, 5, 6],   // de la Ruta del Parcial
  "semanas_desarrolladas": [
    {
      "numero": 1,
      "tema": "Números enteros: representación, valor absoluto y orden",
      "fechas": "07/09/2026 al 11/09/2026",
      "periodos": "6",
      "objetivo": "Identificar, representar, ordenar y comparar ...",
      "competencias": ["8.SUP.A.R.L.M.1", "8.SUP.A.R.L.M.1.1", "8.SUP.A.R.L.M.1.1.1"],
      "pagina_inicio": 17,
      "pagina_fin": 40,
      "periodos_detalle": [
        { "numero": 1, "titulo": "Comprende los números enteros", "pagina": 19 },
        { "numero": 2, "titulo": "Representa enteros en la recta numérica", "pagina": 21 },
        { "numero": 3, "titulo": "Reconoce números opuestos", "pagina": 24 },
        { "numero": 4, "titulo": "Ubica puntos en el plano cartesiano", "pagina": 26 },
        { "numero": 5, "titulo": "Interpreta el valor absoluto", "pagina": 29 },
        { "numero": 6, "titulo": "Ordena y compara números enteros", "pagina": 31 }
      ],
      "ruta_aprendizaje": ["Comprende el conjunto Z", "Representa en la recta", "..."],
      "sintesis": ["Números enteros", "Recta numérica", "Opuestos", "Plano cartesiano", "Valor absoluto", "Orden"],
      "actividades": ["Explora Y Conecta", "Actividad Guiada", "Taller", "Práctica Progresiva", "Comprueba Tu Aprendizaje", "Autoevaluación", "Síntesis"]
    }
  ]
}
```

### 4.2 Respuesta del endpoint de validación

```jsonc
// ValidacionResultado — respuesta de POST /validar
{
  "veredicto_global": "CUMPLE_PARCIAL",          // CUMPLE | CUMPLE_PARCIAL | NO_CUMPLE
  "resumen": "5 de 7 semanas cumplen. Desarrolladas en el material: 5/7.",

  "semanas": {                                    // dimensión de conteo (regla dura)
    "silabo": 7,
    "material_desarrolladas": 5,
    "material_solo_mencionadas": [5, 6],
    "veredicto": "CUMPLE_PARCIAL",
    "observaciones": ["Las semanas 5, 6 aparecen en la Ruta del Parcial pero no tienen desarrollo (lecciones, actividades ni evaluación)."],
    "recomendaciones": ["Desarrollar las semanas faltantes con la misma estructura de las existentes: datos informativos, períodos, actividades guiadas, taller y evaluación."]
  },

  "detalle_semanal": [
    {
      "semana": 1,
      "tema_silabo": "Concepto de números enteros, recta numérica, ...",
      "tema_material": "Números enteros: representación, valor absoluto y orden",
      "desarrollada_en_material": true,
      "veredicto_semana": "CUMPLE",
      "habilita_generacion": true,                // compuerta del Módulo 3

      "matriz_subtemas": {
        "cobertura": 1.0,                         // cubiertos / total
        "cubiertos": 6, "total": 6,
        "subtemas": [
          {
            "texto": "valor absoluto",
            "estado": "CUBIERTO",                 // CUBIERTO | MENCIONADO | AUSENTE
            "evidencia": "Período 5 — Interpreta el valor absoluto (pág. 29)",
            "fuentes": ["periodo", "ruta", "sintesis"]
          }
        ],
        "enriquecimiento": []                     // subtemas del material no planificados en el sílabo
      },

      "notas_informativas": [                     // NO afectan el veredicto
        "El sílabo planifica 'hoja de trabajo'; el material lo cubre con 'Taller integrador' y 'Práctica progresiva'."
      ],

      "coherencia": {                             // verificaciones transversales (informativas)
        "fechas": { "ok": true, "detalle": "07/09–11/09 dentro del rango del sílabo" },
        "periodos": { "ok": true, "detalle": "6 declarados = 6 desarrollados" },
        "codigos_competencia": { "ok": true, "detalle": "8.SUP.A.R.L.M.1.1.1 presente en ambos" }
      },

      // Dimensiones informativas (se calculan pero NO puntúan):
      "resultados_aprendizaje": { "informativa": true, "veredicto": "CUMPLE", "observaciones": [], "evidencia": "códigos cubiertos 1/1" },
      "estrategias":            { "informativa": true, "veredicto": "CUMPLE_PARCIAL", "observaciones": ["..."], "evidencia": "instrumentos 1/2" }
    },
    {
      "semana": 5,
      "tema_silabo": "Potenciación, radicación y polinomios aritméticos ...",
      "tema_material": null,
      "desarrollada_en_material": false,
      "veredicto_semana": "NO_CUMPLE",
      "habilita_generacion": false,
      "matriz_subtemas": { "cobertura": 0, "cubiertos": 0, "total": 4, "subtemas": [], "enriquecimiento": [] },
      "observaciones": ["La semana 5 ('Potenciación, radicación...') aparece en la Ruta del Parcial pero no está desarrollada en el material."],
      "recomendaciones": ["Crear la lección de la semana 5 cubriendo: potenciación, radicación, polinomios aritméticos, jerarquía de operaciones."],
      "coherencia": { "fechas": { "ok": false, "detalle": "El rango 05/10–09/10 del sílabo no tiene semana en el material", "confianza": "alta" } }
    }
  ],

  "temas_validados": [                            // ENTRADA del Módulo 3 (generador)
    {
      "semana": 1,
      "tema": "Concepto de números enteros, recta numérica, ...",
      "subtemas": ["...", "..."],
      "competencias": ["8.SUP.A.R.L.M.1.1.1 Identifica, representa, ..."],
      "estrategias": { "Activación": "...", "Construcción": "..." },
      "tecnica_instrumento": "..."
    }
  ],

  "metadatos": {
    "asignatura": "Matemática", "unidad": "Números enteros",
    "docente": "Ing. Luis Ortiz MSc.",
    "fechas_silabo": "01/09/2026 - 16/10/2026",
    "fechas_material": "01/09/2026 al 16/10/2026",
    "juez_llm": true
  }
}
```

---

## 5. Motor de validación: algoritmos

### 5.1 Normalización de texto (base de todo matching)

```
funcion normalizar(texto):
    texto = minusculas(texto)
    texto = quitar_diacriticos(texto)          # NFD + eliminar marcas
    texto = reemplazar_no_alfanumerico_por_espacio(texto)
    return texto

funcion tokens(texto):
    STOPWORDS = {de, la, el, los, las, y, e, con, en, del, al, a, un, una,
                 por, para, su, sus, que, o, u, se, numeros, numero,
                 resolucion, problemas, concepto}
    resultado = conjunto vacío
    para cada palabra en normalizar(texto).split():
        si longitud(palabra) <= 2 o palabra en STOPWORDS: continuar
        # raíz burda: tolera plurales, conjugaciones y faltas leves
        agregar( palabra[0:6] si longitud > 6, si no palabra )
    return resultado

funcion similitud(a, b):
    ta, tb = tokens(a), tokens(b)
    si ta vacío o tb vacío: return 0.0
    # solapamiento sobre el conjunto MENOR (no Jaccard):
    # correcto cuando un texto es mucho más largo que el otro
    return |ta ∩ tb| / min(|ta|, |tb|)
```

### 5.2 Descomposición del tema en subtemas (componente D)

**Entrada:** los temas de TODAS las semanas del sílabo.
**Salida:** lista de subtemas atómicos por semana.

**Ruta principal (LLM, 1 sola llamada por validación):** enviar los temas
juntos, pedir JSON estricto. Regla de contexto crítica: modificadores
pertenecen a su núcleo — en "Multiplicación y división exacta de números
enteros. Propiedades, reglas de signo y problemas de aplicación", los
subtemas son [multiplicación, división exacta, propiedades, reglas de
signo, problemas de aplicación], NO se pierden ni se pegan.

Prompt de referencia (system):

```
Eres un experto en planificación curricular. Recibes los temas semanales de
un sílabo. Descompón cada tema en subtemas atómicos (unidades de contenido
enseñables por separado). Reglas:
- Conserva el contexto: "propiedades, reglas de signo" dentro de un tema de
  multiplicación pertenecen a ese tema.
- No inventes subtemas que no estén en el texto.
- Ignora conectores y frases de encuadre ("Resolución de problemas con..."
  produce el subtema "resolución de problemas de <contexto>").
Responde SOLO JSON: {"semanas": [{"numero": N, "subtemas": ["...", ...]}]}
```

**Ruta fallback (determinista, sin API key):**

```
funcion descomponer_fallback(tema):
    # separar por: punto, coma, " y " — pero NO dentro de conectores
    NO_SEPARAN = {"criterios de", "reglas de", "relaciones de",
                  "resolución de", "análisis de", "jerarquía de"}
    segmentos = dividir por [.,;] y por " y " respetando NO_SEPARAN
    return [limpiar(s) para s en segmentos si tokens(s) no vacío]
```

**Criterio de aceptación** (contra el sílabo real de referencia):
S0→4, S1→6, S2→3, S3→3, S4→5, S5→4, S6→2 subtemas.

### 5.3 Matriz de trazabilidad subtema × evidencia (componente E — el corazón)

```
funcion construir_matriz(subtemas_silabo, semana_material):
    fuentes = {
      "periodo":  [titulo de cada periodo_detalle],   # = DESARROLLO
      "ruta":     semana_material.ruta_aprendizaje,   # = MENCIÓN
      "sintesis": semana_material.sintesis            # = MENCIÓN
    }
    UMBRAL_MATCH = 0.5     # similitud mínima para considerar correspondencia

    matriz = []
    para cada sub en subtemas_silabo:
        hallado_en = {}
        para cada (nombre, items) en fuentes:
            mejor = max( similitud(sub, item) para item en items )  # y el item
            si mejor >= UMBRAL_MATCH: hallado_en[nombre] = item_ganador

        si "periodo" en hallado_en:
            estado = CUBIERTO
            evidencia = "Período N — <título> (pág. X)"
        sino si hallado_en no vacío:
            estado = MENCIONADO        # está en ruta/síntesis sin período propio
        sino:
            estado = AUSENTE           # candidato a juez LLM

        matriz.agregar({texto: sub, estado, evidencia, fuentes: claves(hallado_en)})

    # Escalado al juez LLM: SOLO los AUSENTES/MENCIONADOS, en UN solo batch
    dudosos = [m para m en matriz si m.estado != CUBIERTO]
    si juez_disponible() y dudosos no vacío:
        resoluciones = juez_llm(dudosos, semana_material)   # sección 5.6
        aplicar(resoluciones, matriz)     # puede subirlos a CUBIERTO

    # Cruce inverso (enriquecimiento): períodos sin subtema del sílabo
    enriquecimiento = [p.titulo para p en periodos_detalle
                       si max(similitud(p.titulo, s) para s en subtemas_silabo) < UMBRAL_MATCH]

    cobertura = contar(estado == CUBIERTO) / longitud(matriz)
    return {matriz, cobertura, enriquecimiento}
```

**Generación de observaciones/recomendaciones por subtema no cubierto:**

- `AUSENTE`: *"El subtema '<X>' de la semana N no tiene desarrollo en el
  material; se esperaría entre las págs. A–B."* → recomendación: *"Agregar
  un período o sección que desarrolle '<X>' con al menos una actividad."*
- `MENCIONADO`: *"El subtema '<X>' aparece en la ruta/síntesis de la semana
  N pero no tiene período de desarrollo."*

### 5.4 Veredicto por semana (componente G)

```
funcion veredicto_semana(semana_silabo, semana_material_o_nulo, matriz):
    si semana_material es nulo:                       # NO DESARROLLADA
        return NO_CUMPLE, habilita_generacion = falso
        # observación distinta según esté en la ruta o totalmente ausente

    # DESARROLLADA → manda la cobertura de subtemas (umbrales congelados):
    si matriz.cobertura >= 0.80:  v = CUMPLE
    sino si matriz.cobertura >= 0.50:  v = CUMPLE_PARCIAL
    sino:  v = NO_CUMPLE

    habilita_generacion = (v == CUMPLE)               # compuerta ESTRICTA
    return v, habilita_generacion
```

**Importante:** RA y estrategias ya NO participan del veredicto. Se calculan
(algoritmos 5.7) y se emiten con `informativa: true` + notas.

### 5.5 Veredicto global

```
funcion veredicto_global(detalle):
    n_total  = |detalle|
    n_cumple = contar(veredicto_semana == CUMPLE)
    peor     = max(detalle, orden: CUMPLE < CUMPLE_PARCIAL < NO_CUMPLE)

    si todas CUMPLE:                         return CUMPLE
    si n_cumple >= redondear(n_total * 0.5): return CUMPLE_PARCIAL
        # mayoría cumple: el faltante ya está reportado; no colapsar a NO_CUMPLE
    si no:                                   return peor
```

### 5.6 Juez LLM (componente H) — alcance acotado

Se activa solo si existe la API key. **Máximo 2 llamadas por validación:**

1. **Descomposición de subtemas** (sección 5.2) — 1 llamada.
2. **Resolución de subtemas dudosos en batch** — 1 llamada con TODOS los
   dudosos de TODAS las semanas.

Prompt de referencia del juez (system):

```
Eres un evaluador pedagógico. Para cada subtema dudoso decide si el material
de la semana realmente lo desarrolla. Ignora ortografía, sinónimos y orden
("valor absoluto" ≡ "interpreta el valor absoluto" ≡ "distancia al cero").
Equivalencias pedagógicas válidas: taller ≈ hoja de trabajo ≈ guía;
prueba corta ≈ evaluación escrita ≈ comprueba tu aprendizaje.
Responde SOLO JSON:
{"resoluciones": [{"semana": N, "subtema": "...",
  "estado": "CUBIERTO|MENCIONADO|AUSENTE",
  "evidencia": "...", "justificacion": "una línea"}]}
```

Contexto que se envía por dudoso: el subtema + los títulos de períodos,
ruta y síntesis de su semana (NO el texto completo del material: controla
costo y contexto).

**Manejo de fallos del LLM:** timeout, JSON inválido o veredicto fuera del
enum → conservar el resultado determinista (nunca fallar la validación por
el juez). Limpiar fences ` ```json ` antes de parsear. Reintento máx. 1.

### 5.7 Dimensiones informativas (se calculan, no puntúan)

**Resultados de aprendizaje (por códigos):**

```
cod_silabo   = códigos de ≥6 segmentos extraídos de competencias_especificas
cod_material = códigos extraídos del bloque Datos informativos de la semana
cubiertos    = {c en cod_silabo si algún cm en cod_material tiene prefijo común}
si cubiertos == cod_silabo → nota: "competencias evidenciadas N/N"
si no → nota informativa listando los códigos sin evidencia
```

**Estrategias/instrumentos:**

```
INSTRUMENTOS = { taller: /\btaller/, hoja de trabajo: /hoja/,
                 prueba: /prueba/, autoevaluación: /autoevaluaci/,
                 guía-refuerzo: /(gu[íi]a|refuerzo)/ }
exigidos  = instrumentos presentes en (estrategias + tecnica_instrumento) del sílabo
presentes = instrumentos presentes en (actividades + objetivo) del material
faltan    = exigidos − presentes
→ nota informativa: "El sílabo planifica <faltan>; el material lo cubre
   con <secciones equivalentes detectadas>."  (redacción NEUTRA, sin tono de falta)
```

### 5.8 Verificador de coherencia transversal (componente F)

Todas informativas, con un caso especial de **refuerzo de confianza**:

```
1) FECHAS
   rango_silabo = [fecha_inicio, fecha_fin]
   rangos_material = fechas de cada semana desarrollada
   - cada rango semanal debe caer dentro del rango del sílabo
   - calcular semanas lectivas (lunes–viernes) del rango del sílabo SIN
     rango en el material → "huecos"
   - SI los huecos coinciden con las semanas no desarrolladas detectadas
     por estructura → marcar esas observaciones con confianza: "alta"
     (dos vías independientes confirman el faltante)

2) PERÍODOS
   periodos_semanales del sílabo == campo Períodos de cada semana del material
   y == cantidad de "Período N —" detectados en la semana

3) CÓDIGOS
   códigos específicos del sílabo presentes en el bloque de la semana del material
```

---

## 6. Compuerta del Módulo 3 (generador de herramientas)

- **Regla estricta:** solo semanas con `veredicto_semana == CUMPLE` tienen
  `habilita_generacion: true`. Semana no hecha o mal diseñada (cobertura
  insuficiente) = seleccionable **deshabilitado** en la UI, con tooltip:
  *"Corrige el material de esta semana para habilitar la generación"*.
- El arreglo `temas_validados` de la respuesta es el **contrato de entrada**
  del Módulo 3: incluye tema, subtemas, competencias específicas,
  estrategias por fase y técnica/instrumento — para que las herramientas
  generadas (hoja de trabajo, quiz, presentación, recurso lúdico) se alineen
  a la planificación real de esa semana.
- Formatos de salida previstos del Módulo 3 (fuera de alcance v1.2, se
  documenta para no romper el contrato): docx, pdf, pptx, html, imagen
  (ej. sopa de letras).

---

## 7. API HTTP

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/validar` | multipart: `silabo` (file), `material` (file), `usar_llm` (bool, default true) → `ValidacionResultado` |
| `GET` | `/salud` | `{ "estado": "ok", "juez_llm": true|false }` |

Errores: `415` (tipo de archivo), `422` (estructura irreconocible, con
mensaje orientado al docente), `500` genérico. CORS abierto para el
frontend. Archivos temporales SIEMPRE eliminados (try/finally).

Variables de entorno: `ANTHROPIC_API_KEY` (opcional),
`VALIDADOR_MODELO` (default del juez; usar un modelo de la familia Claude
económico para la descomposición y uno de razonamiento para el juez si se
quiere separar).

---

## 8. Frontend (una pantalla)

Flujo: 2 zonas de carga (sílabo .docx / material .pdf o .docx) → botón
"Validar documentos" → resultado.

Componentes del resultado:

1. **Sello de veredicto global** (elemento firma de la UI: recuadro con
   borde doble, ligera rotación, color por veredicto —
   verde `CUMPLE`, ámbar `CUMPLE PARCIAL`, rojo `NO CUMPLE`).
2. **Resumen:** X de Y semanas cumplen · desarrolladas N/M · solo
   mencionadas: [...].
3. **Matriz semanal:** una fila por semana con UN veredicto + barra de
   cobertura de subtemas ("5/6 subtemas · 83%"). Fila expandible con:
   - matriz de subtemas (✅ CUBIERTO / ⚠️ MENCIONADO / ❌ AUSENTE, con
     evidencia y página),
   - notas informativas (estilo ℹ️ gris **neutro**, visualmente distinto de
     observaciones ámbar/rojas — el docente debe percibir que no penalizan),
   - coherencia (fechas/períodos/códigos).
4. **Sección "Herramientas didácticas":** una tarjeta por semana; botón
   "Generar herramientas" habilitado solo si `habilita_generacion`.

Accesibilidad mínima: foco visible en zonas de carga, `prefers-reduced-motion`
respetado, tabla usable en móvil (ocultar columna de tema largo en < 720px).

---

## 9. Casos de prueba (regresión obligatoria)

### 9.1 Caso real de referencia (Matemática 8.º EGB, T1-P1)

Par: sílabo `Syllabu_micro_8vo_T1_P1.docx` + material `main__1_.pdf`
(94 págs.). Resultado esperado EXACTO:

| Verificación | Valor esperado |
|---|---|
| Semanas del sílabo | 7 (numeradas 0–6) |
| Adaptaciones excluidas | 3 por semana (21 filas ignoradas) |
| Semanas mencionadas en material | [0,1,2,3,4,5,6] |
| Semanas desarrolladas | [0,1,2,3,4] |
| Subtemas por semana (sílabo) | S0:4 · S1:6 · S2:3 · S3:3 · S4:5 |
| Cobertura | S0 4/4 · S1 6/6 · S2 3/3 · S3 3/3 · S4 5/5 |
| Veredictos S0–S4 | CUMPLE (S1 con nota informativa de instrumentos: "hoja de trabajo" ↔ "taller integrador/práctica progresiva") |
| Enriquecimiento | S2: "propiedades de la adición" · S4: "operaciones combinadas de mult./div." |
| Veredictos S5–S6 | NO_CUMPLE, observación "mencionadas en Ruta del Parcial sin desarrollo", **confianza: alta** (huecos de fechas 05–09/10 y 12–16/10 coinciden) |
| Veredicto global | CUMPLE_PARCIAL |
| `temas_validados` (compuerta) | semanas [0,1,2,3,4] |
| Fechas y períodos | coherentes (rango global igual; 6=6 períodos) |

### 9.2 Casos sintéticos

| # | Mutación sobre el caso real | Resultado esperado |
|---|---|---|
| A | Quitar 1 período a la S1 del material (queda 5/6 = 83%) | S1 sigue CUMPLE |
| B | Quitar 2 períodos a la S1 (4/6 = 67%) | S1 → CUMPLE_PARCIAL, compuerta cerrada, observaciones con los 2 subtemas ausentes |
| C | Reemplazar el contenido de la S3 por un tema ajeno (geometría) | cobertura ≈ 0% → S3 NO_CUMPLE aunque "exista" |
| D | Material con las 7 semanas desarrolladas | global CUMPLE, compuerta [0..6] |
| E | Sílabo con tema con faltas ortográficas ("Fraciones equibalentes") | matching lo resuelve (normalización o juez), sin penalización |
| F | PDF escaneado (sin capa de texto) | 422 con mensaje claro |
| G | Archivo .docx renombrado a .pdf | detectado por magic bytes, procesado como docx o rechazado con 415 coherente |
| H | Sin `ANTHROPIC_API_KEY` | validación completa en modo degradado; `metadatos.juez_llm=false` |
| I | Semana en material no presente en el sílabo | nota informativa de material huérfano; no penaliza |

### 9.3 Pruebas unitarias mínimas por componente

- `normalizar/tokens/similitud`: tildes, ortografía, textos de longitudes
  muy distintas.
- `silabo_parser`: celdas fusionadas deduplicadas; adaptaciones excluidas;
  tema extraído sin arrastrar códigos; 4 fases separadas.
- `material_parser`: ambas variantes del campo semana ("Semana y lección
  Semana N" y "Semana N" sola); ruta vs desarrollo; períodos con título y
  página.
- `descomposicion`: fallback determinista produce los conteos de 5.2.
- `matriz`: estados CUBIERTO/MENCIONADO/AUSENTE; enriquecimiento; umbrales
  80/50 en los bordes exactos (0.80 → CUMPLE; 0.79→PARCIAL; 0.50→PARCIAL;
  0.49→NO_CUMPLE).
- `juez`: respuesta malformada → conserva determinista.

---

## 10. Decisiones de producto congeladas (changelog de acuerdos)

| Decisión | Valor |
|---|---|
| Usuarios | Docentes de primaria y secundaria (Ecuador) |
| Formatos de entrada | Sílabo: Word .docx · Material: PDF/Word |
| Comparación de temas | Semana por semana (S3 sílabo vs S3 material) |
| Escala de veredicto | CUMPLE / CUMPLE_PARCIAL / NO_CUMPLE, con observaciones y recomendaciones en parcial y negativo |
| Filosofía v1.1+ | Presencia sobre estructura; nombres/estructura distintos = notas informativas |
| Salvaguarda de contenido | Cobertura de subtemas (única métrica de contenido que puntúa) |
| Umbrales de cobertura | **≥80% CUMPLE · 50–79% PARCIAL · <50% NO_CUMPLE** |
| Regla de oro | Mencionado ≠ desarrollado (semanas y subtemas) |
| Compuerta Módulo 3 | Estricta: solo CUMPLE habilita generación |
| Reporte | Solo en pantalla, sin descarga |
| Sesión | Anónima, stateless, sin historial |
| Ortografía | Nunca penaliza |
| Juez LLM | Opcional, máx. 2 llamadas/validación, con modo degradado |
| Módulo 2 (scraping) | Solo repositorios abiertos (MinEduc/CC/GeoGebra), sin evasión de bots, jobs en segundo plano, metadatos de licencia/atribución |
| Módulo 3 (generador) | Hojas de trabajo, quizzes, presentaciones, recursos lúdicos → docx/pdf/pptx/html/imagen |

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Formatos de otros docentes sin tabla SÍNTESIS o sin períodos titulados | Las 3 fuentes de evidencia son redundantes: con una sola disponible la matriz opera. Si ninguna existe, degradar a similitud tema-completo vs texto de la semana y marcarlo en metadatos |
| Sílabos de otras instituciones con otra plantilla | El parser está calibrado al formato VRPA; documentar el requisito en la UI. A futuro: extracción por LLM como parser universal de respaldo |
| Costo del LLM | Tope de 2 llamadas; enviar índices, no texto completo |
| PDF escaneados | Rechazo claro en v1.2; OCR como mejora |
| Falsos AUSENTE por vocabulario muy distinto | El juez LLM resuelve; sin API key, el umbral 0.5 de matching + raíz de 6 caracteres tolera variación moderada |

---

*Documento de especificación v1.2 — listo para implementación en cualquier
framework. Los valores de las secciones 5 y 9 fueron verificados contra los
documentos reales de referencia mediante auditoría funcional manual y una
implementación de prueba.*
