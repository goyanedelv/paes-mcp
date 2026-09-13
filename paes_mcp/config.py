"""Configuracion por variables de entorno.

Todas las rutas se resuelven contra PAES_DATA_DIR (por defecto, la raiz del
repositorio), de modo que el servidor funciona sin configuracion alguna cuando
se ejecuta con `cwd` en el proyecto.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_PAQUETE = Path(__file__).resolve().parent
_RAIZ_REPO = _PAQUETE.parent


def _raiz_datos_por_defecto() -> Path:
    """Raiz del repositorio si trae los datos; si no (instalacion en site-packages),
    el directorio de trabajo actual."""
    if (_RAIZ_REPO / "data").is_dir():
        return _RAIZ_REPO
    return Path.cwd()


def _ruta_env(nombre: str, por_defecto: Path) -> Path:
    valor = os.environ.get(nombre)
    return Path(valor).expanduser().resolve() if valor else por_defecto


@dataclass(frozen=True)
class Config:
    """Rutas y opciones efectivas del servidor."""

    data_dir: Path
    specs_dir: Path
    progreso_db: Path
    prueba_por_defecto: str
    max_bytes_imagen: int

    @classmethod
    def desde_entorno(cls) -> "Config":
        data_dir = _ruta_env("PAES_DATA_DIR", _raiz_datos_por_defecto())
        return cls(
            data_dir=data_dir,
            specs_dir=_ruta_env("PAES_SPECS_DIR", _PAQUETE / "data" / "pruebas"),
            progreso_db=_ruta_env("PAES_PROGRESO_DB", data_dir / "data" / "progreso_estudiante.sqlite"),
            prueba_por_defecto=os.environ.get("PAES_PRUEBA_DEFAULT", "m1"),
            max_bytes_imagen=int(os.environ.get("PAES_MAX_BYTES_IMAGEN", 4 * 1024 * 1024)),
        )


CONFIG = Config.desde_entorno()
