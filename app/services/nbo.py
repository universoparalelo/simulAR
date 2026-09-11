"""Consulta puntual de interacciones NBO (Natural Bond Orbital) en un .log de Gaussian.

Parsea la tabla "Second Order Perturbation Theory Analysis of Fock Matrix in
NBO Basis" (requiere que el cálculo se haya corrido con `pop=nbo` o similar)
y permite buscar, por átomos, las interacciones donor→acceptor que matchean
una consulta (ej. donor="O10", acceptor="O18-H19"), devolviendo el E(2) de
cada una agrupado por su orbital LP/BD/CR.

No se persiste nada: es una herramienta de consulta ad-hoc en vez de una
métrica — se re-parsea el .log en cada pedido, ver CLAUDE.md.
"""
from __future__ import annotations

import re
from typing import Any

_INICIO_TABLA = "Second Order Perturbation Theory Analysis of Fock Matrix in NBO Basis"
_FIN_TABLA = "Natural Bond Orbitals (Summary)"

_THRESHOLD_RE = re.compile(r"Threshold for printing:\s*([\d.]+)\s*kcal/mol")

_CONTEXTO_RE = re.compile(
    r"^\s*(within unit\s+\d+|from unit\s+\d+\s+to unit\s+\d+)", re.IGNORECASE
)

# Formato real de una línea de interacción (confirmado contra docs/Fructosa-nbo.log.txt):
#   41. LP (   1) O  10                /344. BD*(   1) O  18 - H  19            4.63    1.09    0.064
#    1. BD (   1) H   1 - O   2        / 72. RY*(   1) C   3                    2.61    1.81    0.061
# El donor puede ser de 1 átomo (LP, CR) o 2 (BD); el aceptor siempre lleva
# un "/" antes de su número global de orbital.
_LINEA_RE = re.compile(
    r"^\s*\d+\.\s+"
    r"(?P<donor_tipo>[A-Z]+\*?)\s*\(\s*(?P<donor_n>\d+)\)\s*"
    r"(?P<donor_elem1>[A-Z][a-z]?)\s*(?P<donor_idx1>\d+)"
    r"(?:\s*-\s*(?P<donor_elem2>[A-Z][a-z]?)\s*(?P<donor_idx2>\d+))?"
    r"\s*/\s*\d+\.\s+"
    r"(?P<acep_tipo>[A-Z]+\*?)\s*\(\s*(?P<acep_n>\d+)\)\s*"
    r"(?P<acep_elem1>[A-Z][a-z]?)\s*(?P<acep_idx1>\d+)"
    r"(?:\s*-\s*(?P<acep_elem2>[A-Z][a-z]?)\s*(?P<acep_idx2>\d+))?"
    r"\s+(?P<e2>[\d.]+)\s+(?P<e_diff>[\d.]+)\s+(?P<f_ij>[\d.]+)\s*$"
)

_ATOMO_QUERY_RE = re.compile(r"([A-Za-z]{1,2})\s*(\d+)")

Atomo = tuple[str, int]


def _atomos_de_match(elem1: str, idx1: str, elem2: str | None, idx2: str | None) -> list[Atomo]:
    atomos = [(elem1, int(idx1))]
    if elem2 and idx2:
        atomos.append((elem2, int(idx2)))
    return atomos


def parsear_tabla_nbo(log_path: str) -> dict[str, Any]:
    """Parsea la sección de análisis de segundo orden NBO de un .log de Gaussian.

    Si el .log tiene más de una tabla (ej. NBO corrido en varios pasos), se
    queda con la última — mismo criterio que `parsear_gaussian_log` usa para
    la energía SCF final.

    Devuelve {"filas": [...], "threshold_kcal_mol": float | None}. Si no
    encuentra la tabla, "filas" queda vacía.
    """
    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
    except OSError:
        return {"filas": [], "threshold_kcal_mol": None}

    inicio = contenido.rfind(_INICIO_TABLA)
    if inicio == -1:
        return {"filas": [], "threshold_kcal_mol": None}

    fin = contenido.find(_FIN_TABLA, inicio)
    tabla_texto = contenido[inicio:fin] if fin != -1 else contenido[inicio:]

    threshold_match = _THRESHOLD_RE.search(tabla_texto)
    threshold = float(threshold_match.group(1)) if threshold_match else None

    filas: list[dict[str, Any]] = []
    contexto: str | None = None
    for linea in tabla_texto.splitlines():
        if not linea.strip():
            continue

        contexto_match = _CONTEXTO_RE.match(linea)
        if contexto_match:
            contexto = contexto_match.group(1).strip()
            continue

        m = _LINEA_RE.match(linea)
        if not m:
            continue

        d = m.groupdict()
        filas.append(
            {
                "contexto": contexto,
                "donor_tipo": d["donor_tipo"],
                "donor_n": int(d["donor_n"]),
                "donor_atomos": _atomos_de_match(
                    d["donor_elem1"], d["donor_idx1"], d["donor_elem2"], d["donor_idx2"]
                ),
                "acceptor_tipo": d["acep_tipo"],
                "acceptor_n": int(d["acep_n"]),
                "acceptor_atomos": _atomos_de_match(
                    d["acep_elem1"], d["acep_idx1"], d["acep_elem2"], d["acep_idx2"]
                ),
                "e2": float(d["e2"]),
                "e_diff": float(d["e_diff"]),
                "f_ij": float(d["f_ij"]),
            }
        )

    return {"filas": filas, "threshold_kcal_mol": threshold}


def parsear_atomos_query(texto: str) -> list[Atomo]:
    """Parsea una consulta de átomos tipo "O10" o "O18-H19" en [(elem, idx), ...]."""
    return [(elem.capitalize(), int(idx)) for elem, idx in _ATOMO_QUERY_RE.findall(texto)]


def _mismos_atomos(a: list[Atomo], b: list[Atomo]) -> bool:
    return set(a) == set(b)


def buscar_interacciones(
    filas: list[dict[str, Any]],
    donor_query: list[Atomo],
    acceptor_query: list[Atomo],
) -> list[dict[str, Any]]:
    """Filtra las filas cuyo donor y aceptor coinciden exactamente (sin
    importar el orden de los átomos) con los átomos consultados."""
    return [
        fila
        for fila in filas
        if _mismos_atomos(fila["donor_atomos"], donor_query)
        and _mismos_atomos(fila["acceptor_atomos"], acceptor_query)
    ]


def consultar_nbo(log_path: str, donor: str, acceptor: str) -> dict[str, Any]:
    """Punto de entrada de la consulta: parsea el .log y busca la interacción
    donor→acceptor pedida. Lanza ValueError con un mensaje claro si la
    consulta no se puede interpretar o si el .log no tiene tabla NBO."""
    donor_atomos = parsear_atomos_query(donor)
    acceptor_atomos = parsear_atomos_query(acceptor)

    if not donor_atomos:
        raise ValueError(f"No se pudo interpretar el donor: {donor!r}")
    if not acceptor_atomos:
        raise ValueError(f"No se pudo interpretar el aceptor: {acceptor!r}")

    tabla = parsear_tabla_nbo(log_path)
    if not tabla["filas"]:
        raise ValueError(
            'No se encontró la tabla "Second Order Perturbation Theory" en el .log. '
            "¿Se corrió el cálculo con pop=nbo?"
        )

    resultados = sorted(
        buscar_interacciones(tabla["filas"], donor_atomos, acceptor_atomos),
        key=lambda f: f["donor_n"],
    )

    return {
        "donor": donor,
        "acceptor": acceptor,
        "threshold_kcal_mol": tabla["threshold_kcal_mol"],
        "resultados": [
            {
                "orbital": f'{fila["donor_tipo"]}({fila["donor_n"]})',
                "e2_kcal_mol": fila["e2"],
                "e_diff_au": fila["e_diff"],
                "f_ij_au": fila["f_ij"],
                "contexto": fila["contexto"],
            }
            for fila in resultados
        ],
    }
