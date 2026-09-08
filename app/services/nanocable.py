"""Generación de nanocables supramoleculares a partir de una roseta base.

Reimplementación sin dependencias externas (NumPy + stdlib) del pipeline que
antes corría en Colab con condacolab + PyMOL: parsea un .pdb con una roseta,
la replica N veces incrementando numeración de átomos/residuos, rota cada
roseta un ángulo creciente sobre un eje y vuelve a escribir el .pdb final.

Nota de precisión científica: la traslación entre rosetas apiladas
(`distancia_z`) y el pivote de rotación (centroide de cada roseta) son
aproximaciones razonables para validar el flujo, pero deben confirmarse
contra la salida del notebook original antes de usar esto en producción.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np


def parsear_pdb(contenido: str) -> List[Dict[str, Any]]:
    """Parsea registros ATOM de un PDB usando las columnas fijas del formato
    (no `.split()`, que se rompe con coordenadas negativas pegadas)."""
    atomos = []
    for numero_linea, linea in enumerate(contenido.splitlines(), start=1):
        if not linea.startswith("ATOM"):
            continue
        linea = linea.ljust(80)
        try:
            atomos.append(
                {
                    "record": linea[0:6].strip(),
                    "serial": int(linea[6:11]),
                    "name": linea[12:16].strip(),
                    "altloc": linea[16].strip(),
                    "resname": linea[17:20].strip(),
                    "chain": linea[21].strip(),
                    "resseq": int(linea[22:26]),
                    "icode": linea[26].strip(),
                    "x": float(linea[30:38]),
                    "y": float(linea[38:46]),
                    "z": float(linea[46:54]),
                    "occupancy": float(linea[54:60]) if linea[54:60].strip() else 1.0,
                    "tempfactor": float(linea[60:66]) if linea[60:66].strip() else 0.0,
                    "element": linea[76:78].strip(),
                }
            )
        except ValueError as exc:
            raise ValueError(f"Línea PDB malformada (línea {numero_linea}): {linea!r}") from exc

    if not atomos:
        raise ValueError("El archivo no contiene registros ATOM válidos")
    return atomos


def extender_nanocable(
    atomos: List[Dict[str, Any]], n_repeticiones: int, distancia_z: float = 0.0
) -> Tuple[List[Dict[str, Any]], int]:
    """Devuelve la roseta original + N copias con residue/atom number
    incrementados y, opcionalmente, trasladadas en Z para apilarlas."""
    if n_repeticiones < 0:
        raise ValueError("n_repeticiones debe ser >= 0")

    residuos_por_roseta = max(atomo["resseq"] for atomo in atomos)
    atomos_por_roseta = len(atomos)

    resultado = [dict(atomo) for atomo in atomos]
    for i in range(1, n_repeticiones + 1):
        for atomo in atomos:
            copia = dict(atomo)
            copia["resseq"] = atomo["resseq"] + residuos_por_roseta * i
            copia["serial"] = atomo["serial"] + atomos_por_roseta * i
            copia["z"] = atomo["z"] + distancia_z * i
            resultado.append(copia)

    return resultado, residuos_por_roseta


def _matriz_rotacion(eje: str, angulo_grados: float) -> np.ndarray:
    theta = np.radians(angulo_grados)
    c, s = np.cos(theta), np.sin(theta)
    if eje == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if eje == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    if eje == "z":
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    raise ValueError(f"Eje inválido: {eje!r} (debe ser 'x', 'y' o 'z')")


def rotar_por_roseta(
    atomos: List[Dict[str, Any]],
    angulo_incremento: float,
    residuos_por_roseta: int,
    eje: str = "z",
) -> List[Dict[str, Any]]:
    """Rota cada roseta un múltiplo de `angulo_incremento` sobre su propio
    centroide (roseta 0 sin rotar, roseta 1 rotada 1x el ángulo, etc.)."""
    if residuos_por_roseta <= 0:
        raise ValueError("residuos_por_roseta debe ser > 0")

    coords_por_roseta: Dict[int, List[Tuple[float, float, float]]] = {}
    for atomo in atomos:
        idx = (atomo["resseq"] - 1) // residuos_por_roseta
        coords_por_roseta.setdefault(idx, []).append((atomo["x"], atomo["y"], atomo["z"]))
    centroides = {idx: np.mean(coords, axis=0) for idx, coords in coords_por_roseta.items()}

    resultado = []
    for atomo in atomos:
        idx = (atomo["resseq"] - 1) // residuos_por_roseta
        rotacion = _matriz_rotacion(eje, idx * angulo_incremento)
        centro = centroides[idx]
        punto = np.array([atomo["x"], atomo["y"], atomo["z"]]) - centro
        rotado = rotacion @ punto + centro

        copia = dict(atomo)
        copia["x"], copia["y"], copia["z"] = rotado.tolist()
        resultado.append(copia)

    return resultado


def _formatear_nombre_atomo(nombre: str) -> str:
    nombre = nombre.strip()
    if len(nombre) >= 4:
        return nombre[:4]
    if nombre and nombre[0].isalpha():
        return (" " + nombre).ljust(4)
    return nombre.ljust(4)


def _formatear_linea_atom(atomo: Dict[str, Any]) -> str:
    linea = [" "] * 80
    linea[0:6] = list((atomo.get("record") or "ATOM").ljust(6)[:6])
    linea[6:11] = list(str(atomo["serial"])[-5:].rjust(5))
    linea[12:16] = list(_formatear_nombre_atomo(atomo.get("name", "")))
    linea[16] = (atomo.get("altloc") or " ")[:1] or " "
    linea[17:20] = list((atomo.get("resname") or "").strip()[:3].rjust(3))
    linea[21] = (atomo.get("chain") or " ")[:1] or " "
    linea[22:26] = list(str(atomo["resseq"])[-4:].rjust(4))
    linea[26] = (atomo.get("icode") or " ")[:1] or " "
    linea[30:38] = list(f"{atomo['x']:.3f}".rjust(8))
    linea[38:46] = list(f"{atomo['y']:.3f}".rjust(8))
    linea[46:54] = list(f"{atomo['z']:.3f}".rjust(8))
    linea[54:60] = list(f"{atomo.get('occupancy', 1.0):.2f}".rjust(6))
    linea[60:66] = list(f"{atomo.get('tempfactor', 0.0):.2f}".rjust(6))
    linea[76:78] = list((atomo.get("element") or "").strip()[:2].rjust(2))
    return "".join(linea).rstrip()


def escribir_pdb(atomos: List[Dict[str, Any]]) -> str:
    lineas: List[str] = []
    residuo_anterior = None
    for atomo in atomos:
        if residuo_anterior is not None and atomo["resseq"] != residuo_anterior:
            lineas.append("TER")
        lineas.append(_formatear_linea_atom(atomo))
        residuo_anterior = atomo["resseq"]
    lineas.append("TER")
    lineas.append("END")
    return "\n".join(lineas) + "\n"


def generar_nanocable(
    contenido_pdb: str,
    n_repeticiones: int,
    angulo: float,
    eje: str = "z",
    distancia_z: float = 0.0,
) -> Dict[str, Any]:
    """Pipeline completo: parsear -> extender -> rotar -> escribir."""
    atomos_originales = parsear_pdb(contenido_pdb)
    atomos_extendidos, residuos_por_roseta = extender_nanocable(
        atomos_originales, n_repeticiones, distancia_z
    )
    atomos_rotados = rotar_por_roseta(atomos_extendidos, angulo, residuos_por_roseta, eje)
    pdb_final = escribir_pdb(atomos_rotados)

    return {
        "pdb": pdb_final,
        "atomos_originales": len(atomos_originales),
        "atomos_generados": len(atomos_rotados),
        "n_rosetas": n_repeticiones + 1,
        "residuos_por_roseta": residuos_por_roseta,
    }
