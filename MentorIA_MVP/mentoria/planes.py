"""Módulo 2 – Planes de estudio personalizados con gamificación (EDT 1.3.3).

El plan reparte las horas semanales disponibles entre los temas del sílabo.
Las unidades que el estudiante marca como débiles reciben el doble de peso.
La gamificación se limita a lo aprobado en el alcance: puntos, rachas e insignias.
"""
from datetime import date, datetime, timedelta

PUNTOS_POR_TAREA = 10
ACTIVIDADES = [
    "Leer el tema en el sílabo y resumirlo en 5 líneas",
    "Resolver 3 preguntas de práctica con el chatbot",
    "Autoevaluación: explicar el tema sin mirar los apuntes",
]

INSIGNIAS = {
    "primer_paso": "Primer paso – completaste tu primera tarea",
    "racha_3": "Racha de 3 días estudiando",
    "racha_7": "Constancia – 7 días seguidos",
    "explorador": "Explorador – 5 preguntas al chatbot",
    "unidad_dominada": "Unidad dominada – todas las tareas de una unidad",
    "plan_completo": "Plan completo",
}


def generar_plan(con, indice, estudiante, curso, horas_semana, semanas, unidades_debiles=()):
    if not 1 <= horas_semana <= 20:
        raise ValueError("Las horas por semana deben estar entre 1 y 20.")
    if not 1 <= semanas <= 16:
        raise ValueError("Las semanas deben estar entre 1 y 16.")
    temas = [(f["unidad"], f["tema"]) for f in indice.fragmentos
             if f["curso"] == curso and not f["unidad"].startswith("Evaluación")]
    if not temas:
        raise ValueError(f"El curso {curso} no tiene sílabo indexado.")
    debiles = set(unidades_debiles)
    pesos = [2 if u in debiles else 1 for u, _ in temas]
    minutos_totales = int(horas_semana * 60 * semanas)
    sesiones = []
    for (unidad, tema), peso in zip(temas, pesos):
        repeticiones = 2 if peso == 2 else 1
        for r in range(repeticiones):
            sesiones.append((peso, unidad, tema, ACTIVIDADES[r % len(ACTIVIDADES)]))
    # Primero las unidades débiles, luego el orden del sílabo.
    sesiones.sort(key=lambda s: -s[0])
    peso_total = sum(s[0] for s in sesiones)
    cur = con.execute("INSERT INTO planes (estudiante, curso, horas_semana, semanas) VALUES (?,?,?,?)",
                      (estudiante, curso, horas_semana, semanas))
    plan_id = cur.lastrowid
    minutos_semana = horas_semana * 60
    acumulado, semana = 0, 1
    for peso, unidad, tema, actividad in sesiones:
        minutos = max(20, int(round(minutos_totales * peso / peso_total / 5.0)) * 5)
        if acumulado + minutos > minutos_semana and semana < semanas:
            semana += 1
            acumulado = 0
        acumulado += minutos
        con.execute("INSERT INTO tareas (plan_id, semana, unidad, tema, actividad, minutos) VALUES (?,?,?,?,?,?)",
                    (plan_id, semana, unidad, tema, actividad, minutos))
    con.commit()
    return obtener_plan(con, plan_id)


def obtener_plan(con, plan_id):
    plan = con.execute("SELECT * FROM planes WHERE id=?", (plan_id,)).fetchone()
    if not plan:
        return None
    tareas = [dict(t) for t in con.execute("SELECT * FROM tareas WHERE plan_id=? ORDER BY semana, id", (plan_id,))]
    hechas = sum(t["completada"] for t in tareas)
    return {**dict(plan), "tareas": tareas, "avance": round(100 * hechas / len(tareas), 1) if tareas else 0.0}


def plan_vigente(con, estudiante, curso):
    fila = con.execute("SELECT id FROM planes WHERE estudiante=? AND curso=? ORDER BY id DESC LIMIT 1",
                       (estudiante, curso)).fetchone()
    return obtener_plan(con, fila["id"]) if fila else None


def completar_tarea(con, tarea_id, estudiante, cuando=None):
    t = con.execute("SELECT t.*, p.estudiante FROM tareas t JOIN planes p ON p.id=t.plan_id WHERE t.id=?",
                    (tarea_id,)).fetchone()
    if not t or t["estudiante"] != estudiante:
        raise ValueError("La tarea no existe o no pertenece al estudiante.")
    if not t["completada"]:
        marca = (cuando or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        con.execute("UPDATE tareas SET completada=1, completada_en=? WHERE id=?", (marca, tarea_id))
        con.commit()
    return gamificacion(con, estudiante)


def _racha(dias):
    """Días consecutivos con al menos una tarea, contando hacia atrás desde el último día activo."""
    if not dias:
        return 0
    ordenados = sorted(dias, reverse=True)
    racha, previo = 1, ordenados[0]
    for d in ordenados[1:]:
        if previo - d == timedelta(days=1):
            racha += 1
            previo = d
        else:
            break
    return racha


def gamificacion(con, estudiante):
    filas = con.execute("""SELECT t.*, p.curso FROM tareas t JOIN planes p ON p.id=t.plan_id
                           WHERE p.estudiante=?""", (estudiante,)).fetchall()
    hechas = [f for f in filas if f["completada"]]
    dias = {date.fromisoformat(f["completada_en"][:10]) for f in hechas}
    racha = _racha(dias)
    preguntas = con.execute("SELECT COUNT(*) FROM consultas WHERE estudiante=?", (estudiante,)).fetchone()[0]
    nuevas = set()
    if hechas:
        nuevas.add("primer_paso")
    if racha >= 3:
        nuevas.add("racha_3")
    if racha >= 7:
        nuevas.add("racha_7")
    if preguntas >= 5:
        nuevas.add("explorador")
    por_unidad = {}
    for f in filas:
        por_unidad.setdefault((f["plan_id"], f["unidad"]), []).append(f["completada"])
    if any(all(v) for v in por_unidad.values()):
        nuevas.add("unidad_dominada")
    por_plan = {}
    for f in filas:
        por_plan.setdefault(f["plan_id"], []).append(f["completada"])
    if any(all(v) for v in por_plan.values()):
        nuevas.add("plan_completo")
    for ins in nuevas:
        con.execute("INSERT OR IGNORE INTO logros (estudiante, insignia) VALUES (?,?)", (estudiante, ins))
    con.commit()
    obtenidas = [r["insignia"] for r in con.execute("SELECT insignia FROM logros WHERE estudiante=? ORDER BY obtenida",
                                                     (estudiante,))]
    return {
        "estudiante": estudiante,
        "puntos": PUNTOS_POR_TAREA * len(hechas) + 2 * preguntas,
        "tareas_completadas": len(hechas),
        "tareas_totales": len(filas),
        "racha_dias": racha,
        "preguntas_chatbot": preguntas,
        "insignias": [{"id": i, "descripcion": INSIGNIAS[i]} for i in obtenidas],
        "insignias_pendientes": [{"id": i, "descripcion": d} for i, d in INSIGNIAS.items() if i not in obtenidas],
    }
