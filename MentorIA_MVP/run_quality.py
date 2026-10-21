"""Ejecuta el plan de pruebas y genera el reporte de calidad del MVP.

    python run_quality.py

Salida: reports/reporte_calidad.json y reports/reporte_calidad.md
"""
import json
import platform
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from tests import test_mentoria  # noqa: E402

CRITERIOS = [
    ("RF-01", "Sílabos de los 2 cursos piloto indexados", "100 %",
     lambda m: m["fragmentos_indexados"] / m["temas_en_silabos"], lambda v: v >= 1.0, "{:.0%}"),
    ("RF-02", "Recuperación del tema correcto (top 3)", "≥ 90 %",
     lambda m: m["recuperacion_top3"], lambda v: v >= 0.90, "{:.1%}"),
    ("RF-03", "Rechazo de preguntas fuera del sílabo", "100 %",
     lambda m: m["rechazo_fuera_silabo"], lambda v: v >= 1.0, "{:.0%}"),
    ("RNF-01", "Tiempo de respuesta promedio del chatbot", "< 5 s",
     lambda m: m["tiempo_respuesta"]["promedio_ms"], lambda v: v < 5000, "{:.0f} ms"),
    ("RNF-02", "Sensibilidad del modelo de alertas", "≥ 70 %",
     lambda m: m["alertas"]["sensibilidad"], lambda v: v >= 0.70, "{:.1%}"),
]


class Registro(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.casos = []
        self._t0 = {}

    def startTest(self, test):
        self._t0[test.id()] = time.perf_counter()
        super().startTest(test)

    def _guardar(self, test, resultado, detalle=""):
        doc = (test._testMethodDoc or "").strip()
        partes = [p.strip() for p in doc.split("|")]
        self.casos.append({
            "codigo": partes[0] if len(partes) > 2 else test.id(),
            "requerimiento": partes[1] if len(partes) > 2 else "",
            "descripcion": partes[2] if len(partes) > 2 else doc,
            "resultado": resultado, "detalle": detalle,
            "ms": round((time.perf_counter() - self._t0.get(test.id(), time.perf_counter())) * 1000, 1),
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._guardar(test, "Aprobado")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._guardar(test, "Fallido", str(err[1]))

    def addError(self, test, err):
        super().addError(test, err)
        self._guardar(test, "Error", str(err[1]))


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_mentoria)
    runner = unittest.TextTestRunner(resultclass=Registro, verbosity=1)
    inicio = time.perf_counter()
    res = runner.run(suite)
    duracion = time.perf_counter() - inicio
    casos = sorted(res.casos, key=lambda c: c["codigo"])
    m = test_mentoria.METRICAS
    criterios = []
    for codigo, nombre, meta, valor, cumple, fmt in CRITERIOS:
        try:
            v = valor(m)
            criterios.append({"requerimiento": codigo, "criterio": nombre, "meta": meta,
                              "valor": v, "valor_texto": fmt.format(v), "cumple": bool(cumple(v))})
        except (KeyError, ZeroDivisionError):
            criterios.append({"requerimiento": codigo, "criterio": nombre, "meta": meta,
                              "valor": None, "valor_texto": "sin medir", "cumple": False})
    reporte = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "entorno": f"Python {platform.python_version()} · {platform.system()} {platform.release()}",
        "total": res.testsRun, "aprobados": sum(c["resultado"] == "Aprobado" for c in casos),
        "fallidos": len(res.failures), "errores": len(res.errors), "duracion_s": round(duracion, 2),
        "casos": casos, "metricas": m, "criterios": criterios,
    }
    (BASE / "reports").mkdir(exist_ok=True)
    (BASE / "reports" / "reporte_calidad.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2),
                                                           encoding="utf-8")
    lineas = [f"# Reporte de calidad – MentorIA MVP", "",
              f"Fecha: {reporte['fecha']} · Entorno: {reporte['entorno']}", "",
              f"**{reporte['aprobados']} de {reporte['total']} casos aprobados** en {reporte['duracion_s']} s.", "",
              "## Criterios de aceptación", "", "| Req. | Criterio | Meta | Resultado | Cumple |", "|---|---|---|---|---|"]
    lineas += [f"| {c['requerimiento']} | {c['criterio']} | {c['meta']} | {c['valor_texto']} | {'Sí' if c['cumple'] else 'No'} |"
               for c in criterios]
    lineas += ["", "## Casos de prueba", "", "| Caso | Req. | Descripción | Resultado |", "|---|---|---|---|"]
    lineas += [f"| {c['codigo']} | {c['requerimiento']} | {c['descripcion']} | {c['resultado']} |" for c in casos]
    (BASE / "reports" / "reporte_calidad.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"\nReporte generado en reports/: {reporte['aprobados']}/{reporte['total']} aprobados.")
    for c in criterios:
        print(f"  {c['requerimiento']:7} {c['criterio']:45} {c['valor_texto']:>10}  {'OK' if c['cumple'] else 'NO CUMPLE'}")
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
