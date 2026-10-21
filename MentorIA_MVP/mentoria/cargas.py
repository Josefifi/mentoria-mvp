"""Carga de notas por el docente (EDT 1.3.4, RF-11).

El acta excluye la integración con los sistemas de notas de USIL. En su lugar, el
docente exporta de su registro un extracto anonimizado (notas parciales,
asistencia y tareas) y lo carga como CSV. El archivo se valida antes de usarse:
se rechazan columnas con datos personales, códigos que no sean E### y valores
fuera de rango.
"""
import csv
import io
import re
import unicodedata
from pathlib import Path

from .alertas import VARIABLES

COLUMNAS = ["codigo"] + VARIABLES
RANGOS = {"nota_pc1": (0, 20), "nota_pc2": (0, 20), "asistencia": (0, 100), "tareas": (0, 100)}
PERSONALES = {"nombre", "nombres", "apellido", "apellidos", "dni", "documento", "correo", "email", "mail",
              "telefono", "celular", "direccion", "alumno", "estudiante_nombre"}
DIR_CARGAS = Path(__file__).resolve().parent.parent / "data" / "cargas"
MAX_FILAS = 500
MAX_BYTES = 200_000

PLANTILLA = "codigo;nota_pc1;nota_pc2;asistencia;tareas\nE001;14;12,5;90;85\nE002;9;8;70;60\n"


def _clave(texto):
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def leer_csv(texto, curso):
    """Valida el CSV y devuelve la lista de registros. Lanza ValueError con un mensaje claro."""
    if not texto or not texto.strip():
        raise ValueError("El archivo está vacío.")
    if len(texto.encode("utf-8")) > MAX_BYTES:
        raise ValueError("El archivo supera los 200 KB.")
    texto = texto.lstrip("﻿")
    primera = texto.splitlines()[0]
    separador = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto), delimiter=separador)
    columnas = {_clave(c): c for c in (lector.fieldnames or []) if c}
    personales = sorted(set(columnas) & PERSONALES)
    if personales:
        raise ValueError("El archivo contiene columnas con datos personales (" + ", ".join(personales) +
                         "). Elimínelas y use solo códigos anonimizados E###.")
    faltan = [c for c in COLUMNAS if c not in columnas]
    if faltan:
        raise ValueError("Faltan columnas: " + ", ".join(faltan) + ". Use la plantilla.")
    registros, errores, vistos = [], [], set()
    for n, fila in enumerate(lector, start=2):
        if not any((v or "").strip() for v in fila.values()):
            continue
        codigo = (fila[columnas["codigo"]] or "").strip().upper()
        if not re.fullmatch(r"E\d{3}", codigo):
            errores.append(f"fila {n}: código «{codigo}» no válido (formato E###)")
            continue
        if codigo in vistos:
            errores.append(f"fila {n}: código {codigo} repetido")
            continue
        registro = {"codigo": codigo, "curso": curso, "desaprobo": None}
        for v in VARIABLES:
            bruto = (fila[columnas[v]] or "").strip().replace(",", ".")
            try:
                valor = float(bruto)
            except ValueError:
                errores.append(f"fila {n}: {v} «{bruto}» no es un número")
                break
            minimo, maximo = RANGOS[v]
            if not minimo <= valor <= maximo:
                errores.append(f"fila {n}: {v} = {bruto} fuera del rango {minimo}–{maximo}")
                break
            registro[v] = valor
        else:
            vistos.add(codigo)
            registros.append(registro)
        if len(errores) >= 5:
            break
    if errores:
        raise ValueError("Se encontraron errores; no se cargó nada. " + "; ".join(errores) + ".")
    if not registros:
        raise ValueError("El archivo no tiene filas con datos.")
    if len(registros) > MAX_FILAS:
        raise ValueError(f"El archivo supera las {MAX_FILAS} filas.")
    return registros


def guardar(registros, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for r in registros:
            w.writerow({c: r[c] for c in COLUMNAS})


def leer_guardado(ruta, curso):
    return leer_csv(Path(ruta).read_text(encoding="utf-8"), curso)
