import pandas as pd

from pipeline_llm import carga, compresion, extraccion, limpieza, validacion


# --- El bug de producción, en un test -------------------------------------

def test_cp1252_con_replace_no_detecta_caracteres_de_control():
    # 0x03 es válido en cp1252: errors="replace" lo deja pasar tal cual.
    assert "PE\x03A 819".encode("cp1252", errors="replace") == b"PE\x03A 819"


def test_safe_clean_quita_control_y_acentos():
    assert limpieza.safe_clean("PE\x03A 819") == "PEA 819"
    assert limpieza.safe_clean("PEÑA 819, LANÚS") == "PENA 819, LANUS"
    assert limpieza.safe_clean("linea1\nlinea2\tok") == "linea1\nlinea2\tok"
    assert limpieza.safe_clean(None) is None


def test_limpiar_marca_filas_para_revision():
    df = pd.DataFrame({"direccion": ["PEÑA 819", "PE\x03A 819"], "resumen": ["ok", "ok"]})
    limpio, revisar = limpieza.limpiar(df, ["direccion", "resumen"])
    assert revisar.tolist() == [False, True]
    assert limpio["direccion"].tolist() == ["PENA 819", "PEA 819"]


# --- Validación del archivo -------------------------------------------------

def _csv(tmp_path, filas):
    ruta = tmp_path / "x.csv"
    ruta.write_bytes(b"\r\n".join(filas) + b"\r\n")
    return str(ruta)


def test_validar_csv_ok(tmp_path):
    r = validacion.validar_csv(_csv(tmp_path, [b"a|b|c", b"1|PE\xd1A|3"]), 3)
    assert r.ok and r.filas == 2


def test_validar_csv_detecta_byte_de_control_y_linea(tmp_path):
    r = validacion.validar_csv(_csv(tmp_path, [b"a|b|c", b"1|PE\x03A|3"]), 3)
    assert not r.ok
    assert r.errores == ["línea 2: caracteres de control 0x03"]


def test_validar_csv_detecta_columnas_desalineadas(tmp_path):
    r = validacion.validar_csv(_csv(tmp_path, [b"a|b|c", b"1|2"]), 3)
    assert "línea 2: 2 columnas, se esperaban 3" in r.errores


# --- Compresión y deduplicación ---------------------------------------------

def test_compresion_ida_y_vuelta():
    texto = "Agente: Hola\nCliente: Peña 819, Lanús"
    assert compresion.descomprimir(compresion.comprimir(texto)) == texto


def test_hash_ignora_espacios_y_mayusculas():
    assert compresion.hash_texto("Hola  Mundo\n") == compresion.hash_texto("hola mundo")


def test_deduplicar():
    df = pd.DataFrame({"transcripcion": ["a b", "A  B", "c"]})
    unico, descartadas = compresion.deduplicar(df)
    assert len(unico) == 2 and descartadas == 1


# --- Extracción y carga -----------------------------------------------------

def test_extraccion_devuelve_columnas_esperadas():
    t = ("Cliente: Hola, quería contratar internet de 300 megas.\nCliente: Sí, es 30111222.\n"
         "Cliente: Peña 819, Lanús.\nCliente: 11 4555-1234.\n"
         "Agente: Listo, la venta quedó registrada.")
    df = pd.DataFrame({"id_conversacion": ["C1"], "fecha": ["2026-09-01"], "transcripcion": [t]})
    fila = extraccion.extraer_local(df, filas_corruptas=0).iloc[0]
    assert fila["documento"] == "30111222"
    assert fila["telefono"] == "11 4555-1234"
    assert fila["direccion"] == "PEÑA 819, LANÚS"
    assert bool(fila["venta_concretada"]) is True


def test_carga_por_lotes(tmp_path):
    con = carga.conexion_demo(str(tmp_path / "t.db"))
    df = pd.DataFrame([{"id_conversacion": f"C{i}", "hash_conversacion": f"h{i}"} for i in range(2500)])
    assert carga.cargar_por_lotes(con, "conversaciones_llm", df, lote=1000) == 2500
    assert con.execute("SELECT COUNT(*) FROM conversaciones_llm").fetchone()[0] == 2500
