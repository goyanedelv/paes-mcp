"""Servidor MCP `paes-tutor`: tutoria deterministica sobre material oficial PAES.

Principios de diseno:
  * Anti-spoiler: la clave de correccion solo sale por `paes_verificar_respuesta`.
  * Determinismo: el clavijero y el material grafico mandan; el LLM solo guia.
  * Multi-prueba: toda herramienta acepta `prueba` (por defecto, M1).
  * Transparencia: cada salida declara si es material oficial, dato derivado o
    andamiaje generado por el servidor.
"""

from __future__ import annotations

import json
from typing import Any

from . import __version__, activos, ensayos, pistas, plantillas, puntajes
from .catalogo import CATALOGO, PruebaDesconocida, PruebaNoDisponible
from .compat import Image, VERSION_SDK, crear_servidor
from .config import CONFIG
from .ejes import ejes_validos
from .progreso import Progreso
from .repositorio import PreguntaNoEncontrada, RepositorioPreguntas

INSTRUCCIONES = """\
Servidor MCP libre para estudiar las pruebas PAES (Chile) con material oficial
y gratuito del DEMRE.

Reglas de uso para el modelo:
1. Nunca declares cual es la alternativa correcta antes de llamar a
   'paes_verificar_respuesta'; el servidor retiene la clave a proposito.
2. Prefiere 'paes_solicitar_pista' antes que resolver el ejercicio tu mismo.
3. Los ejes tematicos son una clasificacion heuristica del servidor, no oficial.
4. Los puntajes pueden ser estimados: respeta el campo 'es_oficial' al informarlos.
"""

servidor = crear_servidor(
    name="paes-tutor",
    title="Tutor PAES (open source)",
    version=__version__,
    instructions=INSTRUCCIONES,
)

_progreso: Progreso | None = None


def _progreso_estudiante() -> Progreso:
    global _progreso
    if _progreso is None:
        _progreso = Progreso()
    return _progreso


def _repo(prueba: str | None) -> RepositorioPreguntas:
    return RepositorioPreguntas(prueba)


def _error(mensaje: str, **extra: Any) -> dict[str, Any]:
    return {"error": mensaje, **extra}


def _mensaje(exc: Exception) -> str:
    """KeyError repr-ea su argumento; aqui se recupera el texto limpio."""
    return str(exc.args[0]) if exc.args else str(exc)


def _manejar(fn, *args: Any, **kwargs: Any) -> Any:
    """Traduce las excepciones de dominio a respuestas legibles para el modelo."""
    try:
        return fn(*args, **kwargs)
    except (PruebaDesconocida, PruebaNoDisponible) as exc:
        return _error(_mensaje(exc), pruebas_disponibles=CATALOGO.ids())
    except PreguntaNoEncontrada as exc:
        return _error(_mensaje(exc))
    except (ValueError, LookupError, activos.ActivoNoDisponible) as exc:
        return _error(str(exc))


# ---------------------------------------------------------------------- tools


@servidor.tool(
    description="Lista las pruebas PAES soportadas por este servidor y si su dataset local esta disponible."
)
def paes_listar_pruebas() -> dict[str, Any]:
    return {
        "prueba_por_defecto": CONFIG.prueba_por_defecto,
        "pruebas": [spec.resumen() for spec in CATALOGO.todas()],
        "como_agregar_una_prueba": "docs/AGREGAR_PRUEBA.md",
    }


@servidor.tool(
    description="Busca preguntas oficiales por anio, texto, eje tematico o rasgos visuales. No devuelve claves."
)
def paes_buscar_preguntas(
    prueba: str | None = None,
    anio: int | None = None,
    termino_busqueda: str | None = None,
    eje_tematico: str | None = None,
    requiere_diagrama: bool | None = None,
    opciones_visuales: bool | None = None,
    excluir_pilotos: bool = True,
    limite: int = 5,
    aleatorio: bool = False,
) -> dict[str, Any]:
    def _accion() -> dict[str, Any]:
        if eje_tematico and eje_tematico not in ejes_validos():
            raise ValueError(
                f"Eje tematico '{eje_tematico}' no valido. Opciones: {', '.join(ejes_validos())}."
            )
        repo = _repo(prueba)
        total, preguntas = repo.buscar(
            anio=anio,
            termino_busqueda=termino_busqueda,
            eje_tematico=eje_tematico,
            requiere_diagrama=requiere_diagrama,
            opciones_visuales=opciones_visuales,
            excluir_pilotos=excluir_pilotos,
            limite=min(max(limite, 1), 20),
            orden="aleatorio" if aleatorio else "numero",
        )
        return {
            "prueba": repo.spec.id,
            "total_encontradas": total,
            "devueltas": len(preguntas),
            "preguntas": [p.resumen() for p in preguntas],
            "nota": "Las claves de correccion no se entregan en la busqueda.",
        }

    return _manejar(_accion)


@servidor.tool(
    description=(
        "Entrega el enunciado, las alternativas y los diagramas de una pregunta. "
        "NUNCA incluye la alternativa correcta (diseno anti-spoiler)."
    )
)
def paes_obtener_pregunta(
    id_unico: str,
    prueba: str | None = None,
    incluir_imagenes: bool = True,
) -> Any:
    def _accion() -> Any:
        repo = _repo(prueba)
        pregunta = repo.obtener(id_unico)
        ficha = pregunta.ficha()
        if not incluir_imagenes:
            return ficha

        bloques: list[Any] = [json.dumps(ficha, ensure_ascii=False, indent=2)]
        recursos = []
        if pregunta.tiene_diagrama and pregunta.imagen_enunciado:
            recursos.append("enunciado")
        elif pregunta.imagen_completa:
            recursos.append("completa")
        recursos += [
            f"opcion/{a.letra}" for a in pregunta.alternativas if a.imagen_ruta_relativa
        ]
        for recurso in recursos:
            try:
                ruta = activos.ruta_de_recurso(repo.spec, pregunta, recurso)
            except activos.ActivoNoDisponible:
                continue
            bloques.append(Image(data=activos.leer_bytes(ruta), format="png"))
        return bloques

    return _manejar(_accion)


@servidor.tool(
    description=(
        "Corrige la respuesta del estudiante contra el clavijero oficial y registra el intento. "
        "Unica via por la que el servidor revela la clave."
    )
)
def paes_verificar_respuesta(
    id_unico: str,
    alternativa_seleccionada: str,
    prueba: str | None = None,
    tiempo_segundos: int | None = None,
    nivel_pista_usada: int = 0,
    sesion_id: str | None = None,
) -> dict[str, Any]:
    def _accion() -> dict[str, Any]:
        repo = _repo(prueba)
        pregunta = repo.obtener(id_unico)
        elegida = (alternativa_seleccionada or "").strip().upper()
        validas = [a.letra for a in pregunta.alternativas]
        if elegida not in validas:
            raise ValueError(
                f"Alternativa '{alternativa_seleccionada}' no valida. Opciones: {', '.join(validas)}."
            )
        clave = repo.clave_oficial(id_unico)
        acierto = elegida == clave
        _progreso_estudiante().registrar_intento(
            prueba=repo.spec.id,
            id_unico=id_unico,
            alternativa=elegida,
            acierto=acierto,
            tiempo_segundos=tiempo_segundos,
            nivel_pista_usada=nivel_pista_usada,
            eje_tematico=pregunta.eje_tematico,
            sesion_id=sesion_id,
        )
        return {
            "prueba": repo.spec.id,
            "id_unico": id_unico,
            "acierto": acierto,
            "alternativa_seleccionada": elegida,
            "alternativa_correcta": clave,
            "fuente_clave": f"clavijero oficial publicado ({pregunta.fuente})",
            "es_piloto": pregunta.es_piloto,
            "eje_tematico": pregunta.eje_tematico,
            "intento_registrado": True,
            "sugerencia_pedagogica": (
                "Pide al estudiante que explique su procedimiento y refuerza el paso que lo llevo al acierto."
                if acierto
                else "No entregues la resolucion completa de inmediato: pidele que reconstruya su razonamiento "
                     "y contrasta donde se desvio."
            ),
        }

    return _manejar(_accion)


@servidor.tool(
    description=(
        "Entrega andamiaje socratico graduado (1 concepto, 2 planteamiento, 3 primer paso) "
        "sin revelar ni insinuar la alternativa correcta."
    )
)
def paes_solicitar_pista(
    id_unico: str, nivel_pista: int = 1, prueba: str | None = None
) -> dict[str, Any]:
    def _accion() -> dict[str, Any]:
        repo = _repo(prueba)
        return pistas.generar(repo.obtener(id_unico), nivel_pista)

    return _manejar(_accion)


@servidor.tool(
    description=(
        "Convierte respuestas correctas a la escala PAES (100-1000). Declara si el valor es "
        "oficial o estimado por interpolacion."
    )
)
def paes_calcular_puntaje(
    respuestas_correctas: int, prueba: str | None = None, anio: int | None = None
) -> dict[str, Any]:
    return _manejar(puntajes.calcular, respuestas_correctas, prueba, anio)


@servidor.tool(
    description=(
        "Arma una sesion de practica: 'completo', 'minisensayo', 'focalizado' (por ejes debiles) "
        "o 'repaso_errores'. Devuelve un sesion_id para registrar los intentos."
    )
)
def paes_generar_ensayo(
    modalidad: str = "minisensayo",
    prueba: str | None = None,
    anio_referencia: int | None = None,
    cantidad: int | None = None,
    semilla: int | None = None,
) -> dict[str, Any]:
    return _manejar(
        ensayos.generar,
        prueba=prueba,
        modalidad=modalidad,
        anio_referencia=anio_referencia,
        cantidad=cantidad,
        semilla=semilla,
        progreso=_progreso_estudiante(),
    )


@servidor.tool(
    description="Resumen local del rendimiento del estudiante: aciertos, tiempos y desempeno por eje tematico."
)
def paes_resumen_progreso(prueba: str | None = None) -> dict[str, Any]:
    return _progreso_estudiante().resumen(prueba)


@servidor.tool(
    description="Preguntas falladas pendientes de refuerzo, ordenadas por prioridad de repaso."
)
def paes_preguntas_pendientes(prueba: str | None = None, limite: int = 20) -> dict[str, Any]:
    pendientes = _progreso_estudiante().pendientes(prueba, min(max(limite, 1), 100))
    return {"prueba": prueba, "total": len(pendientes), "pendientes": pendientes}


@servidor.tool(
    description="Borra el historial local del estudiante. Requiere confirmar explicitamente."
)
def paes_reiniciar_progreso(confirmar: bool = False, prueba: str | None = None) -> dict[str, Any]:
    if not confirmar:
        return _error(
            "Operacion no ejecutada: vuelva a llamar con confirmar=true para borrar el historial local."
        )
    return {**_progreso_estudiante().reiniciar(prueba), "prueba": prueba}


@servidor.tool(
    description="Cobertura real del dataset local por anio: preguntas, pilotos, diagramas y ejes."
)
def paes_estado_dataset(prueba: str | None = None) -> dict[str, Any]:
    def _accion() -> dict[str, Any]:
        repo = _repo(prueba)
        estado = repo.estadisticas()
        estado["estructura_oficial"] = repo.spec.resumen()["estructura_oficial"]
        estado["advertencia_cobertura"] = (
            "El dataset local puede no cubrir la totalidad de cada prueba oficial; "
            "revise 'preguntas_por_anio' antes de interpretar un ensayo como completo."
        )
        return estado

    return _manejar(_accion)


@servidor.tool(
    description=(
        "Procedencia del material, licencia del software y alcance del proyecto. "
        "Uselo cuando el estudiante pregunte de donde salen las preguntas."
    )
)
def paes_procedencia_y_licencia() -> dict[str, Any]:
    return {
        "software": {
            "licencia": "MIT",
            "codigo_abierto": True,
            "gratuito": True,
            "version": __version__,
            "sdk_mcp": VERSION_SDK,
        },
        "contenido": {
            "origen": "Publicaciones oficiales, gratuitas y de acceso publico del DEMRE (Universidad de Chile).",
            "url_fuente": "https://demre.cl/publicaciones/",
            "uso": "Fines educativos y de estudio personal, sin animo de lucro.",
            "no_incluye": [
                "Material de preuniversitarios u otras editoriales.",
                "Resoluciones o solucionarios de terceros.",
                "Tablas de puntaje reproducidas sin fuente oficial verificable.",
            ],
            "derechos": (
                "Las pruebas y sus claves son obra del DEMRE / Universidad de Chile. Este proyecto "
                "no reclama derechos sobre ellas, las cita con atribucion y atiende solicitudes de retiro."
            ),
            "contacto_retiro": "Abra un issue en el repositorio del proyecto.",
        },
        "privacidad": {
            "datos_del_estudiante": str(CONFIG.progreso_db),
            "telemetria_remota": False,
        },
        "afiliacion_oficial": False,
        "aviso": "Proyecto independiente. No esta afiliado ni patrocinado por el DEMRE ni por ninguna universidad.",
    }


# ------------------------------------------------------------------ resources


@servidor.resource(
    "paes://pruebas",
    name="catalogo_de_pruebas",
    description="Catalogo de pruebas soportadas por el servidor.",
    mime_type="application/json",
)
def recurso_pruebas() -> str:
    return json.dumps(paes_listar_pruebas(), ensure_ascii=False, indent=2)


@servidor.resource(
    "paes://proyecto/licencia",
    name="licencia_y_procedencia",
    description="Licencia del software y procedencia del material oficial.",
    mime_type="application/json",
)
def recurso_licencia() -> str:
    return json.dumps(paes_procedencia_y_licencia(), ensure_ascii=False, indent=2)


@servidor.resource(
    "paes://{prueba}/preguntas/{id_unico}",
    name="ficha_de_pregunta",
    description="Ficha JSON de una pregunta, sin la clave de correccion.",
    mime_type="application/json",
)
def recurso_pregunta(prueba: str, id_unico: str) -> str:
    resultado = _manejar(lambda: _repo(prueba).obtener(id_unico).ficha())
    return json.dumps(resultado, ensure_ascii=False, indent=2)


@servidor.resource(
    "paes://{prueba}/imagenes/{anio}/{id_unico}/{recurso}",
    name="activo_visual",
    description="Recorte PNG del enunciado ('enunciado'), de la pregunta completa ('completa') o de una alternativa.",
    mime_type="image/png",
)
def recurso_imagen(prueba: str, anio: str, id_unico: str, recurso: str) -> bytes:
    repo = _repo(prueba)
    pregunta = repo.obtener(id_unico)
    return activos.leer_bytes(activos.ruta_de_recurso(repo.spec, pregunta, recurso))


@servidor.resource(
    "paes://{prueba}/tabla-puntaje/{anio}",
    name="tabla_de_puntaje",
    description="Tabla de conversion puntaje bruto -> escala PAES, con su estatus (oficial o referencial).",
    mime_type="application/json",
)
def recurso_tabla_puntaje(prueba: str, anio: str) -> str:
    def _accion() -> dict[str, Any]:
        tabla = puntajes.obtener_tabla(prueba, int(anio))
        return {"prueba": prueba, "anio": int(anio), **tabla.como_dict()}

    return json.dumps(_manejar(_accion), ensure_ascii=False, indent=2)


@servidor.resource(
    "paes://estudiante/resumen",
    name="resumen_del_estudiante",
    description="Metricas locales acumuladas del estudiante.",
    mime_type="application/json",
)
def recurso_resumen() -> str:
    return json.dumps(_progreso_estudiante().resumen(), ensure_ascii=False, indent=2)


@servidor.resource(
    "paes://estudiante/pendientes",
    name="bitacora_de_errores",
    description="Preguntas falladas pendientes de refuerzo.",
    mime_type="application/json",
)
def recurso_pendientes() -> str:
    return json.dumps(_progreso_estudiante().pendientes(), ensure_ascii=False, indent=2)


# -------------------------------------------------------------------- prompts


@servidor.prompt(description="Tutoria socratica: guia sin entregar la respuesta.")
def tutor_socratico(prueba: str | None = None, contexto: str = "sesion de estudio general") -> str:
    spec = CATALOGO.obtener(prueba) if (prueba or CONFIG.prueba_por_defecto) in CATALOGO else None
    nombre = spec.nombre if spec else "la prueba PAES seleccionada"
    return plantillas.TUTOR_SOCRATICO.format(nombre_prueba=nombre, contexto=contexto)


@servidor.prompt(description="Analiza los distractores de una pregunta ya verificada.")
def analisis_distractores(id_unico: str, prueba: str | None = None) -> str:
    spec = CATALOGO.obtener(prueba) if (prueba or CONFIG.prueba_por_defecto) in CATALOGO else None
    return plantillas.ANALISIS_DISTRACTORES.format(
        id_unico=id_unico, nombre_prueba=spec.nombre if spec else "PAES"
    )


@servidor.prompt(description="Modo ensayo cronometrado sin pistas.")
def simulacro(sesion_id: str, prueba: str | None = None) -> str:
    spec = CATALOGO.obtener(prueba) if (prueba or CONFIG.prueba_por_defecto) in CATALOGO else None
    return plantillas.SIMULACRO.format(
        nombre_prueba=spec.nombre if spec else "PAES", sesion_id=sesion_id
    )


@servidor.prompt(description="Plan de estudio basado en el progreso real del estudiante.")
def plan_de_estudio(dias: int = 14, prueba: str | None = None) -> str:
    spec = CATALOGO.obtener(prueba) if (prueba or CONFIG.prueba_por_defecto) in CATALOGO else None
    return plantillas.PLAN_DE_ESTUDIO.format(
        dias=dias, nombre_prueba=spec.nombre if spec else "PAES"
    )


def main() -> None:
    """Punto de entrada: transporte stdio por defecto."""
    import os

    transporte = os.environ.get("PAES_TRANSPORTE", "stdio")
    servidor.run(transport=transporte)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
