"""Tests del stub de funcionalización (issue #4). Ver services/funcionalizacion.py
para el motivo del stub: falta que el lab confirme molécula base, grupo y
punto de anclaje antes de poder implementar la química real."""
import pytest

from app.services.funcionalizacion import funcionalizar
from app.services.nanocable import escribir_pdb

ATOMO_BASE = {
    "record": "ATOM",
    "serial": 1,
    "name": "C1",
    "altloc": "",
    "resname": "MOL",
    "chain": "A",
    "resseq": 1,
    "icode": "",
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "occupancy": 1.0,
    "tempfactor": 0.0,
    "element": "C",
}

PDB_BASE = escribir_pdb([ATOMO_BASE])
PDB_GRUPO = escribir_pdb([{**ATOMO_BASE, "name": "N1", "element": "N"}])


def test_sin_grupo_devuelve_la_base_sin_modificar():
    assert funcionalizar(PDB_BASE) == PDB_BASE


def test_con_grupo_stub_tambien_devuelve_la_base_sin_modificar():
    """Passthrough a propósito: la química real todavía no está implementada."""
    assert funcionalizar(PDB_BASE, PDB_GRUPO) == PDB_BASE


def test_base_invalida_lanza_value_error():
    with pytest.raises(ValueError):
        funcionalizar("esto no es un pdb")


def test_grupo_invalido_lanza_value_error():
    with pytest.raises(ValueError):
        funcionalizar(PDB_BASE, "esto tampoco es un pdb")
