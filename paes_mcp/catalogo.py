"""Catalogo de pruebas soportadas.

El catalogo es la pieza que hace al servidor multi-prueba: cada prueba (M1 hoy;
M2, Competencia Lectora, Ciencias o Historia manana) se declara en un archivo
JSON dentro de `paes_mcp/data/pruebas/`. Agregar una prueba nueva no requiere
tocar el codigo del servidor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import CONFIG, Config


class PruebaDesconocida(KeyError):
    """La prueba solicitada no existe en el catalogo."""


class PruebaNoDisponible(RuntimeError):
    """La prueba esta declarada pero su dataset aun no esta presente."""


@dataclass(frozen=True)
class EstructuraOficial:
    preguntas_totales: int
    preguntas_piloto: int
    preguntas_validas: int
    alternativas: tuple[str, ...]
    duracion_minutos: int
    escala_puntaje: tuple[int, int]

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> "EstructuraOficial":
        return cls(
            preguntas_totales=int(d.get("preguntas_totales", 0)),
            preguntas_piloto=int(d.get("preguntas_piloto", 0)),
            preguntas_validas=int(d.get("preguntas_validas", 0)),
            alternativas=tuple(d.get("alternativas", ["A", "B", "C", "D"])),
            duracion_minutos=int(d.get("duracion_minutos", 0)),
            escala_puntaje=tuple(d.get("escala_puntaje", [100, 1000])),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class EspecificacionPrueba:
    """Descripcion declarativa de una prueba y de sus activos locales."""

    id: str
    nombre: str
    disciplina: str
    descripcion: str
    estado: str
    ruta_sqlite: Path
    tabla: str
    ruta_assets: Path
    estructura: EstructuraOficial
    ejes_tematicos: tuple[str, ...]
    tablas_puntaje: dict[str, Any]
    anios_con_tabla_propia: tuple[int, ...]
    fuente_oficial: dict[str, str]
    ruta_spec: Path = field(repr=False, default=Path())

    @property
    def dataset_disponible(self) -> bool:
        return self.ruta_sqlite.is_file()

    def exigir_disponible(self) -> None:
        if not self.dataset_disponible:
            raise PruebaNoDisponible(
                f"La prueba '{self.id}' esta declarada pero falta su dataset en "
                f"{self.ruta_sqlite}. Consulte docs/AGREGAR_PRUEBA.md."
            )

    def resumen(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "disciplina": self.disciplina,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "dataset_disponible": self.dataset_disponible,
            "ejes_tematicos": list(self.ejes_tematicos),
            "estructura_oficial": {
                "preguntas_totales": self.estructura.preguntas_totales,
                "preguntas_piloto": self.estructura.preguntas_piloto,
                "preguntas_validas": self.estructura.preguntas_validas,
                "alternativas": list(self.estructura.alternativas),
                "duracion_minutos": self.estructura.duracion_minutos,
                "escala_puntaje": list(self.estructura.escala_puntaje),
            },
            "fuente_oficial": dict(self.fuente_oficial),
        }

    @classmethod
    def desde_archivo(cls, ruta: Path, cfg: Config) -> "EspecificacionPrueba":
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        dataset = datos.get("dataset", {})
        sqlite_rel = Path(dataset.get("sqlite", f"paes_{datos['id']}_dataset.sqlite"))
        assets_rel = Path(dataset.get("assets_base", "assets"))
        return cls(
            id=datos["id"],
            nombre=datos.get("nombre", datos["id"].upper()),
            disciplina=datos.get("disciplina", ""),
            descripcion=datos.get("descripcion", ""),
            estado=datos.get("estado", "activa"),
            ruta_sqlite=sqlite_rel if sqlite_rel.is_absolute() else cfg.data_dir / sqlite_rel,
            tabla=dataset.get("tabla", "preguntas"),
            ruta_assets=assets_rel if assets_rel.is_absolute() else cfg.data_dir / assets_rel,
            estructura=EstructuraOficial.desde_dict(datos.get("estructura_oficial", {})),
            ejes_tematicos=tuple(datos.get("ejes_tematicos", [])),
            tablas_puntaje=datos.get("tablas_puntaje", {}),
            anios_con_tabla_propia=tuple(datos.get("anios_con_tabla_propia", [])),
            fuente_oficial=datos.get("fuente_oficial", {}),
            ruta_spec=ruta,
        )


class Catalogo:
    """Carga y expone las especificaciones de prueba disponibles."""

    def __init__(self, cfg: Config | None = None) -> None:
        self._cfg = cfg or CONFIG
        self._pruebas: dict[str, EspecificacionPrueba] = {}
        self._cargar()

    def _cargar(self) -> None:
        if not self._cfg.specs_dir.is_dir():
            return
        for ruta in sorted(self._cfg.specs_dir.glob("*.json")):
            if ruta.name.startswith("_"):  # _plantilla.json y similares
                continue
            spec = EspecificacionPrueba.desde_archivo(ruta, self._cfg)
            self._pruebas[spec.id] = spec

    def __contains__(self, prueba_id: object) -> bool:
        return prueba_id in self._pruebas

    def ids(self) -> list[str]:
        return list(self._pruebas)

    def todas(self) -> list[EspecificacionPrueba]:
        return list(self._pruebas.values())

    def obtener(self, prueba_id: str | None = None) -> EspecificacionPrueba:
        pid = (prueba_id or self._cfg.prueba_por_defecto).strip().lower()
        if pid not in self._pruebas:
            raise PruebaDesconocida(
                f"Prueba '{pid}' desconocida. Disponibles: {', '.join(self.ids()) or 'ninguna'}."
            )
        return self._pruebas[pid]


CATALOGO = Catalogo()
