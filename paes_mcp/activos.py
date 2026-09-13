"""Servicio de activos visuales (recortes PNG de figuras, tablas y graficos).

Las rutas provienen del dataset y siempre se resuelven dentro del directorio de
assets de la prueba: cualquier intento de salir de ese arbol se rechaza.
"""

from __future__ import annotations

import base64
from pathlib import Path

from .catalogo import EspecificacionPrueba
from .config import CONFIG
from .repositorio import Pregunta


class ActivoNoDisponible(FileNotFoundError):
    """La imagen pedida no existe o no es accesible."""


def resolver(spec: EspecificacionPrueba, ruta_relativa: str) -> Path:
    """Convierte la ruta guardada en el dataset en una ruta absoluta segura."""
    if not ruta_relativa:
        raise ActivoNoDisponible("La pregunta no tiene una imagen asociada.")
    candidata = Path(ruta_relativa)
    if candidata.is_absolute():
        raise ActivoNoDisponible("Las rutas absolutas no estan permitidas en el dataset.")
    base_assets = spec.ruta_assets.resolve()
    raiz = CONFIG.data_dir.resolve()
    # El dataset guarda rutas como "assets/images/2024/x.png". Se aceptan tanto
    # relativas a la raiz de datos como relativas al directorio de assets de la
    # prueba, con o sin el prefijo del propio directorio de assets.
    sin_prefijo = (
        Path(*candidata.parts[1:])
        if candidata.parts and candidata.parts[0] == base_assets.name
        else candidata
    )
    intentos = [raiz / candidata, base_assets / candidata, base_assets / sin_prefijo]
    for intento in intentos:
        try:
            resuelta = intento.resolve()
        except OSError:
            continue
        if not resuelta.is_relative_to(base_assets):
            continue
        if resuelta.is_file():
            return resuelta
    raise ActivoNoDisponible(
        f"No se encontro el activo '{ruta_relativa}' dentro de {base_assets}."
    )


def ruta_de_recurso(spec: EspecificacionPrueba, pregunta: Pregunta, recurso: str) -> Path:
    """recurso: 'enunciado', 'completa' u 'opcion/A'."""
    recurso = recurso.strip().lower()
    if recurso == "enunciado":
        return resolver(spec, pregunta.imagen_enunciado or "")
    if recurso == "completa":
        return resolver(spec, pregunta.imagen_completa or "")
    if recurso.startswith("opcion"):
        letra = recurso.split("/")[-1].upper()
        for alt in pregunta.alternativas:
            if alt.letra == letra:
                return resolver(spec, alt.imagen_ruta_relativa or "")
        raise ActivoNoDisponible(f"La alternativa '{letra}' no tiene imagen.")
    raise ActivoNoDisponible(f"Recurso visual desconocido: '{recurso}'.")


def leer_bytes(ruta: Path) -> bytes:
    tamano = ruta.stat().st_size
    if tamano > CONFIG.max_bytes_imagen:
        raise ActivoNoDisponible(
            f"El activo {ruta.name} pesa {tamano} bytes y supera el limite configurado "
            f"({CONFIG.max_bytes_imagen}). Ajuste PAES_MAX_BYTES_IMAGEN."
        )
    return ruta.read_bytes()


def leer_base64(ruta: Path) -> str:
    return base64.b64encode(leer_bytes(ruta)).decode("ascii")
