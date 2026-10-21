"""Módulo 1 – Base de conocimiento RAG y chatbot académico (EDT 1.3.1 y 1.3.2).

Recuperación: los sílabos se fragmentan por tema (sección "##") y cada fragmento
se representa con un vector TF-IDF local (embeddings locales, sin servicios
externos). La consulta se compara por similitud coseno y se recuperan los
fragmentos más pertinentes.

Generación: si existe la variable de entorno GEMINI_API_KEY se envían los
fragmentos como contexto al modelo generativo (capa gratuita). Sin clave, o si
el modelo no responde a tiempo, el chatbot compone una respuesta extractiva con
las oraciones más pertinentes del sílabo. En ambos casos la respuesta cita su
fuente y, si la confianza es baja, el chatbot declara que el tema no está en el
sílabo en lugar de inventar (control del riesgo R1).
"""
import json
import math
import os
import re
import time
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SILABOS_DIR = DATA_DIR / "silabos"
INDEX_PATH = DATA_DIR / "indice_vectorial.json"

UMBRAL_CONFIANZA = 0.12
TOP_K = 3

STOPWORDS = set("""
a al algo algun alguna algunas alguno algunos ante antes aqui asi aun cada como con contra cual cuales
cuando de del desde donde dos e el ella ellas ellos en entre era es esa esas ese eso esos esta estan
estas este esto estos fue ha hay la las le les lo los mas me mi mis muy ni no nos o otra otro para pero
por porque que quien se segun ser si sin sobre son su sus tambien te tiene tienen todo todos tu un una
unas uno unos y ya yo explica explicame dime puedes podrias quiero saber significa sirve hace hacer
cuanto cuantos cual cuales entiendo entender ayuda ayudame favor por hola gracias es son
""".split())


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def raiz(token):
    """Lematización ligera para español: plurales y sufijos frecuentes."""
    for suf in ("aciones", "acion", "amente", "mente", "idades", "idad", "ciones", "cion", "es", "s"):
        if len(token) > len(suf) + 3 and token.endswith(suf):
            return token[: -len(suf)]
    return token


def tokenizar(texto):
    # Las siglas en mayúsculas (SUS, CPI, EDT) se conservan aunque coincidan con una palabra vacía.
    siglas = {normalizar(s) for s in re.findall(r"\b[A-ZÁÉÍÓÚ]{2,}\b", texto)}
    tokens = re.findall(r"[a-z0-9]+", normalizar(texto))
    return [raiz(t) if t not in siglas else t for t in tokens
            if (t not in STOPWORDS or t in siglas) and len(t) > 1]


def leer_silabo(ruta):
    """Devuelve (metadatos, lista de fragmentos) de un sílabo en Markdown."""
    texto = Path(ruta).read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if m:
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip()
        texto = texto[m.end():]
    fragmentos, unidad, tema, buffer = [], None, None, []

    def cerrar():
        if tema and buffer:
            contenido = " ".join(" ".join(buffer).split())
            fragmentos.append({"unidad": unidad, "tema": tema, "texto": contenido})

    for linea in texto.splitlines():
        if linea.startswith("# "):
            cerrar(); buffer = []; tema = None
            unidad = linea[2:].strip()
        elif linea.startswith("## "):
            cerrar(); buffer = []
            tema = linea[3:].strip()
        elif linea.strip():
            buffer.append(linea.strip())
    cerrar()
    return meta, fragmentos


class IndiceRAG:
    """Índice vectorial TF-IDF persistido en JSON."""

    def __init__(self, fragmentos, idf):
        self.fragmentos = fragmentos
        self.idf = idf

    # --- construcción -----------------------------------------------------
    @classmethod
    def construir(cls, carpeta=SILABOS_DIR):
        fragmentos = []
        for ruta in sorted(Path(carpeta).glob("*.md")):
            meta, frs = leer_silabo(ruta)
            for i, f in enumerate(frs):
                f.update({
                    "id": f"{meta.get('codigo', ruta.stem)}-{i + 1:02d}",
                    "curso": meta.get("codigo", ruta.stem),
                    "curso_nombre": meta.get("curso", ruta.stem),
                    "archivo": ruta.name,
                })
                # El título del tema pesa doble: resume el contenido del fragmento.
                f["tokens"] = tokenizar(f["tema"]) * 2 + tokenizar(f["unidad"]) + tokenizar(f["texto"])
                fragmentos.append(f)
        n = len(fragmentos)
        df = Counter()
        for f in fragmentos:
            df.update(set(f["tokens"]))
        idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
        for f in fragmentos:
            f["vector"] = cls._vectorizar(f.pop("tokens"), idf)
        return cls(fragmentos, idf)

    @staticmethod
    def _vectorizar(tokens, idf):
        tf = Counter(tokens)
        vec = {t: (1 + math.log(c)) * idf.get(t, 0.0) for t, c in tf.items() if t in idf}
        norma = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: round(v / norma, 6) for t, v in vec.items()}

    def guardar(self, ruta=INDEX_PATH):
        Path(ruta).write_text(json.dumps({"idf": self.idf, "fragmentos": self.fragmentos},
                                         ensure_ascii=False), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta=INDEX_PATH):
        ruta = Path(ruta)
        silabos = list(SILABOS_DIR.glob("*.md"))
        desactualizado = not ruta.exists() or any(s.stat().st_mtime > ruta.stat().st_mtime for s in silabos)
        if desactualizado:
            indice = cls.construir()
            indice.guardar(ruta)
            return indice
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return cls(datos["fragmentos"], datos["idf"])

    # --- consulta ---------------------------------------------------------
    def cursos(self):
        vistos = {}
        for f in self.fragmentos:
            vistos.setdefault(f["curso"], {"codigo": f["curso"], "nombre": f["curso_nombre"], "unidades": []})
            if f["unidad"] not in vistos[f["curso"]]["unidades"]:
                vistos[f["curso"]]["unidades"].append(f["unidad"])
        return list(vistos.values())

    def buscar(self, consulta, curso=None, k=TOP_K):
        q = self._vectorizar(tokenizar(consulta), self.idf)
        resultados = []
        for f in self.fragmentos:
            if curso and f["curso"] != curso:
                continue
            sim = sum(peso * f["vector"].get(t, 0.0) for t, peso in q.items())
            if sim > 0:
                resultados.append((sim, f))
        resultados.sort(key=lambda x: x[0], reverse=True)
        return [(round(s, 4), f) for s, f in resultados[:k]]


def _oraciones_relevantes(consulta, fragmento, maximo=3):
    terminos = set(tokenizar(consulta))
    oraciones = re.split(r"(?<=[.:;])\s+(?=[A-ZÁÉÍÓÚÑ])", fragmento["texto"])
    puntuadas = []
    for i, o in enumerate(oraciones):
        coincidencias = len(terminos & set(tokenizar(o)))
        puntuadas.append((coincidencias, -i, o))
    elegidas = sorted(puntuadas, reverse=True)[:maximo]
    # Se respeta el orden original del sílabo para que la explicación sea legible.
    elegidas.sort(key=lambda x: -x[1])
    texto = " ".join(o for c, _, o in elegidas if c > 0) or oraciones[0]
    return texto


def _generar_con_gemini(consulta, contexto, timeout=4.0):
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        return None
    modelo = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave}"
    prompt = (
        "Eres MentorIA, asistente académico de USIL. Responde en español, en un máximo de 120 palabras, "
        "usando SOLO la información del contexto del sílabo. Si el contexto no responde la pregunta, dilo.\n\n"
        f"Contexto:\n{contexto}\n\nPregunta del estudiante: {consulta}"
    )
    cuerpo = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    try:
        req = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            datos = json.loads(r.read())
        return datos["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None  # se usa la respuesta extractiva


def responder(indice, consulta, curso=None):
    """Responde una consulta. Devuelve un dict con respuesta, fuentes y métricas."""
    inicio = time.perf_counter()
    consulta = (consulta or "").strip()
    if not consulta:
        return {"respuesta": "Escribe tu pregunta sobre el curso.", "fuentes": [], "confianza": 0.0,
                "en_silabo": False, "modo": "validacion", "tema": None, "unidad": None,
                "ms": 0.0}
    hallados = indice.buscar(consulta, curso)
    confianza = hallados[0][0] if hallados else 0.0
    if confianza < UMBRAL_CONFIANZA:
        respuesta = ("No encontré este tema en el sílabo del curso, así que prefiero no responder algo que "
                     "podría ser incorrecto. Reformula la pregunta con términos del curso o consúltalo con tu docente.")
        resultado = {"respuesta": respuesta, "fuentes": [], "confianza": confianza, "en_silabo": False,
                     "modo": "fuera_de_silabo", "tema": None, "unidad": None}
    else:
        principal = hallados[0][1]
        contexto = "\n\n".join(f"[{f['unidad']} – {f['tema']}] {f['texto']}" for _, f in hallados)
        generado = _generar_con_gemini(consulta, contexto)
        if generado:
            cuerpo, modo = generado, "generativo"
        else:
            cuerpo, modo = _oraciones_relevantes(consulta, principal), "extractivo"
        respuesta = f"{cuerpo}\n\nFuente: sílabo de {principal['curso_nombre']}, {principal['unidad']} – {principal['tema']}."
        resultado = {
            "respuesta": respuesta,
            "fuentes": [{"id": f["id"], "curso": f["curso"], "unidad": f["unidad"], "tema": f["tema"],
                         "similitud": s} for s, f in hallados],
            "confianza": confianza, "en_silabo": True, "modo": modo,
            "tema": principal["tema"], "unidad": principal["unidad"],
        }
    resultado["ms"] = round((time.perf_counter() - inicio) * 1000, 2)
    return resultado
