"""Casos de prueba del MVP (EDT 1.4.1 y 1.4.2).

Cada prueba lleva en su docstring el código del caso (CP-xx) y el requerimiento
que verifica (RF = funcional, RNF = no funcional). run_quality.py usa esa
información para armar el reporte de calidad.
"""
import csv
import json
import re
import statistics
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from mentoria import alertas, planes, rag
from mentoria.server import MentorIA, crear_handler
from http.server import ThreadingHTTPServer

BASE = Path(__file__).resolve().parent.parent
REFERENCIA = json.loads((BASE / "tests" / "preguntas_referencia.json").read_text(encoding="utf-8"))
METRICAS = {}  # métricas medidas por las pruebas; run_quality.py las publica en el reporte


def nueva_app():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return MentorIA(ruta_db=tmp.name, dir_cargas=tempfile.mkdtemp())


class PruebasChatbot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = nueva_app()
        cls.indice = cls.app.indice

    def test_cp01_indexacion_completa(self):
        """CP-01 | RF-01 | El 100 % de los temas de los sílabos de los 2 cursos piloto queda indexado."""
        esperados = 0
        for ruta in (BASE / "data" / "silabos").glob("*.md"):
            esperados += len(re.findall(r"^## ", ruta.read_text(encoding="utf-8"), re.M))
        cursos = {f["curso"] for f in self.indice.fragmentos}
        METRICAS["fragmentos_indexados"] = len(self.indice.fragmentos)
        METRICAS["temas_en_silabos"] = esperados
        self.assertEqual(len(self.indice.fragmentos), esperados)
        self.assertEqual(cursos, {"GPC", "IHC"})

    def test_cp02_respuesta_con_fuente(self):
        """CP-02 | RF-02 | La respuesta usa el fragmento pertinente del sílabo y cita curso, unidad y tema."""
        r = rag.responder(self.indice, "¿Cómo se calcula el CPI?", "GPC")
        self.assertTrue(r["en_silabo"])
        self.assertIn("CPI = EV / AC", r["respuesta"])
        self.assertIn("Fuente: sílabo de Gestión de Proyectos de Computación", r["respuesta"])
        self.assertEqual(r["tema"], "Índices de desempeño y pronósticos")

    def test_cp03_precision_recuperacion(self):
        """CP-03 | RF-02 | El tema correcto aparece entre los 3 primeros fragmentos en al menos el 90 % del conjunto de referencia."""
        top1 = top3 = 0
        for p in REFERENCIA["en_silabo"]:
            temas = [f["tema"] for _, f in self.indice.buscar(p["pregunta"], p["curso"])]
            top1 += bool(temas) and temas[0] == p["tema"]
            top3 += p["tema"] in temas
        n = len(REFERENCIA["en_silabo"])
        METRICAS["recuperacion_top1"] = round(top1 / n, 4)
        METRICAS["recuperacion_top3"] = round(top3 / n, 4)
        METRICAS["preguntas_referencia"] = n
        self.assertGreaterEqual(top3 / n, 0.90)

    def test_cp04_rechazo_fuera_de_silabo(self):
        """CP-04 | RF-03 | Las preguntas ajenas al sílabo se rechazan sin inventar respuesta (riesgo R1)."""
        rechazadas = 0
        for p in REFERENCIA["fuera_de_silabo"]:
            r = rag.responder(self.indice, p["pregunta"], p["curso"])
            rechazadas += (not r["en_silabo"]) and not r["fuentes"]
        METRICAS["rechazo_fuera_silabo"] = round(rechazadas / len(REFERENCIA["fuera_de_silabo"]), 4)
        self.assertEqual(rechazadas, len(REFERENCIA["fuera_de_silabo"]))

    def test_cp05_registro_de_consultas(self):
        """CP-05 | RF-04 | Cada consulta queda registrada con su tema para alimentar el tablero docente."""
        antes = self.app.con.execute("SELECT COUNT(*) FROM consultas").fetchone()[0]
        self.app.chat("E002", "GPC", "¿Qué es la holgura total?")
        fila = self.app.con.execute("SELECT * FROM consultas ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(self.app.con.execute("SELECT COUNT(*) FROM consultas").fetchone()[0], antes + 1)
        self.assertEqual(fila["tema"], "Ruta crítica y holgura")
        self.assertEqual(fila["estudiante"], "E002")


class PruebasPlanes(unittest.TestCase):
    def setUp(self):
        self.app = nueva_app()

    def test_cp06_plan_personalizado(self):
        """CP-06 | RF-05 | Se genera un plan para un estudiante de prueba en cada curso piloto, priorizando las unidades débiles."""
        for curso, est in (("GPC", "E001"), ("IHC", "E002")):
            unidades = [u for u in self.app.indice.cursos()[0 if curso == "GPC" else 1]["unidades"]
                        if not u.startswith("Evaluación")]
            debil = unidades[3]
            plan = self.app.crear_plan({"estudiante": est, "curso": curso, "horas_semana": 4, "semanas": 3,
                                        "unidades_debiles": [debil]})
            self.assertTrue(plan["tareas"])
            self.assertEqual(plan["tareas"][0]["unidad"], debil)
            por_semana = {}
            for t in plan["tareas"]:
                por_semana[t["semana"]] = por_semana.get(t["semana"], 0) + t["minutos"]
            for s, m in por_semana.items():
                if s < plan["semanas"]:
                    self.assertLessEqual(m, 4 * 60)
            total = sum(por_semana.values())
            self.assertLessEqual(total, 4 * 60 * 3 * 1.10)
            temas_debiles = [t for t in plan["tareas"] if t["unidad"] == debil]
            temas_unicos = {t["tema"] for t in temas_debiles}
            self.assertEqual(len(temas_debiles), 2 * len(temas_unicos))

    def test_cp07_validacion_entradas_plan(self):
        """CP-07 | RF-05 | El plan rechaza horas o semanas fuera de rango."""
        with self.assertRaises(ValueError):
            self.app.crear_plan({"estudiante": "E001", "curso": "GPC", "horas_semana": 0, "semanas": 3})
        with self.assertRaises(ValueError):
            self.app.crear_plan({"estudiante": "E001", "curso": "GPC", "horas_semana": 4, "semanas": 30})

    def test_cp08_gamificacion(self):
        """CP-08 | RF-06 | Completar tareas otorga puntos, calcula la racha de días e insignias."""
        plan = self.app.crear_plan({"estudiante": "E003", "curso": "GPC", "horas_semana": 3, "semanas": 2})
        base = datetime(2026, 10, 14, 20, 0)
        for i in range(3):
            g = planes.completar_tarea(self.app.con, plan["tareas"][i]["id"], "E003", cuando=base + timedelta(days=i))
        self.assertEqual(g["puntos"], 3 * planes.PUNTOS_POR_TAREA)
        self.assertEqual(g["racha_dias"], 3)
        ids = {i["id"] for i in g["insignias"]}
        self.assertTrue({"primer_paso", "racha_3"} <= ids)
        # completar dos veces la misma tarea no suma puntos dobles
        g2 = planes.completar_tarea(self.app.con, plan["tareas"][0]["id"], "E003")
        self.assertEqual(g2["puntos"], g["puntos"])
        with self.assertRaises(ValueError):
            planes.completar_tarea(self.app.con, plan["tareas"][0]["id"], "E004")
        # preguntas: solo suman las respondidas con el sílabo y como máximo 5 por día
        for _ in range(7):
            self.app.chat("E003", "GPC", "¿Qué es la ruta crítica?")
        self.app.chat("E003", "GPC", "¿Quién ganó el mundial 2022?")
        g3 = planes.gamificacion(self.app.con, "E003")
        self.assertEqual(g3["preguntas_chatbot"], 7)
        self.assertEqual(g3["puntos"], g["puntos"] + planes.TOPE_PREGUNTAS_DIA * planes.PUNTOS_POR_PREGUNTA)


class PruebasAlertas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = nueva_app()

    def test_cp09_probabilidad_coherente(self):
        """CP-09 | RF-07 | El modelo devuelve probabilidades entre 0 y 1 y asigna más riesgo a peores notas y asistencia."""
        m = self.app.modelo
        bueno = {"nota_pc1": 17, "nota_pc2": 16, "asistencia": 95, "tareas": 95}
        malo = {"nota_pc1": 7, "nota_pc2": 8, "asistencia": 60, "tareas": 40}
        pb, pm = m.probabilidad(bueno), m.probabilidad(malo)
        self.assertTrue(0 <= pb <= 1 and 0 <= pm <= 1)
        self.assertLess(pb, 0.2)
        self.assertGreater(pm, 0.8)

    def test_cp10_riesgo_y_recomendaciones(self):
        """CP-10 | RF-08 | El estudiante ve su nivel de riesgo (alto/medio/bajo) y recomendaciones."""
        r = self.app.riesgo("E001")
        self.assertIn(r["nivel"], {"alto", "medio", "bajo"})
        self.assertTrue(r["recomendaciones"])

    def test_cp14_sensibilidad(self):
        """CP-14 | RNF-02 | El modelo detecta al menos el 70 % de los estudiantes en riesgo en los datos simulados de prueba."""
        filas = alertas.cargar_dataset()
        entrenamiento, prueba = alertas.dividir(filas)
        modelo = alertas.ModeloRiesgo().entrenar(entrenamiento)
        met = modelo.evaluar(prueba)
        METRICAS["alertas"] = met
        METRICAS["dataset"] = {"registros": len(filas), "entrenamiento": len(entrenamiento), "prueba": len(prueba),
                               "desaprobados": sum(r["desaprobo"] for r in filas)}
        self.assertGreaterEqual(met["sensibilidad"], 0.70)

    def test_cp15_datos_anonimizados(self):
        """CP-15 | RNF-03 | Los datos son simulados y anonimizados: solo códigos E###, sin nombres, DNI ni correos."""
        with open(alertas.DATASET_PATH, encoding="utf-8") as f:
            lector = csv.DictReader(f)
            columnas = set(lector.fieldnames)
            filas = list(lector)
        prohibidas = {"nombre", "nombres", "apellido", "apellidos", "dni", "correo", "email", "telefono", "direccion"}
        self.assertFalse(columnas & prohibidas)
        self.assertTrue(all(re.fullmatch(r"E\d{3}", r["codigo"]) for r in filas))
        texto = alertas.DATASET_PATH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"[\w.]+@[\w.]+|\b\d{8}\b", texto))


class PruebasCargaNotas(unittest.TestCase):
    def setUp(self):
        self.app = nueva_app()

    def test_cp19_carga_de_notas(self):
        """CP-19 | RF-11 | El docente carga un CSV anonimizado de notas; se rechazan datos personales y valores fuera de rango."""
        ejemplo = (BASE / "docs" / "ejemplos" / "notas_GPC_ejemplo.csv").read_text(encoding="utf-8-sig")
        r = self.app.cargar_notas("GPC", ejemplo)          # separador ";" y coma decimal, como exporta Excel
        self.assertEqual(r["registros"], 20)
        lista = self.app.alertas("GPC")
        self.assertEqual({a["codigo"] for a in lista}, {f"E{301 + i}" for i in range(20)})
        self.assertEqual(self.app.riesgo("E301")["curso"], "GPC")
        self.assertTrue(all(a["curso"] == "IHC" for a in self.app.alertas("IHC")))  # el otro curso no cambia
        malos = [
            "codigo;nombre;nota_pc1;nota_pc2;asistencia;tareas\nE401;Ana Torres;14;13;90;80\n",  # dato personal
            "codigo,nota_pc1,nota_pc2,asistencia,tareas\nE401,25,13,90,80\n",                    # nota > 20
            "codigo,nota_pc1,nota_pc2,asistencia,tareas\n71234567,14,13,90,80\n",               # código no anonimizado
            "codigo,nota_pc1,asistencia\nE401,14,90\n",                                         # faltan columnas
        ]
        for texto in malos:
            with self.assertRaises(ValueError):
                self.app.cargar_notas("GPC", texto)
        self.assertEqual(len(self.app.alertas("GPC")), 20)  # un archivo rechazado no altera lo cargado
        self.app.restaurar_notas("GPC")
        self.assertEqual(self.app.origen_notas("GPC"), "simulado")
        self.assertEqual(len(self.app.alertas("GPC")), 120)


class PruebasTablero(unittest.TestCase):
    def setUp(self):
        self.app = nueva_app()

    def test_cp11_metricas_por_tema(self):
        """CP-11 | RF-09 | El tablero agrega las consultas por tema y coincide con lo registrado."""
        for _ in range(3):
            self.app.chat("E001", "GPC", "¿Cómo se calcula el CPI?")
        self.app.chat("E003", "GPC", "¿Qué es la ruta crítica?")
        self.app.chat("E005", "GPC", "¿Quién ganó el mundial 2022?")
        t = self.app.tablero("GPC")
        por_tema = {x["tema"]: x for x in t["temas"]}
        self.assertEqual(t["total_consultas"], 5)
        self.assertEqual(t["consultas_fuera_de_silabo"], 1)
        self.assertEqual(por_tema["Índices de desempeño y pronósticos"]["consultas"], 3)
        self.assertEqual(por_tema["Ruta crítica y holgura"]["consultas"], 1)
        self.assertEqual(t["temas_criticos"][0]["tema"], "Índices de desempeño y pronósticos")

    def test_cp12_lista_de_alertas(self):
        """CP-12 | RF-10 | El docente ve a sus estudiantes ordenados por riesgo; solo se marcan los que superan el umbral."""
        lista = self.app.alertas("IHC")
        self.assertTrue(all(a["curso"] == "IHC" for a in lista))
        probs = [a["probabilidad"] for a in lista]
        self.assertEqual(probs, sorted(probs, reverse=True))
        self.assertTrue(all(a["alerta"] == (a["probabilidad"] >= self.app.modelo.umbral) for a in lista))


class PruebasIntegracion(unittest.TestCase):
    """Pruebas extremo a extremo sobre HTTP con el servidor real (EDT 1.4.3)."""

    @classmethod
    def setUpClass(cls):
        cls.app = nueva_app()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), crear_handler(cls.app))
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def pedir(self, ruta, datos=None):
        req = urllib.request.Request(self.url + ruta, data=json.dumps(datos).encode() if datos is not None else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read() or b"null") if "json" in r.headers.get("Content-Type", "") else r.read()
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_cp13_tiempo_de_respuesta(self):
        """CP-13 | RNF-01 | El tiempo de respuesta promedio del chatbot, medido extremo a extremo, es menor a 5 s."""
        tiempos = []
        preguntas = REFERENCIA["en_silabo"] * 2
        for p in preguntas:
            t0 = time.perf_counter()
            estado, _ = self.pedir("/api/chat", {"estudiante": "E001", "curso": p["curso"], "pregunta": p["pregunta"]})
            tiempos.append((time.perf_counter() - t0) * 1000)
            self.assertEqual(estado, 200)
        tiempos.sort()
        METRICAS["tiempo_respuesta"] = {
            "consultas": len(tiempos), "promedio_ms": round(statistics.mean(tiempos), 2),
            "p95_ms": round(tiempos[int(len(tiempos) * 0.95) - 1], 2), "maximo_ms": round(max(tiempos), 2),
            "modo": "generativo" if rag.os.environ.get("GEMINI_API_KEY") else "extractivo"}
        self.assertLess(statistics.mean(tiempos), 5000)

    def test_cp16_seguridad_entradas(self):
        """CP-16 | RNF-04 | La API valida las entradas y la interfaz no inserta HTML sin escapar (OWASP)."""
        estado, d = self.pedir("/api/chat", {"estudiante": "X'; DROP TABLE consultas;--", "curso": "GPC", "pregunta": "hola"})
        self.assertEqual(estado, 400)
        estado, _ = self.pedir("/api/estudiantes/E999/riesgo")
        self.assertEqual(estado, 400)
        req = urllib.request.Request(self.url + "/api/chat", data=b"x" * 30000, headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)
        estado, cuerpo = self.pedir("/../mentoria/db.py")
        self.assertEqual(estado, 200)
        self.assertNotIn(b"sqlite3", cuerpo)  # el servidor no expone archivos fuera de /static
        js = (BASE / "static" / "app.js").read_text(encoding="utf-8")
        self.assertNotRegex(js, r"\.innerHTML\s*=")

    def test_cp17_diseno_adaptable(self):
        """CP-17 | RNF-05 | La interfaz es accesible desde web y móvil (viewport y diseño adaptable)."""
        estado, html = self.pedir("/")
        self.assertEqual(estado, 200)
        self.assertIn(b'name="viewport"', html)
        css = (BASE / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 640px)", css)

    def test_cp18_flujo_extremo_a_extremo(self):
        """CP-18 | RF-02, RF-05, RF-06, RF-09 | Flujo completo: pregunta, plan, tarea completada, logros y tablero."""
        estado, salud = self.pedir("/api/health")
        self.assertEqual((estado, salud["estado"]), (200, "ok"))
        estado, codigos = self.pedir("/api/estudiantes?curso=IHC")
        self.assertEqual(len(codigos), 120)  # la vista estudiante ofrece todos los códigos del curso
        self.assertEqual(len(codigos), len(self.app.alertas("IHC")))
        estado, r = self.pedir("/api/chat", {"estudiante": "E007", "curso": "IHC", "pregunta": "¿Qué es el cuestionario SUS?"})
        self.assertEqual(r["tema"], "Cuestionario SUS")
        estado, plan = self.pedir("/api/planes", {"estudiante": "E007", "curso": "IHC", "horas_semana": 5, "semanas": 2})
        self.assertEqual(estado, 201)
        estado, g = self.pedir(f"/api/tareas/{plan['tareas'][0]['id']}/completar", {"estudiante": "E007"})
        self.assertEqual(g["tareas_completadas"], 1)
        estado, t = self.pedir("/api/tablero?curso=IHC")
        self.assertGreaterEqual(t["total_consultas"], 1)
        self.assertIn("Cuestionario SUS", [x["tema"] for x in t["temas_criticos"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
