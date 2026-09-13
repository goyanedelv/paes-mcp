"""Armado de ensayos y mini-ensayos a partir del material disponible."""

from __future__ import annotations

import random
from typing import Any

from .progreso import Progreso
from .repositorio import Pregunta, RepositorioPreguntas

MODALIDADES = {
    "completo": None,        # tantas como defina la estructura oficial de la prueba
    "minisensayo": 15,
    "focalizado": 10,
    "repaso_errores": 10,
}


def _seleccion_focalizada(
    repo: RepositorioPreguntas, progreso: Progreso, cantidad: int, anio: int | None
) -> list[Pregunta]:
    ejes = progreso.ejes_debiles(repo.spec.id)
    seleccion: list[Pregunta] = []
    vistos: set[str] = set()
    for eje in ejes or list(repo.spec.ejes_tematicos):
        _, preguntas = repo.buscar(
            anio=anio, eje_tematico=eje, excluir_ids=vistos,
            limite=cantidad - len(seleccion), orden="aleatorio",
        )
        seleccion.extend(preguntas)
        vistos.update(p.id_unico for p in preguntas)
        if len(seleccion) >= cantidad:
            break
    if len(seleccion) < cantidad:
        _, extra = repo.buscar(
            anio=anio, excluir_ids=vistos, limite=cantidad - len(seleccion), orden="aleatorio"
        )
        seleccion.extend(extra)
    return seleccion[:cantidad]


def _seleccion_repaso(repo: RepositorioPreguntas, progreso: Progreso, cantidad: int) -> list[Pregunta]:
    pendientes = progreso.pendientes(repo.spec.id, limite=cantidad)
    preguntas: list[Pregunta] = []
    for fila in pendientes:
        try:
            preguntas.append(repo.obtener(fila["id_unico"]))
        except KeyError:  # la pregunta ya no esta en el dataset
            continue
    return preguntas


def generar(
    prueba: str | None = None,
    modalidad: str = "minisensayo",
    anio_referencia: int | None = None,
    cantidad: int | None = None,
    semilla: int | None = None,
    progreso: Progreso | None = None,
) -> dict[str, Any]:
    if modalidad not in MODALIDADES:
        raise ValueError(
            f"Modalidad '{modalidad}' no valida. Opciones: {', '.join(MODALIDADES)}."
        )
    repo = RepositorioPreguntas(prueba)
    progreso = progreso or Progreso()
    estructura = repo.spec.estructura
    objetivo = cantidad or MODALIDADES[modalidad] or estructura.preguntas_validas or 60

    if modalidad == "focalizado":
        preguntas = _seleccion_focalizada(repo, progreso, objetivo, anio_referencia)
    elif modalidad == "repaso_errores":
        preguntas = _seleccion_repaso(repo, progreso, objetivo)
    else:
        _, preguntas = repo.buscar(anio=anio_referencia, limite=objetivo, orden="aleatorio")

    if semilla is not None:
        random.Random(semilla).shuffle(preguntas)

    advertencias: list[str] = []
    if len(preguntas) < objetivo:
        advertencias.append(
            f"Se solicitaron {objetivo} preguntas y el material local disponible alcanza para "
            f"{len(preguntas)}. Agregue mas publicaciones oficiales al dataset para completar el ensayo."
        )
    if modalidad == "completo" and len(preguntas) < estructura.preguntas_validas:
        advertencias.append(
            "Este ensayo no replica la extension oficial de la prueba; tratelo como practica parcial."
        )

    sesion_id = progreso.crear_sesion(repo.spec.id, modalidad, [p.id_unico for p in preguntas])
    duracion = (
        estructura.duracion_minutos
        if modalidad == "completo" or not estructura.preguntas_validas
        else round(estructura.duracion_minutos * len(preguntas) / estructura.preguntas_validas)
    )
    return {
        "sesion_id": sesion_id,
        "prueba": repo.spec.id,
        "modalidad": modalidad,
        "cantidad": len(preguntas),
        "duracion_sugerida_minutos": duracion,
        "anio_referencia": anio_referencia,
        "preguntas": [p.resumen() for p in preguntas],
        "instruccion_para_el_tutor": (
            "Entrega una pregunta a la vez con 'paes_obtener_pregunta' y registra cada respuesta "
            "con 'paes_verificar_respuesta' usando este sesion_id. No adelantes claves."
        ),
        "advertencias": advertencias,
    }
