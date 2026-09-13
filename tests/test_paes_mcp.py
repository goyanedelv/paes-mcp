"""Pruebas del nucleo del servidor (no requieren el SDK de MCP instalado)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paes_mcp import activos, ejes, ensayos, pistas, puntajes
from paes_mcp.catalogo import CATALOGO, PruebaDesconocida
from paes_mcp.progreso import Progreso
from paes_mcp.repositorio import PreguntaNoEncontrada, RepositorioPreguntas

ID_GEOMETRIA = "PAES_2024_M1_Q45"


@pytest.fixture(scope="module")
def repo() -> RepositorioPreguntas:
    return RepositorioPreguntas("m1")


@pytest.fixture()
def progreso(tmp_path: Path) -> Progreso:
    return Progreso(tmp_path / "progreso.sqlite")


# --------------------------------------------------------------------- catalogo


def test_catalogo_expone_m1():
    assert "m1" in CATALOGO.ids()
    assert CATALOGO.obtener("m1").dataset_disponible


def test_catalogo_rechaza_prueba_desconocida():
    with pytest.raises(PruebaDesconocida):
        CATALOGO.obtener("prueba-inexistente")


def test_plantilla_no_se_carga_como_prueba():
    assert "_plantilla" not in CATALOGO.ids()


# ------------------------------------------------------------------ anti-spoiler


def test_la_ficha_nunca_incluye_la_clave(repo: RepositorioPreguntas):
    ficha = json.dumps(repo.obtener(ID_GEOMETRIA).ficha(), ensure_ascii=False).lower()
    assert "alternativa_correcta" not in ficha
    assert '"clave"' not in ficha


def test_el_resumen_de_busqueda_no_incluye_la_clave(repo: RepositorioPreguntas):
    _, preguntas = repo.buscar(limite=5)
    for pregunta in preguntas:
        assert "correcta" not in json.dumps(pregunta.resumen(), ensure_ascii=False).lower()


def test_la_pista_no_consulta_ni_revela_la_clave(repo: RepositorioPreguntas):
    pregunta = repo.obtener(ID_GEOMETRIA)
    for nivel in (1, 2, 3):
        texto = json.dumps(pistas.generar(pregunta, nivel), ensure_ascii=False).lower()
        assert "correcta" not in texto.replace("la alternativa correcta.", "")


def test_clave_oficial_disponible_solo_bajo_demanda(repo: RepositorioPreguntas):
    assert repo.clave_oficial(ID_GEOMETRIA) in ("A", "B", "C", "D")


# -------------------------------------------------------------------- busquedas


def test_busqueda_por_termino_y_diagrama(repo: RepositorioPreguntas):
    total, preguntas = repo.buscar(termino_busqueda="probabilidad", limite=3)
    assert total >= len(preguntas) > 0
    _, con_figura = repo.buscar(requiere_diagrama=True, limite=4)
    assert con_figura and all(p.tiene_diagrama for p in con_figura)


def test_busqueda_excluye_pilotos_por_defecto(repo: RepositorioPreguntas):
    _, preguntas = repo.buscar(limite=20)
    assert not any(p.es_piloto for p in preguntas)


def test_pregunta_inexistente(repo: RepositorioPreguntas):
    with pytest.raises(PreguntaNoEncontrada):
        repo.obtener("PAES_1999_M1_Q99")


def test_cobertura_distingue_lo_no_publicado_de_lo_pendiente(repo: RepositorioPreguntas):
    """2025 y 2026 tienen 45 items porque el DEMRE publico solo 45, no por una
    transcripcion incompleta: no debe quedar nada pendiente de transcribir."""
    por_anio = {a["anio"]: a for a in repo.estadisticas()["preguntas_por_anio"]}
    assert por_anio[2024]["preguntas"] == 65
    assert not por_anio[2024]["no_publicados_por_el_demre"]
    for anio in (2025, 2026):
        datos = por_anio[anio]
        assert datos["preguntas"] == 45
        assert len(datos["no_publicados_por_el_demre"]) == 20
        assert datos["pendientes_de_transcribir"] == []
        assert datos["preguntas"] + len(datos["no_publicados_por_el_demre"]) == datos["items_oficiales"]


def test_ningun_item_no_publicado_esta_en_el_dataset(repo: RepositorioPreguntas):
    """Blindaje contra items inventados: lo que el DEMRE no publico no puede aparecer."""
    for anio in (2025, 2026):
        numeros = {p.numero for p in repo.buscar(anio=anio, excluir_pilotos=False, limite=65)[1]}
        assert not numeros & set(repo.spec.items_no_publicados(anio))


# ----------------------------------------------------------------------- ejes


def test_los_antipatrones_neutralizan_palabras_enganosas():
    """'cuadrado magico' es aritmetica; la palabra 'cuadrado' no debe arrastrarla a geometria."""
    assert "cuadrado" not in ejes.clasificar_con_evidencia("un cuadrado magico de 3x3")[1]


def test_la_clasificacion_expone_su_evidencia():
    """El tutor debe poder ver en que se baso el eje para descartarlo si no corresponde."""
    eje, evidencia = ejes.clasificar_con_evidencia("calcula el area del triangulo")
    assert eje == "geometria" and {"area", "triangulo"} <= set(evidencia)
    assert ejes.clasificar_con_evidencia("texto sin senal matematica") == (ejes.EJE_DESCONOCIDO, [])


def test_la_ficha_muestra_la_evidencia_del_eje(repo: RepositorioPreguntas):
    ficha = repo.obtener(ID_GEOMETRIA).ficha()
    assert ficha["clasificacion_eje"] == "heuristica"
    assert ficha["palabras_que_decidieron_el_eje"]


def test_clasificacion_heuristica_es_estable():
    assert ejes.clasificar("El area del triangulo y su perimetro") == "geometria"
    assert ejes.clasificar("la probabilidad de obtener un dado") == "probabilidad_y_estadistica"
    assert ejes.clasificar("") == ejes.EJE_DESCONOCIDO


# -------------------------------------------------------------------- puntajes


def test_puntaje_se_declara_estimado_si_no_hay_tabla_oficial():
    resultado = puntajes.calcular(50, "m1", 2024)
    assert resultado["puntaje_paes"] == 811
    assert resultado["es_oficial"] is False
    assert resultado["advertencias"]


def test_puntaje_interpola_de_forma_monotona():
    valores = [puntajes.calcular(n, "m1", 2024)["puntaje_paes"] for n in range(0, 61)]
    assert valores == sorted(valores)
    assert valores[0] == 100 and valores[-1] == 1000


def test_puntaje_acota_correctas_fuera_de_rango():
    resultado = puntajes.calcular(99, "m1", 2024)
    assert resultado["puntaje_paes"] == 1000
    assert any("acotado" in a for a in resultado["advertencias"])


# -------------------------------------------------------------------- progreso


def test_registro_de_intentos_y_bitacora(progreso: Progreso):
    progreso.registrar_intento("m1", ID_GEOMETRIA, "B", False, 40, 1, "geometria")
    progreso.registrar_intento("m1", ID_GEOMETRIA, "A", True, 30, 0, "geometria")
    resumen = progreso.resumen("m1")
    assert resumen["total_intentos"] == 2 and resumen["aciertos"] == 1
    assert progreso.pendientes("m1")[0]["estado_dominio"] == "en_repaso"


def test_reinicio_borra_historial(progreso: Progreso):
    progreso.registrar_intento("m1", ID_GEOMETRIA, "A", True, 10, 0, "geometria")
    progreso.reiniciar("m1")
    assert progreso.resumen("m1")["total_intentos"] == 0


# --------------------------------------------------------------------- ensayos


def test_ensayo_genera_sesion_y_preguntas(progreso: Progreso):
    ensayo = ensayos.generar("m1", "minisensayo", progreso=progreso)
    assert ensayo["cantidad"] == 15
    assert ensayo["sesion_id"].startswith("m1-minisensayo-")
    assert len({p["id_unico"] for p in ensayo["preguntas"]}) == 15


def test_ensayo_focalizado_prioriza_ejes_debiles(progreso: Progreso):
    for _ in range(3):
        progreso.registrar_intento("m1", ID_GEOMETRIA, "B", False, 40, 0, "geometria")
    ensayo = ensayos.generar("m1", "focalizado", cantidad=5, progreso=progreso)
    assert ensayo["preguntas"] and ensayo["preguntas"][0]["eje_tematico"] == "geometria"


def test_modalidad_invalida(progreso: Progreso):
    with pytest.raises(ValueError):
        ensayos.generar("m1", "modalidad-inventada", progreso=progreso)


# ---------------------------------------------------------------------- activos


def test_activo_visual_existe_y_es_png(repo: RepositorioPreguntas):
    pregunta = repo.obtener(ID_GEOMETRIA)
    ruta = activos.ruta_de_recurso(repo.spec, pregunta, "enunciado")
    assert activos.leer_bytes(ruta).startswith(b"\x89PNG")


def test_activo_fuera_del_arbol_se_rechaza(repo: RepositorioPreguntas):
    with pytest.raises(activos.ActivoNoDisponible):
        activos.resolver(repo.spec, "../../etc/passwd")
    with pytest.raises(activos.ActivoNoDisponible):
        activos.resolver(repo.spec, "/etc/passwd")
