"""Andamiaje socratico graduado.

Las pistas NO son material oficial ni resoluciones publicadas: son directrices
metodologicas generadas por el servidor a partir del eje tematico inferido y de
rasgos estructurales del item (tiene diagrama, alternativas graficas, etc.).

El servidor entrega *como guiar*, no *la respuesta*: en ningun nivel se revela
ni se insinua la alternativa correcta, que ni siquiera se consulta aqui.
"""

from __future__ import annotations

from typing import Any

from .ejes import EJE_DESCONOCIDO
from .repositorio import Pregunta

NIVELES = {
    1: "concepto",
    2: "planteamiento",
    3: "primer_paso",
}

_GUIAS: dict[str, dict[int, str]] = {
    "numeros": {
        1: "Identifica que tipo de numero y que operacion estan en juego (signos, fracciones, potencias, porcentajes) y recuerda la prioridad de operaciones.",
        2: "Traduce el enunciado a una sola expresion numerica antes de calcular; escribe cada dato con su unidad y su signo.",
        3: "Resuelve primero lo que esta dentro de parentesis y las potencias o raices; deja sumas y restas para el final y compara recien entonces con las alternativas.",
    },
    "algebra_y_funciones": {
        1: "Define con claridad que representa la incognita y que relacion entre cantidades describe el enunciado.",
        2: "Escribe la ecuacion, inecuacion o funcion que modela la situacion antes de manipular nada; revisa que cada termino tenga sentido dimensional.",
        3: "Aplica una sola transformacion algebraica valida (factorizar, despejar, reemplazar un valor) y verifica que la igualdad se conserve.",
    },
    "geometria": {
        1: "Reconoce la figura o el cuerpo involucrado y que propiedad lo caracteriza (lados, angulos, simetrias, caras).",
        2: "Marca sobre la figura los datos conocidos y los desconocidos; decide si necesitas Pitagoras, semejanza, area, perimetro o volumen.",
        3: "Plantea la relacion geometrica pertinente con los datos marcados y expresa la incognita en terminos de la variable del enunciado.",
    },
    "probabilidad_y_estadistica": {
        1: "Distingue si te piden describir datos (medidas de tendencia central o dispersion) o cuantificar incertidumbre (probabilidad).",
        2: "Ordena los datos o el espacio muestral de forma explicita: tabla de frecuencias, lista de casos o diagrama.",
        3: "Cuenta casos favorables y casos totales (o ubica la posicion que define la medida pedida) antes de operar.",
    },
    EJE_DESCONOCIDO: {
        1: "Vuelve al enunciado y subraya que se pregunta exactamente y con que unidad debe responderse.",
        2: "Escribe los datos entregados y la relacion que los conecta; decide que herramienta matematica corresponde.",
        3: "Ejecuta solo el primer paso del procedimiento y detente a revisar si el resultado parcial es razonable.",
    },
}

_GUIA_VISUAL = (
    "La pregunta incluye un diagrama: pide al estudiante que describa primero "
    "que ve (ejes, rotulos, unidades, vertices) antes de calcular. No des tu "
    "propia lectura del grafico como si fuera un hecho verificado."
)
_GUIA_OPCIONES_VISUALES = (
    "Las alternativas son graficas: guia al estudiante a enunciar la propiedad "
    "que deberia cumplir la respuesta y a descartar opciones que la violen."
)


def generar(pregunta: Pregunta, nivel: int) -> dict[str, Any]:
    if nivel not in NIVELES:
        raise ValueError(f"nivel_pista debe ser 1, 2 o 3 (recibido: {nivel}).")
    guias = _GUIAS.get(pregunta.eje_tematico, _GUIAS[EJE_DESCONOCIDO])
    notas: list[str] = []
    if pregunta.tiene_diagrama:
        notas.append(_GUIA_VISUAL)
    if pregunta.opciones_visuales:
        notas.append(_GUIA_OPCIONES_VISUALES)
    return {
        "prueba": pregunta.prueba,
        "id_unico": pregunta.id_unico,
        "nivel_pista": nivel,
        "tipo_pista": NIVELES[nivel],
        "eje_tematico": pregunta.eje_tematico,
        "clasificacion_eje": "heuristica",
        "directriz_para_el_tutor": guias[nivel],
        "notas_multimodales": notas,
        "origen": (
            "Andamiaje generado por el servidor (no es material oficial del DEMRE "
            "ni una solucion publicada)."
        ),
        "restriccion": (
            "No reveles la alternativa correcta. Formula una pregunta al estudiante "
            "en lugar de resolver el ejercicio por el."
        ),
    }
