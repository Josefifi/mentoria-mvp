"""Módulo 4 – Tablero docente (EDT 1.3.5).

Agrega las consultas al chatbot por tema para mostrar al docente dónde se
concentran las dudas de sus estudiantes. Solo muestra datos agregados y códigos
anonimizados, nunca el contenido asociado a una persona identificable.
"""


def metricas_curso(con, indice, modelo, dataset, curso):
    temas = [(f["unidad"], f["tema"]) for f in indice.fragmentos if f["curso"] == curso]
    filas = con.execute("""SELECT unidad, tema, COUNT(*) n, COUNT(DISTINCT estudiante) est,
                                  AVG(confianza) conf, AVG(ms) ms
                           FROM consultas WHERE curso=? AND en_silabo=1
                           GROUP BY unidad, tema""", (curso,)).fetchall()
    por_tema = {(r["unidad"], r["tema"]): r for r in filas}
    total = sum(r["n"] for r in filas)
    detalle = []
    for unidad, tema in temas:
        r = por_tema.get((unidad, tema))
        n = r["n"] if r else 0
        detalle.append({
            "unidad": unidad, "tema": tema, "consultas": n,
            "estudiantes": r["est"] if r else 0,
            "porcentaje": round(100 * n / total, 1) if total else 0.0,
            "confianza_promedio": round(r["conf"], 3) if r else None,
        })
    detalle.sort(key=lambda d: d["consultas"], reverse=True)
    resumen = con.execute("""SELECT COUNT(*) n, COUNT(DISTINCT estudiante) est, AVG(ms) ms,
                                    SUM(CASE WHEN en_silabo=0 THEN 1 ELSE 0 END) fuera
                             FROM consultas WHERE curso=?""", (curso,)).fetchone()
    recientes = [dict(r) for r in con.execute(
        "SELECT pregunta, tema, fecha FROM consultas WHERE curso=? AND en_silabo=1 ORDER BY id DESC LIMIT 8", (curso,))]
    alertas = alertas_curso(modelo, dataset, curso)
    return {
        "curso": curso,
        "total_consultas": resumen["n"] or 0,
        "estudiantes_activos": resumen["est"] or 0,
        "tiempo_respuesta_ms": round(resumen["ms"] or 0, 2),
        "consultas_fuera_de_silabo": resumen["fuera"] or 0,
        "temas": detalle,
        "temas_criticos": [d for d in detalle if d["consultas"]][:3],
        "consultas_recientes": recientes,
        "alertas": {"alto": sum(a["nivel"] == "alto" for a in alertas),
                    "medio": sum(a["nivel"] == "medio" for a in alertas),
                    "bajo": sum(a["nivel"] == "bajo" for a in alertas)},
    }


def alertas_curso(modelo, dataset, curso):
    from .alertas import evaluar_estudiante
    lista = [evaluar_estudiante(modelo, r) for r in dataset if r["curso"] == curso]
    lista.sort(key=lambda a: a["probabilidad"], reverse=True)
    return lista
