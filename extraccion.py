"""Extracción de datos estructurados desde la transcripción.

En producción esto lo hace Gemini dentro de BigQuery con AI.GENERATE
(ver sql/bigquery/01_extraccion_gemini.sql). Para poder correr el
proyecto sin una cuenta de GCP, acá hay un extractor local que devuelve
la misma estructura.

El extractor local además simula el problema real que apareció en
producción: en unas pocas filas el modelo devolvió caracteres de control
(0x03, 0x04, 0x13, 0x14) en lugar de la Ñ y de vocales acentuadas.
"""
import random
import re

import pandas as pd

COLUMNAS_SALIDA = ["documento", "telefono", "direccion", "resumen", "venta_concretada"]

# Lo que se observó en la salida del modelo: letras reemplazadas por bytes de control.
CORRUPCION = {"Ñ": "\x03", "Ó": "\x04", "Í": "\x13", "Ú": "\x14"}


def _extraer_una(texto: str) -> dict:
    dni = re.search(r"es (\d{7,8})", texto)
    tel = re.search(r"Cliente: (11 \d{4}-\d{4})", texto)
    dire = re.search(r"Cliente: ([^\n]+?\d+), ([^\n]+)\.", texto)
    vendio = "venta quedó registrada" in texto
    vel = re.search(r"internet de (\d+) megas", texto)
    return {
        "documento": dni.group(1) if dni else None,
        "telefono": tel.group(1) if tel else None,
        "direccion": f"{dire.group(1)}, {dire.group(2)}".upper() if dire else None,
        "resumen": f"Cliente consulta por plan de {vel.group(1) if vel else '?'} megas; "
                   + ("se concreta la venta." if vendio else "no concreta."),
        "venta_concretada": vendio,
    }


def _corromper(valor: str) -> str:
    for letra, byte in CORRUPCION.items():
        if letra in valor:
            return valor.replace(letra, byte, 1)
    return valor


def extraer_local(df: pd.DataFrame, filas_corruptas: int = 4, semilla: int = 7) -> pd.DataFrame:
    """Devuelve una fila por conversación con las columnas que pediría el prompt."""
    salida = pd.DataFrame([_extraer_una(t) for t in df["transcripcion"]], index=df.index)

    # Simula el bug del modelo en unas pocas filas con letras "corrompibles".
    rng = random.Random(semilla)
    candidatas = [i for i, d in salida["direccion"].items()
                  if d and any(c in d for c in CORRUPCION)]
    for i in rng.sample(candidatas, min(filas_corruptas, len(candidatas))):
        salida.at[i, "direccion"] = _corromper(salida.at[i, "direccion"])

    return pd.concat([df[["id_conversacion", "fecha"]], salida], axis=1)
