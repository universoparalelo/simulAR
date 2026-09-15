"""Funcionalización de la molécula base antes de armar la roseta (issue #4).

Stub: implementar la química real (punto de anclaje, alineación del grupo
anexado, eliminación del átomo que reemplaza) requiere un caso concreto del
lab — qué molécula/motivo se usa como base, qué grupo anexar y qué átomo se
reemplaza. Hasta tener esa info, esta función no modifica nada: devuelve la
base tal cual, funcionalizada o no. Deja armado el contrato (2 inputs, 1
output, mismo formato .pdb que ya consume `generar_nanocable`) para que
cuando llegue esa info solo haga falta reemplazar el cuerpo de la función.
"""
from __future__ import annotations

from typing import Optional

from app.services.nanocable import parsear_pdb


def funcionalizar(base_pdb: str, grupo_pdb: Optional[str] = None) -> str:
    """Anexa `grupo_pdb` a `base_pdb` en el punto de anclaje de la molécula base.

    TODO(bloqueado por el lab, ver issue #4): lógica química real.
    Por ahora es un passthrough — valida que ambos archivos sean .pdb con
    registros ATOM (mismo chequeo que usa el builder de nanocables) y
    devuelve la base sin modificar.
    """
    parsear_pdb(base_pdb)
    if grupo_pdb is not None:
        parsear_pdb(grupo_pdb)
    return base_pdb
