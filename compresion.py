"""Compresión y deduplicación de transcripciones.

- La transcripción completa se guarda comprimida (gzip + base64) para que
  el dashboard HTML la pueda descomprimir en el navegador sin pesar de más.
- El hash SHA-256 del texto normalizado identifica conversaciones repetidas.
"""
import base64
import gzip
import hashlib

import pandas as pd


def comprimir(texto: str) -> str:
    return base64.b64encode(gzip.compress(texto.encode("utf-8"), mtime=0)).decode("ascii")


def descomprimir(dato: str) -> str:
    return gzip.decompress(base64.b64decode(dato)).decode("utf-8")


def hash_texto(texto: str) -> str:
    normalizado = " ".join(texto.split()).lower()
    return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def deduplicar(df: pd.DataFrame, columna: str = "transcripcion") -> tuple[pd.DataFrame, int]:
    """Agrega hash_conversacion y descarta repetidas. Devuelve (df, cantidad_descartada)."""
    df = df.copy()
    df["hash_conversacion"] = df[columna].map(hash_texto)
    antes = len(df)
    df = df.drop_duplicates(subset="hash_conversacion", keep="first")
    return df, antes - len(df)
