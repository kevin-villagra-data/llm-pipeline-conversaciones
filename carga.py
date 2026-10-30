"""Escritura del archivo de carga y carga por lotes.

En producción el destino es SQL Server (pyodbc con fast_executemany).
Para la demo local se usa SQLite: la API DB-API y el estilo de parámetros
(`?`) son los mismos, así que la función de carga es idéntica.
"""
import csv
import sqlite3

import pandas as pd

SEPARADOR = "|"


def escribir_csv(df: pd.DataFrame, ruta: str) -> None:
    """CSV en cp1252 con separador |, como lo espera el BULK INSERT de destino.

    - Booleanos como 1/0 para que entren directo en columnas BIT.
    - Sin comillas (BULK INSERT clásico no las interpreta), por eso el
      separador se reemplaza dentro de los textos.
    """
    salida = df.copy()
    for col in salida.columns:
        if salida[col].dtype == bool:
            salida[col] = salida[col].astype(int)
        elif salida[col].dtype == object:
            salida[col] = salida[col].map(
                lambda v: v.replace(SEPARADOR, "/") if isinstance(v, str) else
                (int(v) if isinstance(v, bool) else v))
    salida.to_csv(ruta, sep=SEPARADOR, index=False, encoding="cp1252", errors="replace",
                  lineterminator="\r\n", quoting=csv.QUOTE_NONE)


def cargar_por_lotes(conexion, tabla: str, df: pd.DataFrame, lote: int = 1000) -> int:
    columnas = ", ".join(df.columns)
    marcas = ", ".join("?" for _ in df.columns)
    sql = f"INSERT INTO {tabla} ({columnas}) VALUES ({marcas})"
    cursor = conexion.cursor()
    if hasattr(cursor, "fast_executemany"):  # pyodbc
        cursor.fast_executemany = True
    filas = df.astype(object).where(df.notna(), None).values.tolist()
    for i in range(0, len(filas), lote):
        cursor.executemany(sql, filas[i:i + lote])
    conexion.commit()
    return len(filas)


def conexion_demo(ruta_db: str) -> sqlite3.Connection:
    con = sqlite3.connect(ruta_db)
    con.execute("DROP TABLE IF EXISTS conversaciones_llm")
    con.execute("""
        CREATE TABLE conversaciones_llm (
            id_conversacion   TEXT PRIMARY KEY,
            fecha             TEXT,
            hash_conversacion TEXT UNIQUE,
            documento         TEXT,
            telefono          TEXT,
            direccion         TEXT,
            resumen           TEXT,
            venta_concretada  INTEGER,
            requiere_revision INTEGER,
            transcripcion_gz  TEXT
        )""")
    return con


def conexion_sqlserver(cadena: str):
    """Ejemplo para SQL Server. Requiere `pip install pyodbc` y el driver ODBC 18."""
    import pyodbc
    return pyodbc.connect(cadena)
