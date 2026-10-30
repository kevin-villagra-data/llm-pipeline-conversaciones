"""Corre el pipeline completo con datos sintéticos.

    python main.py                 # flujo normal
    python main.py --sin-limpieza  # reproduce el error de producción
"""
import argparse
import os
import sys

import pandas as pd

from pipeline_llm import carga, compresion, datos_sinteticos, extraccion, limpieza, validacion

COLUMNAS_TEXTO = ["documento", "telefono", "direccion", "resumen"]


def main() -> int:
    p = argparse.ArgumentParser(description="Pipeline LLM sobre conversaciones (demo)")
    p.add_argument("--entrada", default="data/transcripciones_demo.csv")
    p.add_argument("--salida", default="salida")
    p.add_argument("--sin-limpieza", action="store_true",
                   help="saltea safe_clean para ver cómo lo detecta el validador")
    args = p.parse_args()
    os.makedirs(args.salida, exist_ok=True)

    if not os.path.exists(args.entrada):
        datos_sinteticos.generar(args.entrada)

    # 1. Lectura y deduplicación por hash
    df = pd.read_csv(args.entrada, dtype=str)
    df, repetidas = compresion.deduplicar(df)
    print(f"[1] {len(df)} conversaciones únicas ({repetidas} repetidas descartadas por SHA-256)")

    # 2. Extracción (en producción: Gemini en BigQuery)
    extraido = extraccion.extraer_local(df)
    extraido["hash_conversacion"] = df["hash_conversacion"]
    extraido["transcripcion_gz"] = df["transcripcion"].map(compresion.comprimir)
    print(f"[2] Extracción: {len(extraido)} filas con {len(extraccion.COLUMNAS_SALIDA)} campos")

    # 3. Limpieza
    if args.sin_limpieza:
        extraido["requiere_revision"] = False
        print("[3] Limpieza salteada (--sin-limpieza)")
    else:
        extraido, revisar = limpieza.limpiar(extraido, COLUMNAS_TEXTO)
        extraido["requiere_revision"] = revisar
        print(f"[3] Limpieza: {int(revisar.sum())} filas tenían caracteres de control -> marcadas para revisión")

    # 4. Archivo de carga + validación por bytes
    columnas = ["id_conversacion", "fecha", "hash_conversacion", *extraccion.COLUMNAS_SALIDA,
                "requiere_revision", "transcripcion_gz"]
    extraido = extraido[columnas]
    ruta_csv = os.path.join(args.salida, "carga_conversaciones.csv")
    carga.escribir_csv(extraido, ruta_csv)
    res = validacion.validar_csv(ruta_csv, columnas_esperadas=len(columnas))
    if not res.ok:
        print(f"[4] Validación FALLÓ en {len(res.errores)} línea(s) de {res.filas}:")
        for e in res.errores:
            print("    -", e)
        print("    La carga se cancela antes de llegar a la base.")
        return 1
    print(f"[4] Validación OK: {res.filas} líneas sin caracteres de control y con columnas consistentes")

    # 5. Carga por lotes
    con = carga.conexion_demo(os.path.join(args.salida, "demo.db"))
    n = carga.cargar_por_lotes(con, "conversaciones_llm", extraido)
    ventas = con.execute("SELECT SUM(venta_concretada) FROM conversaciones_llm").fetchone()[0]
    print(f"[5] Carga: {n} filas en conversaciones_llm ({ventas} con venta concretada)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
