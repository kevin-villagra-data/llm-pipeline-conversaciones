"""Limpieza de texto antes de escribir el CSV de carga.

Por qué existe: `texto.encode("cp1252", errors="replace")` NO protege de
los caracteres de control. 0x03 es un byte válido en cp1252, así que pasa
sin cambios y después rompe la carga en SQL Server (que toma 0x03 como
fin de texto y desalinea las columnas).
"""
import unicodedata

import pandas as pd

# Se conservan tab, salto de línea y retorno de carro; el resto de 0x00-0x1F y 0x7F se elimina.
_PERMITIDOS = {"\t", "\n", "\r"}


def es_control(c: str) -> bool:
    return unicodedata.category(c) == "Cc" and c not in _PERMITIDOS


def contiene_control(texto) -> bool:
    return isinstance(texto, str) and any(es_control(c) for c in texto)


def safe_clean(texto):
    """Quita caracteres de control y deja el texto en ASCII.

    'PEÑA 819'    -> 'PENA 819'
    'PE\\x03A 819' -> 'PEA 819'  (la letra original no se puede recuperar;
                                 la fila queda marcada para revisión)
    """
    if not isinstance(texto, str):
        return texto
    sin_control = "".join(c for c in texto if not es_control(c))
    return unicodedata.normalize("NFKD", sin_control).encode("ascii", "ignore").decode("ascii")


def limpiar(df: pd.DataFrame, columnas: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    """Limpia las columnas indicadas. Devuelve (df_limpio, marca_revision por fila)."""
    df = df.copy()
    revisar = df[columnas].map(contiene_control).any(axis=1)
    for col in columnas:
        df[col] = df[col].map(safe_clean)
    return df, revisar
