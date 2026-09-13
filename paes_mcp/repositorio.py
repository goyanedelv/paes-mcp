"""Acceso de solo lectura al dataset de preguntas.

Regla de oro del proyecto (diseno anti-spoiler): las funciones que arman la
ficha de una pregunta para el modelo NUNCA incluyen la alternativa correcta.
La clave solo sale del servidor a traves de `clave_oficial()`, que se invoca
unicamente al verificar una respuesta ya emitida por el estudiante.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable

from .catalogo import CATALOGO, Catalogo, EspecificacionPrueba
from .ejes import clasificar, normalizar

LETRAS = ("A", "B", "C", "D", "E")


class PreguntaNoEncontrada(KeyError):
    """No existe una pregunta con ese identificador en la prueba indicada."""


@dataclass(frozen=True)
class Alternativa:
    letra: str
    texto: str
    imagen_uri: str | None
    imagen_ruta_relativa: str | None


@dataclass(frozen=True)
class Pregunta:
    """Ficha completa de un item, sin la clave de correccion."""

    prueba: str
    id_unico: str
    anio: int
    fuente: str
    disciplina: str
    forma: str
    numero: int
    es_piloto: bool
    pagina_pdf: int | None
    enunciado: str
    tiene_diagrama: bool
    imagen_enunciado: str | None
    imagen_completa: str | None
    alternativas: tuple[Alternativa, ...]
    eje_tematico: str

    @property
    def opciones_visuales(self) -> bool:
        return any(alt.imagen_uri for alt in self.alternativas)

    def uri(self, recurso: str) -> str:
        return f"paes://{self.prueba}/imagenes/{self.anio}/{self.id_unico}/{recurso}"

    def resumen(self) -> dict[str, Any]:
        return {
            "prueba": self.prueba,
            "id_unico": self.id_unico,
            "anio": self.anio,
            "numero": self.numero,
            "enunciado_resumen": (self.enunciado[:160] + "...") if len(self.enunciado) > 160 else self.enunciado,
            "eje_tematico": self.eje_tematico,
            "clasificacion_eje": "heuristica",
            "tiene_diagrama": self.tiene_diagrama,
            "opciones_visuales": self.opciones_visuales,
            "es_piloto": self.es_piloto,
        }

    def ficha(self) -> dict[str, Any]:
        """Ficha para el estudiante: todo menos la clave."""
        return {
            "prueba": self.prueba,
            "id_unico": self.id_unico,
            "anio": self.anio,
            "fuente_oficial": self.fuente,
            "disciplina": self.disciplina,
            "forma": self.forma,
            "numero": self.numero,
            "pagina_pdf": self.pagina_pdf,
            "es_piloto": self.es_piloto,
            "eje_tematico": self.eje_tematico,
            "clasificacion_eje": "heuristica",
            "enunciado": self.enunciado,
            "tiene_diagrama": self.tiene_diagrama,
            "uri_diagrama": self.uri("enunciado") if self.tiene_diagrama else None,
            "uri_pregunta_completa": self.uri("completa") if self.imagen_completa else None,
            "alternativas": [
                {"letra": a.letra, "texto": a.texto, "imagen_uri": a.imagen_uri}
                for a in self.alternativas
            ],
            "nota_anti_spoiler": (
                "La alternativa correcta permanece en el servidor. Use "
                "'paes_verificar_respuesta' despues de que el estudiante responda."
            ),
        }


def _bool(valor: Any) -> bool:
    return bool(valor) and str(valor) not in ("0", "", "None")


def _texto(valor: Any) -> str:
    return (valor or "").strip()


class RepositorioPreguntas:
    """Consulta facetada sobre el SQLite de una prueba."""

    def __init__(self, prueba: str | None = None, catalogo: Catalogo | None = None) -> None:
        self.spec: EspecificacionPrueba = (catalogo or CATALOGO).obtener(prueba)
        self.spec.exigir_disponible()

    def _conectar(self) -> sqlite3.Connection:
        con = sqlite3.connect(f"file:{self.spec.ruta_sqlite}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        return con

    def _fila_a_pregunta(self, fila: sqlite3.Row) -> Pregunta:
        cols = fila.keys()
        alternativas: list[Alternativa] = []
        for letra in LETRAS:
            col_texto = f"alternativa_{letra.lower()}_texto"
            col_imagen = f"alternativa_{letra.lower()}_imagen"
            if col_texto not in cols:
                continue
            texto = _texto(fila[col_texto])
            imagen = _texto(fila[col_imagen]) if col_imagen in cols else ""
            if not texto and not imagen:
                continue
            id_unico = fila["id_unico"]
            anio = fila["año"] if "año" in cols else fila["anio"]
            alternativas.append(
                Alternativa(
                    letra=letra,
                    texto=texto,
                    imagen_uri=(
                        f"paes://{self.spec.id}/imagenes/{anio}/{id_unico}/opcion/{letra}"
                        if imagen
                        else None
                    ),
                    imagen_ruta_relativa=imagen or None,
                )
            )
        enunciado = _texto(fila["enunciado_pregunta"])
        material = " ".join([enunciado, *(a.texto for a in alternativas)])
        return Pregunta(
            prueba=self.spec.id,
            id_unico=fila["id_unico"],
            anio=fila["año"] if "año" in cols else fila["anio"],
            fuente=_texto(fila["fuente"]) if "fuente" in cols else "",
            disciplina=_texto(fila["disciplina"]) if "disciplina" in cols else self.spec.disciplina,
            forma=_texto(fila["forma"]) if "forma" in cols else "",
            numero=fila["numero_en_fuente"] if "numero_en_fuente" in cols else 0,
            es_piloto=_bool(fila["es_piloto"]) if "es_piloto" in cols else False,
            pagina_pdf=fila["pagina_pdf"] if "pagina_pdf" in cols else None,
            enunciado=enunciado,
            tiene_diagrama=_bool(fila["tiene_imagen_enunciado"]) if "tiene_imagen_enunciado" in cols else False,
            imagen_enunciado=_texto(fila["imagen_enunciado"]) or None,
            imagen_completa=_texto(fila["imagen_pregunta_completa"]) or None,
            alternativas=tuple(alternativas),
            eje_tematico=clasificar(material),
        )

    # ---------------------------------------------------------------- consultas

    def obtener(self, id_unico: str) -> Pregunta:
        with self._conectar() as con:
            fila = con.execute(
                f"SELECT * FROM {self.spec.tabla} WHERE id_unico = ?", (id_unico,)
            ).fetchone()
        if fila is None:
            raise PreguntaNoEncontrada(
                f"No existe la pregunta '{id_unico}' en la prueba '{self.spec.id}'."
            )
        return self._fila_a_pregunta(fila)

    def clave_oficial(self, id_unico: str) -> str:
        """Devuelve la clave del clavijero oficial. Uso exclusivo de la correccion."""
        with self._conectar() as con:
            fila = con.execute(
                f"SELECT alternativa_correcta FROM {self.spec.tabla} WHERE id_unico = ?",
                (id_unico,),
            ).fetchone()
        if fila is None:
            raise PreguntaNoEncontrada(
                f"No existe la pregunta '{id_unico}' en la prueba '{self.spec.id}'."
            )
        return _texto(fila["alternativa_correcta"]).upper()

    def buscar(
        self,
        anio: int | None = None,
        termino_busqueda: str | None = None,
        eje_tematico: str | None = None,
        requiere_diagrama: bool | None = None,
        opciones_visuales: bool | None = None,
        excluir_pilotos: bool = True,
        excluir_ids: Iterable[str] = (),
        limite: int = 5,
        orden: str = "numero",
    ) -> tuple[int, list[Pregunta]]:
        clausulas: list[str] = []
        params: list[Any] = []
        if anio is not None:
            clausulas.append("año = ?")
            params.append(anio)
        if excluir_pilotos:
            clausulas.append("COALESCE(es_piloto, 0) = 0")
        if requiere_diagrama is not None:
            clausulas.append(
                "COALESCE(tiene_imagen_enunciado, 0) = ?" if requiere_diagrama else
                "COALESCE(tiene_imagen_enunciado, 0) = 0"
            )
            if requiere_diagrama:
                params.append(1)
        where = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        orden_sql = "RANDOM()" if orden == "aleatorio" else "año, numero_en_fuente"
        with self._conectar() as con:
            filas = con.execute(
                f"SELECT * FROM {self.spec.tabla} {where} ORDER BY {orden_sql}", params
            ).fetchall()

        excluidos = set(excluir_ids)
        termino = normalizar(termino_busqueda) if termino_busqueda else None
        resultados: list[Pregunta] = []
        for fila in filas:
            pregunta = self._fila_a_pregunta(fila)
            if pregunta.id_unico in excluidos:
                continue
            if termino:
                material = normalizar(
                    " ".join([pregunta.enunciado, *(a.texto for a in pregunta.alternativas)])
                )
                if termino not in material:
                    continue
            if eje_tematico and pregunta.eje_tematico != eje_tematico:
                continue
            if opciones_visuales is not None and pregunta.opciones_visuales != opciones_visuales:
                continue
            resultados.append(pregunta)
        return len(resultados), resultados[: max(0, limite)]

    def estadisticas(self) -> dict[str, Any]:
        """Cobertura real del dataset local, por anio."""
        with self._conectar() as con:
            filas = con.execute(f"SELECT * FROM {self.spec.tabla}").fetchall()
        preguntas = [self._fila_a_pregunta(f) for f in filas]
        por_anio: dict[int, dict[str, Any]] = {}
        for p in preguntas:
            d = por_anio.setdefault(
                p.anio,
                {"anio": p.anio, "preguntas": 0, "pilotos": 0, "con_diagrama": 0,
                 "con_opciones_visuales": 0, "ejes": {}, "numeros": set()},
            )
            d["numeros"].add(p.numero)
            d["preguntas"] += 1
            d["pilotos"] += int(p.es_piloto)
            d["con_diagrama"] += int(p.tiene_diagrama)
            d["con_opciones_visuales"] += int(p.opciones_visuales)
            d["ejes"][p.eje_tematico] = d["ejes"].get(p.eje_tematico, 0) + 1
        for anio, d in por_anio.items():
            numeros = d.pop("numeros")
            no_publicados = self.spec.items_no_publicados(anio)
            oficiales = (
                self.spec.cobertura_publicada.get(str(anio), {}).get("items_oficiales")
                or self.spec.estructura.preguntas_totales
            )
            # Ausentes del dataset que TAMPOCO estan en el cuadernillo oficial:
            # no son deuda de transcripcion, no existen en ninguna fuente publica.
            faltantes = [
                n for n in range(1, oficiales + 1)
                if n not in numeros and n not in no_publicados
            ]
            d["items_oficiales"] = oficiales
            d["no_publicados_por_el_demre"] = no_publicados
            d["pendientes_de_transcribir"] = faltantes
            d["cobertura"] = (
                "completa respecto del cuadernillo publicado" if not faltantes
                else f"faltan {len(faltantes)} items presentes en el cuadernillo oficial"
            )

        return {
            "prueba": self.spec.id,
            "nombre": self.spec.nombre,
            "total_preguntas": len(preguntas),
            "preguntas_por_anio": [por_anio[a] for a in sorted(por_anio)],
            "nota_cobertura": self.spec.cobertura_publicada.get("_meta", {}).get("nota", ""),
            "clasificacion_eje": "heuristica (no oficial)",
            "fuente_oficial": dict(self.spec.fuente_oficial),
        }

    def anios(self) -> list[int]:
        with self._conectar() as con:
            return [f[0] for f in con.execute(
                f"SELECT DISTINCT año FROM {self.spec.tabla} ORDER BY año"
            )]
