"""Tests de detect_software(): la lógica que decide qué pipeline de análisis
corre cada simulación. Ver CLAUDE.md / PR #8 por el bug que motivó estos
tests (un .chk suelto en una carpeta de AMBER se detectaba como Gaussian)."""
from app.services.escaner import detect_software


def _files(exts):
    return [{"extension": ext, "ruta_completa": f"/sim/archivo{ext}"} for ext in exts]


def test_amber_por_extensiones_propias():
    assert detect_software(_files([".prmtop", ".inpcrd", ".mdcrd"])) == "AMBER"


def test_gromacs_por_extensiones_propias():
    assert detect_software(_files([".gro", ".top", ".xtc"])) == "GROMACS"


def test_gaussian_por_gjf():
    assert detect_software(_files([".gjf", ".log"])) == "Gaussian"


def test_gaussian_por_fchk():
    assert detect_software(_files([".fchk"])) == "Gaussian"


def test_travis():
    assert detect_software(_files([".travis"])) == "Travis"


def test_chk_suelto_no_alcanza_para_gaussian():
    """Sin .gjf/.fchk ni .log que lo confirme, un .chk solo no determina software."""
    assert detect_software(_files([".chk"])) is None


def test_amber_con_chk_sobrante_no_se_confunde_con_gaussian():
    """Caso reportado: AMBER con un .chk residual seguía detectándose como AMBER."""
    archivos = _files([".prmtop", ".rst7", ".nc", ".mdin", ".chk"])
    assert detect_software(archivos) == "AMBER"


def test_gromacs_con_chk_sobrante_no_se_confunde_con_gaussian():
    archivos = _files([".gro", ".top", ".xtc", ".chk"])
    assert detect_software(archivos) == "GROMACS"


def test_gaussian_real_con_chk_y_gjf_sigue_funcionando():
    """El caso legítimo (.chk + .gjf juntos, como deja Gaussian real) no se rompe."""
    archivos = _files([".gjf", ".chk", ".log"])
    assert detect_software(archivos) == "Gaussian"


def test_sin_senales_devuelve_none():
    assert detect_software(_files([".txt", ".csv"])) is None


def test_log_de_gaussian_por_contenido(tmp_path):
    log = tmp_path / "salida.log"
    log.write_text(" Entering Gaussian System, Link 0=g09\n", encoding="utf-8")
    archivos = [{"extension": ".log", "ruta_completa": str(log)}]
    assert detect_software(archivos) == "Gaussian"


def test_chk_suelto_confirmado_por_log_de_gaussian(tmp_path):
    """Sin .gjf/.fchk, un .chk solo se confirma como Gaussian vía contenido del .log."""
    log = tmp_path / "salida.log"
    log.write_text(" Entering Gaussian System, Link 0=g16\n", encoding="utf-8")
    archivos = [
        {"extension": ".chk", "ruta_completa": "/sim/archivo.chk"},
        {"extension": ".log", "ruta_completa": str(log)},
    ]
    assert detect_software(archivos) == "Gaussian"


def test_log_de_amber_por_contenido(tmp_path):
    log = tmp_path / "salida.log"
    log.write_text(" Amber 20 SANDER \n", encoding="utf-8")
    archivos = [{"extension": ".log", "ruta_completa": str(log)}]
    assert detect_software(archivos) == "AMBER"
