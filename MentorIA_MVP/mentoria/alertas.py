"""Módulo 3 – Alertas tempranas de riesgo (EDT 1.3.4) y datos simulados (EDT 1.5.1).

Los datos son sintéticos y anonimizados (Ley N.° 29733): cada estudiante se
identifica solo con un código correlativo (E001, E002, ...), sin nombres, DNI ni
correos. El modelo es una regresión logística entrenada por descenso de
gradiente, sin librerías externas, que estima la probabilidad de desaprobar a
partir de dos notas parciales, la asistencia y el porcentaje de tareas entregadas.
"""
import csv
import json
import math
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATASET_PATH = DATA_DIR / "estudiantes_simulados.csv"
MODELO_PATH = DATA_DIR / "modelo_alertas.json"

VARIABLES = ["nota_pc1", "nota_pc2", "asistencia", "tareas"]
COLUMNAS = ["codigo", "curso"] + VARIABLES + ["desaprobo"]
UMBRAL_ALERTA = 0.40   # elegido para priorizar la sensibilidad (meta del acta: >= 70 %)
SEMILLA = 2026


def generar_dataset(n=240, semilla=SEMILLA, ruta=DATASET_PATH):
    """Genera notas y asistencia simuladas para los 2 cursos piloto."""
    rnd = random.Random(semilla)
    filas = []
    for i in range(n):
        curso = "GPC" if i % 2 == 0 else "IHC"
        habilidad = rnd.gauss(0, 1)             # factor latente del estudiante
        compromiso = rnd.gauss(0, 1)
        pc1 = min(20, max(0, 12 + 3.2 * habilidad + rnd.gauss(0, 2)))
        pc2 = min(20, max(0, 12 + 3.0 * habilidad + 1.0 * compromiso + rnd.gauss(0, 2)))
        asistencia = min(100, max(30, 85 + 9 * compromiso + rnd.gauss(0, 6)))
        tareas = min(100, max(0, 78 + 14 * compromiso + 5 * habilidad + rnd.gauss(0, 10)))
        final = 0.3 * pc1 + 0.35 * pc2 + 0.04 * asistencia + 0.03 * tareas - 1.9 + rnd.gauss(0, 1.6)
        filas.append({
            "codigo": f"E{i + 1:03d}", "curso": curso,
            "nota_pc1": round(pc1, 1), "nota_pc2": round(pc2, 1),
            "asistencia": round(asistencia), "tareas": round(tareas),
            "desaprobo": int(final < 10.5),
        })
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    return filas


def cargar_dataset(ruta=DATASET_PATH):
    if not Path(ruta).exists():
        generar_dataset(ruta=ruta)
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        for v in VARIABLES:
            r[v] = float(r[v])
        r["desaprobo"] = int(r["desaprobo"])
    return filas


def _escalar(x):
    # notas sobre 20 y porcentajes sobre 100 llevados a [0, 1]
    return [x[0] / 20, x[1] / 20, x[2] / 100, x[3] / 100]


def _sigmoide(z):
    return 1 / (1 + math.exp(-max(-30, min(30, z))))


class ModeloRiesgo:
    def __init__(self, pesos=None, sesgo=0.0, umbral=UMBRAL_ALERTA, metricas=None):
        self.pesos = pesos or [0.0] * len(VARIABLES)
        self.sesgo = sesgo
        self.umbral = umbral
        self.metricas = metricas or {}

    def probabilidad(self, registro):
        x = _escalar([float(registro[v]) for v in VARIABLES])
        return _sigmoide(self.sesgo + sum(w * xi for w, xi in zip(self.pesos, x)))

    def entrenar(self, filas, epocas=4000, tasa=1.5):
        X = [_escalar([r[v] for v in VARIABLES]) for r in filas]
        y = [r["desaprobo"] for r in filas]
        n = len(X)
        for _ in range(epocas):
            grad_w = [0.0] * len(self.pesos)
            grad_b = 0.0
            for xi, yi in zip(X, y):
                error = _sigmoide(self.sesgo + sum(w * v for w, v in zip(self.pesos, xi))) - yi
                grad_b += error
                for j, v in enumerate(xi):
                    grad_w[j] += error * v
            self.sesgo -= tasa * grad_b / n
            self.pesos = [w - tasa * g / n for w, g in zip(self.pesos, grad_w)]
        return self

    def evaluar(self, filas):
        vp = fp = vn = fn = 0
        for r in filas:
            pred = self.probabilidad(r) >= self.umbral
            real = r["desaprobo"] == 1
            vp += pred and real
            fp += pred and not real
            vn += (not pred) and (not real)
            fn += (not pred) and real
        total = vp + fp + vn + fn
        return {
            "verdaderos_positivos": vp, "falsos_positivos": fp,
            "verdaderos_negativos": vn, "falsos_negativos": fn,
            "sensibilidad": round(vp / (vp + fn), 4) if vp + fn else 0.0,
            "precision": round(vp / (vp + fp), 4) if vp + fp else 0.0,
            "exactitud": round((vp + vn) / total, 4) if total else 0.0,
            "n_prueba": total,
        }

    def nivel(self, p):
        if p >= 0.60:
            return "alto"
        if p >= self.umbral:
            return "medio"
        return "bajo"

    def guardar(self, ruta=MODELO_PATH):
        Path(ruta).write_text(json.dumps({"pesos": self.pesos, "sesgo": self.sesgo, "umbral": self.umbral,
                                          "variables": VARIABLES, "metricas": self.metricas}, indent=2),
                              encoding="utf-8")

    @classmethod
    def cargar(cls, ruta=MODELO_PATH):
        if not Path(ruta).exists():
            return entrenar_y_guardar()
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return cls(d["pesos"], d["sesgo"], d["umbral"], d.get("metricas"))


def dividir(filas, proporcion=0.7, semilla=SEMILLA):
    idx = list(range(len(filas)))
    random.Random(semilla).shuffle(idx)
    corte = int(len(idx) * proporcion)
    return [filas[i] for i in idx[:corte]], [filas[i] for i in idx[corte:]]


def entrenar_y_guardar():
    filas = cargar_dataset()
    entrenamiento, prueba = dividir(filas)
    modelo = ModeloRiesgo().entrenar(entrenamiento)
    modelo.metricas = modelo.evaluar(prueba)
    modelo.guardar()
    return modelo


def recomendaciones(registro, p):
    recs = []
    if registro["asistencia"] < 75:
        recs.append("Tu asistencia está por debajo de 75 %: prioriza asistir a las próximas sesiones.")
    if registro["tareas"] < 70:
        recs.append("Tienes tareas pendientes: entrégalas para no perder puntaje.")
    if min(registro["nota_pc1"], registro["nota_pc2"]) < 11:
        recs.append("Refuerza los temas de la práctica con nota más baja con un plan de estudio en MentorIA.")
    if p >= UMBRAL_ALERTA and not recs:
        recs.append("Agenda una consulta con tu docente para revisar tu avance.")
    return recs or ["Vas bien. Mantén tu ritmo de estudio."]


def evaluar_estudiante(modelo, registro):
    p = modelo.probabilidad(registro)
    return {
        "codigo": registro["codigo"], "curso": registro["curso"],
        "probabilidad": round(p, 3), "nivel": modelo.nivel(p), "alerta": p >= modelo.umbral,
        "variables": {v: registro[v] for v in VARIABLES},
        "recomendaciones": recomendaciones(registro, p),
    }
