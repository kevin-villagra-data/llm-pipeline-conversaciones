"""Genera transcripciones sintéticas de llamadas de venta.

Todos los datos son inventados (empresa ficticia "Conecta Fibra").
Sirven para correr el pipeline de punta a punta sin datos reales.
"""
import csv
import random
from datetime import date, timedelta

AGENTES = ["Lucía", "Martín", "Sofía", "Diego", "Camila", "Joaquín"]
CALLES = ["PEÑA", "NÚÑEZ", "GÜEMES", "ECHEVERRÍA", "BELGRANO", "AVELLANEDA",
          "RAMÓN FALCÓN", "MUÑIZ", "PRINGLES", "GASCÓN", "ACUÑA DE FIGUEROA", "LAS HERAS"]
LOCALIDADES = ["CABALLITO", "FLORES", "ALMAGRO", "PALERMO", "LANÚS", "MORÓN", "QUILMES"]
VELOCIDADES = [100, 300, 500, 1000]


def _transcripcion(rng: random.Random) -> str:
    agente = rng.choice(AGENTES)
    dni = rng.randint(20_000_000, 45_999_999)
    calle = rng.choice(CALLES)
    altura = rng.randint(100, 4999)
    localidad = rng.choice(LOCALIDADES)
    telefono = f"11 {rng.randint(4000, 6999)}-{rng.randint(1000, 9999)}"
    velocidad = rng.choice(VELOCIDADES)
    vende = rng.random() < 0.6

    lineas = [
        f"Agente: Buenas tardes, le habla {agente} de Conecta Fibra. ¿En qué puedo ayudarle?",
        f"Cliente: Hola, quería contratar internet de {velocidad} megas.",
        "Agente: Perfecto. ¿Me indica su número de documento?",
        f"Cliente: Sí, es {dni}.",
        "Agente: ¿Cuál es la dirección de instalación?",
        f"Cliente: {calle.title()} {altura}, {localidad.title()}.",
        "Agente: ¿Un teléfono de contacto?",
        f"Cliente: {telefono}.",
    ]
    if vende:
        lineas.append("Agente: Listo, la venta quedó registrada. Le llega la confirmación por mensaje.")
    else:
        lineas.append("Cliente: Lo voy a pensar y vuelvo a llamar, gracias.")
    return "\n".join(lineas)


def generar(ruta: str, filas: int = 300, duplicados: int = 5, semilla: int = 42) -> None:
    """Escribe un CSV con transcripciones sintéticas.

    Agrega algunas transcripciones repetidas a propósito para mostrar
    la deduplicación por hash.
    """
    rng = random.Random(semilla)
    inicio = date(2026, 9, 1)
    registros = []
    for i in range(1, filas + 1):
        registros.append({
            "id_conversacion": f"C{i:06d}",
            "fecha": (inicio + timedelta(days=rng.randint(0, 29))).isoformat(),
            "transcripcion": _transcripcion(rng),
        })
    for j in range(duplicados):
        original = rng.choice(registros[:filas])
        registros.append({**original, "id_conversacion": f"C{filas + j + 1:06d}"})

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id_conversacion", "fecha", "transcripcion"])
        w.writeheader()
        w.writerows(registros)


if __name__ == "__main__":
    generar("data/transcripciones_demo.csv")
