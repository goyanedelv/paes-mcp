"""El servidor debe funcionar completo sin conexión a internet.

No es un detalle de implementación: es una promesa del proyecto (sin telemetría,
sin llamadas a APIs remotas, datos del estudiante solo en su máquina) y una
condición de uso real, porque muchos estudiantes estudian con datos móviles
limitados o conexión intermitente. Esta prueba la hace exigible: corta toda
salida de red y ejecuta el flujo completo de estudio.
"""

from __future__ import annotations

import socket

import pytest

from paes_mcp import server


class RedProhibida(RuntimeError):
    """Se intentó usar la red donde el proyecto promete no usarla."""


@pytest.fixture()
def sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inutiliza toda salida de red durante la prueba (se restaura al terminar)."""

    def bloquear(*args: object, **kwargs: object) -> None:
        raise RedProhibida("el servidor intentó usar la red")

    for objetivo, atributo in (
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
        (socket, "gethostbyname"),
    ):
        monkeypatch.setattr(objetivo, atributo, bloquear)


def test_ciclo_de_estudio_completo_sin_conexion(
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
    """Ningún módulo del paquete debe traer clientes HTTP ni sockets propios."""
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
