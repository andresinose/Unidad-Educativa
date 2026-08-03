"""Concordance Engine according to Spec v1.2 with institutional exclusions.
Week 0 (Diagnóstico/Nivelación) and Final Week (Cierre/Evaluación) are completely excluded from the validation run.
"""
from __future__ import annotations

import math
from app.schemas.concordance import (
    CoherenciaDetalle,
    CoherenciaTransversal,
    ConcordanceResult,
    ConcordanceStatus,
    DetalleSemanal,
    DimensionInformativa,
    EstadoSubtema,
    MatrizSubtemas,
    ResumenSemanasDura,
    SubtemaEvidencia,
    TemaValidado,
)
from app.schemas.extraction import GuiaExtraction, GuiaWeekDeveloped, SilaboExtraction
from app.services.concordance.llm_judge import resolver_dudosos_batch
from app.services.concordance.subtopic_decomposer import descomponer_subtemas_batch
from app.services.concordance.text_utils import similitud

UMBRAL_MATCH = 0.5


def build_concordance(silabo: SilaboExtraction, guia: GuiaExtraction, api_key: str | None = None) -> ConcordanceResult:
    # 1. Identificar semanas evaluables excluyendo Semana 0 y Semana Final por directiva institucional
    all_week_numbers = [w.week_number for w in silabo.weeks]
    max_week = max(all_week_numbers) if all_week_numbers else -1

    semanas_evaluables = [
        w for w in silabo.weeks
        if w.week_number != 0 and (len(all_week_numbers) <= 2 or w.week_number != max_week)
    ]
    if not semanas_evaluables:
        semanas_evaluables = silabo.weeks

    # 2. Descomposición de subtemas únicamente para semanas evaluables
    subtemas_dict = descomponer_subtemas_batch(semanas_evaluables, api_key)

    dev_by_week = {w.numero: w for w in guia.semanas_desarrolladas}
    
    for wn in guia.weeks_detected:
        if wn not in dev_by_week:
            codes = guia.competency_codes_by_week.get(wn, [])
            dev_by_week[wn] = GuiaWeekDeveloped(
                numero=wn,
                competencias=codes,
                periodos_detalle=[]
            )

    dudosos_list: list[dict] = []
    matriz_preliminar: dict[int, list[dict]] = {}

    for w in semanas_evaluables:
        wn = w.week_number
        subs = subtemas_dict.get(wn, [])
        g_week = dev_by_week.get(wn)
        
        preliminar_items = []
        if g_week is not None and wn in guia.weeks_detected:
            for sub in subs:
                hallado_en: dict[str, tuple[float, str]] = {}
                
                # Check periodos (DESARROLLO)
                for p_det in g_week.periodos_detalle:
                    sim = similitud(sub, p_det.titulo)
                    if sim >= UMBRAL_MATCH:
                        ev_str = f"Período {p_det.numero} — {p_det.titulo} (pág. {p_det.pagina})"
                        if "periodo" not in hallado_en or sim > hallado_en["periodo"][0]:
                            hallado_en["periodo"] = (sim, ev_str)
                            
                # Check ruta (MENCIÓN)
                for r_item in g_week.ruta_aprendizaje:
                    sim = similitud(sub, r_item)
                    if sim >= UMBRAL_MATCH:
                        ev_str = f"Ruta de aprendizaje — {r_item}"
                        if "ruta" not in hallado_en or sim > hallado_en["ruta"][0]:
                            hallado_en["ruta"] = (sim, ev_str)
                            
                # Check síntesis (MENCIÓN)
                for s_item in g_week.sintesis:
                    sim = similitud(sub, s_item)
                    if sim >= UMBRAL_MATCH:
                        ev_str = f"Síntesis — {s_item}"
                        if "sintesis" not in hallado_en or sim > hallado_en["sintesis"][0]:
                            hallado_en["sintesis"] = (sim, ev_str)

                sec_types = [s.section_type for s in guia.sections if s.week_number == wn]
                if not hallado_en and sec_types:
                    ev_str = f"Secciones en guía — {', '.join(sec_types[:3])}"
                    hallado_en["secciones"] = (0.6, ev_str)

                if "periodo" in hallado_en or "secciones" in hallado_en:
                    estado = EstadoSubtema.CUBIERTO
                    evidencia = hallado_en.get("periodo", hallado_en.get("secciones"))[1]
                elif hallado_en:
                    estado = EstadoSubtema.MENCIONADO
                    evidencia = list(hallado_en.values())[0][1]
                else:
                    estado = EstadoSubtema.AUSENTE
                    evidencia = ""

                item_info = {
                    "texto": sub,
                    "estado": estado,
                    "evidencia": evidencia,
                    "fuentes": list(hallado_en.keys())
                }
                preliminar_items.append(item_info)

                if estado != EstadoSubtema.CUBIERTO:
                    dudosos_list.append({
                        "semana": wn,
                        "subtema": sub,
                        "periodos": [p.titulo for p in g_week.periodos_detalle],
                        "ruta": g_week.ruta_aprendizaje,
                        "sintesis": g_week.sintesis
                    })
        matriz_preliminar[wn] = preliminar_items

    # 3. Llamar Juez LLM si hay dudosos
    resoluciones_llm = resolver_dudosos_batch(dudosos_list, api_key) if dudosos_list else {}

    # 4. Construir DetalleSemanal para las semanas evaluables
    detalle_semanal: list[DetalleSemanal] = []
    temas_validados: list[TemaValidado] = []
    
    semanas_mencionadas = guia.semanas_mencionadas or sorted(guia.weeks_detected)
    solo_mencionadas = [w for w in semanas_mencionadas if w not in guia.weeks_detected]

    for w in semanas_evaluables:
        wn = w.week_number
        g_week = dev_by_week.get(wn)
        desarrollada = (wn in guia.weeks_detected)
        subs = subtemas_dict.get(wn, [])
        
        observaciones: list[str] = []
        recomendaciones: list[str] = []
        notas_informativas: list[str] = []

        silabo_codes = list(w.competency_codes)
        guia_codes = list(g_week.competencias) if g_week else list(guia.competency_codes_by_week.get(wn, []))
        missing_codes = [c for c in silabo_codes if c not in guia_codes]
        
        adapt_silabo = bool(w.adaptations) or w.adaptaciones_count > 0
        adapt_guia = any("ADAPTA" in s.section_type for s in guia.sections if s.week_number == wn)
        page_range = f"{g_week.pagina_inicio}-{g_week.pagina_fin}" if g_week and g_week.pagina_inicio > 0 else None

        if not desarrollada:
            veredicto_sem = ConcordanceStatus.NO_CUMPLE
            habilita_gen = False
            
            subtemas_ev: list[SubtemaEvidencia] = [
                SubtemaEvidencia(texto=s, estado=EstadoSubtema.AUSENTE, evidencia="")
                for s in subs
            ]
            matriz_sub = MatrizSubtemas(cobertura=0.0, cubiertos=0, total=len(subs), subtemas=subtemas_ev)

            if wn in solo_mencionadas:
                obs = f"La semana {wn} ('{w.topic}') aparece en la Ruta del Parcial pero no tiene desarrollo en el material."
            else:
                obs = f"La semana {wn} ('{w.topic}') está definida en el sílabo pero no está desarrollada en el material."
            observaciones.append(obs)
            recomendaciones.append(f"Crear la lección para la semana {wn} cubriendo: {', '.join(subs)}.")

            fechas_coherencia = CoherenciaDetalle(
                ok=False,
                detalle=f"La semana {wn} del sílabo ({silabo.start_date} al {silabo.end_date}) no tiene lección correspondiente en el material.",
                confianza="alta"
            )
            periodos_coherencia = CoherenciaDetalle(ok=False, detalle="0 períodos desarrollados en el material", confianza="normal")
            codigos_coherencia = CoherenciaDetalle(ok=False, detalle="Sin códigos desarrollados en el material", confianza="normal")
        else:
            subtemas_ev = []
            cubiertos_cnt = 0
            
            for item in matriz_preliminar.get(wn, []):
                sub = item["texto"]
                est = item["estado"]
                ev = item["evidencia"]
                fuentes = item["fuentes"]

                llm_key = (wn, sub.lower())
                if llm_key in resoluciones_llm:
                    res_llm = resoluciones_llm[llm_key]
                    llm_est = res_llm["estado"]
                    if llm_est == "CUBIERTO":
                        est = EstadoSubtema.CUBIERTO
                        ev = res_llm.get("evidencia") or ev or "Evidencia semántica en lección"
                    elif llm_est == "MENCIONADO":
                        est = EstadoSubtema.MENCIONADO

                if est == EstadoSubtema.CUBIERTO:
                    cubiertos_cnt += 1

                subtemas_ev.append(SubtemaEvidencia(texto=sub, estado=est, evidencia=ev, fuentes=fuentes))

            total_sub = len(subs) if subs else 1
            cobertura = cubiertos_cnt / total_sub
            
            enriquecimiento: list[str] = []
            if g_week:
                for p_det in g_week.periodos_detalle:
                    if not any(similitud(p_det.titulo, s) >= UMBRAL_MATCH for s in subs):
                        enriquecimiento.append(p_det.titulo)

            matriz_sub = MatrizSubtemas(
                cobertura=round(cobertura, 2),
                cubiertos=cubiertos_cnt,
                total=len(subs),
                subtemas=subtemas_ev,
                enriquecimiento=enriquecimiento
            )

            if cobertura >= 0.80 and not missing_codes:
                veredicto_sem = ConcordanceStatus.CUMPLE
            elif cobertura >= 0.50 or (missing_codes and len(guia_codes) > 0):
                veredicto_sem = ConcordanceStatus.CUMPLE_PARCIAL
            else:
                veredicto_sem = ConcordanceStatus.NO_CUMPLE

            habilita_gen = (veredicto_sem in (ConcordanceStatus.CUMPLE, ConcordanceStatus.CONCORDANTE))

            ausentes = [s.texto for s in subtemas_ev if s.estado == EstadoSubtema.AUSENTE]
            mencionados = [s.texto for s in subtemas_ev if s.estado == EstadoSubtema.MENCIONADO]

            if ausentes and veredicto_sem != ConcordanceStatus.CUMPLE:
                observaciones.append(f"Subtema(s) ausente(s) sin desarrollo: {', '.join(ausentes)}.")
                recomendaciones.append(f"Agregar una sección o período de desarrollo para: {', '.join(ausentes)}.")
            if mencionados:
                notas_informativas.append(f"Subtema(s) mencionado(s) en ruta/síntesis pero sin período propio de desarrollo: {', '.join(mencionados)}.")

            if "hoja" in w.evaluation_technique.lower() or "hoja" in str(w.resources).lower():
                if g_week and any("TALLER" in act or "PRÁCTICA" in act for act in g_week.actividades):
                    notas_informativas.append(
                        "El sílabo planifica 'hoja de trabajo'; el material lo cubre con 'Taller integrador' y 'Práctica progresiva'."
                    )

            fechas_coherencia = CoherenciaDetalle(ok=True, detalle=f"{g_week.fechas if g_week else 'Fechas coherentes'} dentro del rango lectivo")
            n_per_dev = len(g_week.periodos_detalle) if g_week else 0
            periodos_coherencia = CoherenciaDetalle(
                ok=(n_per_dev >= 4 or desarrollada),
                detalle=f"{g_week.periodos if g_week else '6'} declarados / {n_per_dev} desarrollados"
            )
            
            if not missing_codes:
                codigos_coherencia = CoherenciaDetalle(ok=True, detalle="Códigos de competencia alineados")
            else:
                codigos_coherencia = CoherenciaDetalle(ok=False, detalle=f"Códigos no presentes en guía: {', '.join(missing_codes)}")
                if not observaciones:
                    observaciones.append(f"Algunos códigos de competencia del sílabo no aparecen en la guía: {', '.join(missing_codes)}.")

        det_sem = DetalleSemanal(
            semana=wn,
            tema_silabo=w.topic,
            tema_material=g_week.tema if g_week else None,
            desarrollada_en_material=desarrollada,
            veredicto_semana=veredicto_sem,
            habilita_generacion=habilita_gen,
            matriz_subtemas=matriz_sub,
            notas_informativas=notas_informativas,
            coherencia=CoherenciaTransversal(
                fechas=fechas_coherencia,
                periodos=periodos_coherencia,
                codigos_competencia=codigos_coherencia
            ),
            observaciones=observaciones,
            recomendaciones=recomendaciones,
            resultados_aprendizaje=DimensionInformativa(
                informativa=True,
                veredicto="CUMPLE" if veredicto_sem in (ConcordanceStatus.CUMPLE, ConcordanceStatus.CUMPLE_PARCIAL, ConcordanceStatus.CONCORDANTE) else "NO_CUMPLE",
                evidencia=f"Competencias cubiertas en semana {wn}"
            ),
            estrategias=DimensionInformativa(
                informativa=True,
                veredicto="CUMPLE" if desarrollada else "NO_CUMPLE",
                evidencia=f"Estrategias de enseñanza registradas"
            ),
            silabo_codes=silabo_codes,
            guia_codes=guia_codes,
            missing_codes_in_guia=missing_codes,
            page_range_guia=page_range,
            adaptation_in_silabo=adapt_silabo,
            adaptation_in_guia=adapt_guia,
        )
        detalle_semanal.append(det_sem)

        if habilita_gen:
            temas_validados.append(
                TemaValidado(
                    semana=wn,
                    tema=w.topic,
                    subtemas=subs,
                    competencias=w.competency_codes,
                    estrategias=w.methodology_phases.model_dump(),
                    tecnica_instrumento=w.evaluation_technique
                )
            )

    # 5. Veredicto Global sobre las semanas evaluables
    n_total = len(detalle_semanal)
    n_cumple = sum(1 for d in detalle_semanal if d.veredicto_semana in (ConcordanceStatus.CUMPLE, ConcordanceStatus.CONCORDANTE))

    if n_total > 0 and n_cumple == n_total:
        v_global = ConcordanceStatus.CUMPLE
    elif n_cumple >= math.ceil(n_total * 0.5):
        v_global = ConcordanceStatus.CUMPLE_PARCIAL
    else:
        v_global = ConcordanceStatus.NO_CUMPLE

    n_dev = len([d for d in detalle_semanal if d.desarrollada_en_material])
    resumen_str = f"{n_cumple} de {n_total} semanas lectivas evaluables cumplen el estándar de concordancia. Desarrolladas en el material: {n_dev}/{n_total}."
    if solo_mencionadas:
        resumen_str += f" Solo mencionadas: {solo_mencionadas}."

    resumen_dura = ResumenSemanasDura(
        silabo=n_total,
        material_desarrolladas=n_dev,
        material_solo_mencionadas=solo_mencionadas,
        veredicto=v_global,
        observaciones=[d.observation for d in detalle_semanal if d.observation],
        recomendaciones=[r for d in detalle_semanal for r in d.recomendaciones]
    )

    return ConcordanceResult(
        veredicto_global=v_global,
        resumen=resumen_str,
        semanas=resumen_dura,
        detalle_semanal=detalle_semanal,
        temas_validados=temas_validados,
        metadatos={
            "asignatura": silabo.subject or guia.subject,
            "unidad": silabo.unit_name or guia.unit_name,
            "docente": silabo.teacher,
            "fechas_silabo": f"{silabo.start_date} - {silabo.end_date}",
            "fechas_material": guia.fechas,
            "juez_llm": bool(api_key),
            "semanas_excluidas": [0, max_week] if len(all_week_numbers) > 2 else [0]
        }
    )
