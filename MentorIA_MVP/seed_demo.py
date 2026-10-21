"""Carga datos de demostración para la exposición: consultas de estudiantes
simulados al chatbot y un plan de estudio con avance para E001.

    python seed_demo.py          (borra la base local y la vuelve a llenar)
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from mentoria import planes
from mentoria.cargas import DIR_CARGAS
from mentoria.db import DB_PATH
from mentoria.server import MentorIA

BASE = Path(__file__).resolve().parent


def main():
    try:
        if DB_PATH.exists():
            DB_PATH.unlink()
    except PermissionError:
        raise SystemExit("MentorIA está abierto. Ciérrelo con Ctrl+C en su ventana y vuelva a ejecutar seed_demo.py.")
    for archivo in DIR_CARGAS.glob("notas_*.csv"):  # vuelve a los datos simulados
        archivo.unlink()
    app = MentorIA()
    rnd = random.Random(7)
    preguntas = json.loads((BASE / "tests" / "preguntas_referencia.json").read_text(encoding="utf-8"))
    banco = {"GPC": [], "IHC": []}
    for p in preguntas["en_silabo"]:
        banco[p["curso"]].append(p["pregunta"])
    # Los temas de valor ganado y ruta crítica concentran más dudas en GPC, y SUS/heurísticas en IHC.
    pesos_extra = {"CPI": 6, "EAC": 4, "ruta crítica": 5, "holgura": 3, "valor ganado": 4,
                   "SUS": 5, "Nielsen": 4, "WCAG": 3}
    total = 0
    for curso in ("GPC", "IHC"):
        estudiantes = [r["codigo"] for r in app.dataset if r["curso"] == curso][:18]
        lista = []
        for q in banco[curso]:
            peso = 1 + sum(v for k, v in pesos_extra.items() if k.lower() in q.lower())
            lista += [q] * peso
        for _ in range(70):
            app.chat(rnd.choice(estudiantes), curso, rnd.choice(lista))
            total += 1
        for p in preguntas["fuera_de_silabo"]:
            if p["curso"] == curso:
                app.chat(rnd.choice(estudiantes), curso, p["pregunta"])
                total += 1
    # Plan de E001 con tareas completadas en 3 días seguidos (muestra la racha y las insignias).
    plan = app.crear_plan({"estudiante": "E001", "curso": "GPC", "horas_semana": 4, "semanas": 3,
                           "unidades_debiles": ["Unidad 5: Gestión de los costos y valor ganado",
                                                "Unidad 4: Gestión del cronograma"]})
    hoy = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
    for i, tarea in enumerate(plan["tareas"][:5]):
        planes.completar_tarea(app.con, tarea["id"], "E001", cuando=hoy - timedelta(days=max(0, 2 - i // 2)))
    for q in ["¿Cómo se calcula el CPI?", "¿Qué es la ruta crítica de un proyecto?", "Fórmula PERT"]:
        app.chat("E001", "GPC", q)
        total += 1
    print(f"Datos de demostración cargados: {total} consultas, plan de E001 con 5 tareas completadas.")
    print(json.dumps(app.logros("E001"), ensure_ascii=False, indent=1)[:400])


if __name__ == "__main__":
    main()
