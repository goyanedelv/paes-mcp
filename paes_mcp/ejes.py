"""Clasificacion tematica heuristica de preguntas.

El dataset oficial no publica el eje tematico de cada item, de modo que aqui se
infiere de forma deterministica a partir de palabras clave del enunciado y de
las alternativas. Es una ayuda de estudio, NO una clasificacion oficial del
DEMRE: toda salida que la use viene marcada con `clasificacion: "heuristica"`.
"""

from __future__ import annotations

import re
import unicodedata

EJE_DESCONOCIDO = "sin_clasificar"

# Frases donde una palabra clave aparece con un sentido ajeno a su eje: se
# neutralizan antes de puntuar. Se agregan solo con un caso real que lo
# justifique, nunca de forma preventiva.
ANTIPATRONES: tuple[str, ...] = (
    "cuadrado magico",      # acertijo aritmetico, no geometria
    "cubo de un numero",    # potencia, no cuerpo geometrico
)

PALABRAS_CLAVE: dict[str, tuple[str, ...]] = {
    "numeros": (
        "entero", "fraccion", "decimal", "porcentaje", "razon", "proporcion",
        "potencia", "raiz", "numero racional", "irracional", "divisor", "multiplo",
        "recta numerica", "valor absoluto", "descuento", "interes", "primo",
        "%", "por ciento", "resultado de", "el doble", "el triple", "quintuplo",
        "mitad", "tercera parte", "cuarta parte", "ganancia", "precio", "$",
        "notacion cientifica", "cuantas veces", "cual es el valor de",
    ),
    "algebra_y_funciones": (
        "ecuacion", "inecuacion", "sistema de ecuaciones", "funcion", "lineal",
        "cuadratica", "expresion algebraica", "producto notable", "factoriz",
        "pendiente", "variable", "grafico de la funcion", "dominio", "recorrido",
        "sucesion", "termino general", "modelo", "x =", "f(x)", "x2",
        "expresion", "representa la frase", "incognita", "despejar", "grafica de",
    ),
    "geometria": (
        "triangulo", "cuadrado", "rectangulo", "circulo", "circunferencia",
        "area", "perimetro", "volumen", "cubo", "cilindro", "cono", "esfera",
        "angulo", "pitagoras", "semejanza", "congruencia", "traslacion",
        "rotacion", "reflexion", "simetria", "plano cartesiano", "vector",
        "poligono", "diagonal", "altura", "arista", "vertice", "cara",
    ),
    "probabilidad_y_estadistica": (
        "probabilidad", "media", "promedio", "mediana", "moda", "rango",
        "cuartil", "percentil", "desviacion", "muestra", "poblacion",
        "diagrama de caja", "grafico de barras", "histograma", "frecuencia",
        "tabla de frecuencia", "dado", "moneda", "azar", "evento", "suceso",
        "encuesta", "dispersion",
    ),
}


def normalizar(texto: str) -> str:
    """Minusculas sin tildes, para comparar sin depender de la acentuacion."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes.lower())


def _sin_antipatrones(normalizado: str) -> str:
    for frase in ANTIPATRONES:
        normalizado = normalizado.replace(frase, " ")
    return normalizado


def puntajes_por_eje(texto: str) -> dict[str, int]:
    normalizado = _sin_antipatrones(normalizar(texto))
    return {
        eje: sum(normalizado.count(clave) for clave in claves)
        for eje, claves in PALABRAS_CLAVE.items()
    }


def clasificar(texto: str) -> str:
    """Devuelve el eje tematico mas probable, o EJE_DESCONOCIDO si no hay senal."""
    return clasificar_con_evidencia(texto)[0]


def clasificar_con_evidencia(texto: str) -> tuple[str, list[str]]:
    """Como `clasificar`, pero devuelve tambien las palabras que lo decidieron.

    La evidencia viaja hasta la respuesta del servidor a proposito: una
    heuristica de palabras clave se equivoca (un "cuadrado magico" no es
    geometria), y mostrar en que se baso permite al tutor y al estudiante
    descartarla cuando no corresponde, en vez de tomarla como un hecho.
    """
    normalizado = _sin_antipatrones(normalizar(texto))
    puntajes = puntajes_por_eje(texto)
    mejor = max(puntajes, key=lambda eje: puntajes[eje])
    if puntajes[mejor] == 0:
        return EJE_DESCONOCIDO, []
    evidencia = sorted(c for c in PALABRAS_CLAVE[mejor] if c in normalizado)
    return mejor, evidencia


def ejes_validos() -> list[str]:
    return [*PALABRAS_CLAVE, EJE_DESCONOCIDO]
