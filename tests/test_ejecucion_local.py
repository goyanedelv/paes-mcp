"""El servidor debe funcionar por completo como proceso local.

No es un servicio alojado: el cliente de IA lo lanza en la maquina del
estudiante y le habla por entrada y salida estandar. De ahi que el dataset, el
clavijero, las imagenes y el progreso vivan en disco propio y que el servidor no
deba contactar servicio externo alguno. Estas pruebas lo hacen exigible en lugar
de dejarlo como promesa de la documentacion.
"""

from __future__ import annotations

import socket

import pytest

from paes_mcp import server


class RedProhibida(RuntimeError):
    """Se intento contactar un servicio externo desde un servidor que es local."""


@pytest.fixture()
def sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inutiliza toda salida de red durante la prueba (se restaura al terminar).

    Asi, cualquier dependencia de un servicio remoto falla de inmediato en vez de
    pasar inadvertida.
    """

    def bloquear(*args: object, **kwargs: object) -> None:
        raise RedProhibida("el servidor intento salir a la red")

    for objetivo, atributo in (
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket, "gethostbyname"),
    ):
        monkeypatch.setattr(objetivo, atributo, bloquear)


def test_ciclo_de_estudio_completo_en_proceso_local(
    sin_red: None, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from paes_mcp.progreso import Progreso

    # El progreso se escribe en un SQLite temporal, no en el del usuario.
    monkeypatch.setattr(server, "_progreso", Progreso(tmp_path / "progreso.sqlite"))

    busqueda = server.paes_buscar_preguntas(requiere_diagrama=True, limite=2)
    assert busqueda["devueltas"] == 2

    bloques = server.paes_obtener_pregunta(id_unico="PAES_2024_M1_Q45")
    assert any(type(b).__name__ == "Image" for b in bloques)

    assert server.paes_solicitar_pista(id_unico="PAES_2024_M1_Q45", nivel_pista=2)["nivel_pista"] == 2

    verificacion = server.paes_verificar_respuesta(
        id_unico="PAES_2024_M1_Q45", alternativa_seleccionada="A"
    )
    assert verificacion["intento_registrado"] is True

    assert server.paes_calcular_puntaje(respuestas_correctas=42, anio=2024)["puntaje_paes"] > 100
    assert server.paes_generar_ensayo(modalidad="minisensayo")["cantidad"] == 15
    assert server.paes_resumen_progreso()["total_intentos"] == 1
    assert server.paes_estado_dataset()["total_preguntas"] == 155

    imagen = server.recurso_imagen("m1", "2024", "PAES_2024_M1_Q45", "enunciado")
    assert imagen.startswith(b"\x89PNG")


def test_el_codigo_no_importa_bibliotecas_de_red() -> None:
    """Un servidor local no necesita clientes HTTP ni sockets propios."""
    import pkgutil
    from pathlib import Path
    import re

    paquete = Path(server.__file__).parent
    patron = re.compile(
        r"^\s*(?:import|from)\s+(socket|http|urllib|requests|httpx|aiohttp|ftplib|smtplib)\b",
        re.MULTILINE,
    )
    modulos = [m.name for m in pkgutil.iter_modules([str(paquete)])]
    assert "server" in modulos and "repositorio" in modulos  # el paquete se leyó bien

    for archivo in paquete.glob("*.py"):
        encontrados = patron.findall(archivo.read_text(encoding="utf-8"))
        assert not encontrados, f"{archivo.name} importa red: {encontrados}"
