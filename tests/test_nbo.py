"""Tests del parser de interacciones NBO (services/nbo.py), usando el .log
real de docs/Fructosa-nbo.log.txt como fixture (mismo que se usa para
probar la feature a mano, ver detalle de la simulación en la UI)."""
from pathlib import Path

import pytest

from app.services.nbo import consultar_nbo, parsear_atomos_query, parsear_tabla_nbo

FIXTURE_LOG = Path(__file__).resolve().parent.parent / "docs" / "Fructosa-nbo.log.txt"


def test_parsear_atomos_query_un_atomo():
    assert parsear_atomos_query("O10") == [("O", 10)]


def test_parsear_atomos_query_dos_atomos():
    assert parsear_atomos_query("O18-H19") == [("O", 18), ("H", 19)]


def test_parsear_tabla_nbo_encuentra_filas():
    tabla = parsear_tabla_nbo(str(FIXTURE_LOG))
    assert tabla["threshold_kcal_mol"] == 0.5
    assert len(tabla["filas"]) > 0


def test_consultar_nbo_interaccion_conocida():
    """LP(1) O10 -> BD*(1) O18-H19, E(2)=4.63 kcal/mol: confirmado a mano
    contra el .log (línea ~2912) y contra la UI."""
    resultado = consultar_nbo(str(FIXTURE_LOG), donor="O10", acceptor="O18-H19")
    assert resultado["threshold_kcal_mol"] == 0.5
    orbitales = {r["orbital"]: r["e2_kcal_mol"] for r in resultado["resultados"]}
    assert orbitales["LP(1)"] == pytest.approx(4.63)
    assert orbitales["LP(2)"] == pytest.approx(8.80)


def test_consultar_nbo_sin_resultados_no_es_error():
    resultado = consultar_nbo(str(FIXTURE_LOG), donor="C99", acceptor="C98")
    assert resultado["resultados"] == []


def test_consultar_nbo_donor_invalido():
    with pytest.raises(ValueError):
        consultar_nbo(str(FIXTURE_LOG), donor="???", acceptor="O18-H19")


def test_consultar_nbo_sin_tabla_nbo_en_el_log(tmp_path):
    log_sin_nbo = tmp_path / "sin_nbo.log"
    log_sin_nbo.write_text(" Entering Gaussian System, Link 0=g09\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pop=nbo"):
        consultar_nbo(str(log_sin_nbo), donor="O10", acceptor="O18-H19")
