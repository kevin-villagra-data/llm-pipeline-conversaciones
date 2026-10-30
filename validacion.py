"""Validación del archivo final, byte por byte, antes de la carga.

Revisa el archivo tal como va a llegar a SQL Server y no el DataFrame:
el problema de producción solo se veía en los bytes.
"""
from dataclasses import dataclass, field

CONTROL_PERMITIDOS = {0x09, 0x0A, 0x0D}


@dataclass
class ResultadoValidacion:
    filas: int = 0
    errores: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errores


def validar_csv(ruta: str, columnas_esperadas: int, separador: str = "|",
                encoding: str = "cp1252") -> ResultadoValidacion:
    r = ResultadoValidacion()
    with open(ruta, "rb") as f:
        crudo = f.read()

    for n, linea in enumerate(crudo.split(b"\r\n"), start=1):
        if not linea:
            continue
        r.filas += 1

        malos = [b for b in linea if (b < 0x20 and b not in CONTROL_PERMITIDOS) or b == 0x7F]
        if malos:
            detalle = ", ".join(f"0x{b:02X}" for b in sorted(set(malos)))
            r.errores.append(f"línea {n}: caracteres de control {detalle}")

        try:
            texto = linea.decode(encoding)
        except UnicodeDecodeError as e:
            r.errores.append(f"línea {n}: no decodifica en {encoding} ({e.reason})")
            continue

        cols = texto.count(separador) + 1
        if cols != columnas_esperadas:
            r.errores.append(f"línea {n}: {cols} columnas, se esperaban {columnas_esperadas}")

    return r
