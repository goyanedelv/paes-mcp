"""Conversion de puntaje bruto a la escala PAES (100-1000).

Honestidad metodologica: el DEMRE publica una tabla de transformacion distinta
para cada proceso de admision y para cada prueba. Este repositorio NO inventa
esas tablas. Mientras no se cargue una tabla oficial completa, el servidor
interpola linealmente entre puntos ancla publicos y marca el resultado como
ESTIMADO (`es_oficial: false`). Si usted dispone de la tabla oficial, dejela en
`paes_mcp/data/puntajes/<prueba>_<anio>.json` con el formato
{"correctas": puntaje, ...} y el conversor la usara como fuente autoritativa.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalogo import CATALOGO, Catalogo, EspecificacionPrueba
from .config import CONFIG, Config

DIR_TABLAS_OFICIALES = Path(__file__).resolve().parent / "data" / "puntajes"


class TablaPuntajes:
    """Tabla de conversion correctas -> puntaje, oficial o referencial."""

    def __init__(self, puntos: dict[int, int], *, es_oficial: bool, origen: str, nota: str = "") -> None:
        if not puntos:
            raise ValueError("La tabla de puntajes no puede estar vacia.")
        self.puntos = dict(sorted(puntos.items()))
        self.es_oficial = es_oficial
        self.origen = origen
        self.nota = nota

    @property
    def maximo_correctas(self) -> int:
        return max(self.puntos)

    def convertir(self, correctas: int) -> tuple[int, bool]:
        """Devuelve (puntaje, exacto). `exacto` indica ancla directa, sin interpolar."""
        correctas = max(0, min(correctas, self.maximo_correctas))
        if correctas in self.puntos:
            return self.puntos[correctas], True
        anclas = sorted(self.puntos)
        inferior = max(a for a in anclas if a < correctas)
        superior = min(a for a in anclas if a > correctas)
        y0, y1 = self.puntos[inferior], self.puntos[superior]
        proporcion = (correctas - inferior) / (superior - inferior)
        return round(y0 + proporcion * (y1 - y0)), False

    def como_dict(self) -> dict[str, Any]:
        return {
            "es_oficial": self.es_oficial,
            "origen": self.origen,
            "nota": self.nota,
            "maximo_correctas": self.maximo_correctas,
            "puntos": {str(k): v for k, v in self.puntos.items()},
        }


def _cargar_tabla_oficial(prueba: str, anio: int, cfg: Config) -> TablaPuntajes | None:
    for base in (DIR_TABLAS_OFICIALES, cfg.data_dir / "data" / "puntajes"):
        ruta = base / f"{prueba}_{anio}.json"
        if ruta.is_file():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            puntos = {int(k): int(v) for k, v in datos.items() if not k.startswith("_")}
            return TablaPuntajes(
                puntos,
                es_oficial=True,
                origen=f"tabla oficial DEMRE cargada localmente ({ruta.name})",
                nota=datos.get("_nota", ""),
            )
    return None


def obtener_tabla(
    prueba: str | None = None, anio: int | None = None,
    catalogo: Catalogo | None = None, cfg: Config | None = None,
) -> TablaPuntajes:
    cfg = cfg or CONFIG
    spec: EspecificacionPrueba = (catalogo or CATALOGO).obtener(prueba)
    if anio is not None:
        oficial = _cargar_tabla_oficial(spec.id, anio, cfg)
        if oficial is not None:
            return oficial

    tablas = spec.tablas_puntaje or {}
    meta = tablas.get("_meta", {})
    clave = f"referencia_{anio}" if anio and f"referencia_{anio}" in tablas else None
    if clave is None:
        candidatas = [k for k in tablas if k.startswith("referencia_")]
        if not candidatas:
            raise LookupError(
                f"La prueba '{spec.id}' no tiene tabla de puntajes ni oficial ni referencial."
            )
        clave = sorted(candidatas)[-1]
    puntos = {int(k): int(v) for k, v in tablas[clave].items()}
    return TablaPuntajes(
        puntos,
        es_oficial=False,
        origen=f"puntos ancla publicos ({clave}) con interpolacion lineal",
        nota=meta.get("nota", ""),
    )


def calcular(
    correctas: int, prueba: str | None = None, anio: int | None = None,
    catalogo: Catalogo | None = None, cfg: Config | None = None,
) -> dict[str, Any]:
    spec = (catalogo or CATALOGO).obtener(prueba)
    tabla = obtener_tabla(spec.id, anio, catalogo, cfg)
    validas = spec.estructura.preguntas_validas or tabla.maximo_correctas
    puntaje, exacto = tabla.convertir(correctas)
    advertencias: list[str] = []
    if not tabla.es_oficial:
        advertencias.append(
            "PUNTAJE ESTIMADO: calculado por interpolacion sobre puntos ancla publicos, "
            "no con la tabla oficial completa del DEMRE. Uselo como referencia de estudio."
        )
    if correctas > validas:
        advertencias.append(
            f"Se recibieron {correctas} correctas pero la prueba tiene {validas} preguntas validas "
            "(las piloto no puntuan); el valor fue acotado."
        )
    return {
        "prueba": spec.id,
        "anio": anio,
        "respuestas_correctas": correctas,
        "maximo_posible": validas,
        "puntaje_paes": puntaje,
        "es_oficial": tabla.es_oficial,
        "interpolado": not exacto,
        "escala": f"{spec.estructura.escala_puntaje[0]} - {spec.estructura.escala_puntaje[1]}",
        "origen_tabla": tabla.origen,
        "advertencias": advertencias,
    }
