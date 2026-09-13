"""Verificacion extremo a extremo contra un cliente MCP real sobre stdio.

Se omite automaticamente si el SDK de MCP no esta instalado, de modo que la
suite del nucleo (tests/test_paes_mcp.py) sigue corriendo sin dependencias.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp", reason="El SDK de MCP no esta instalado.")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ID_GEOMETRIA = "PAES_2024_M1_Q45"


async def _sesion(progreso_db: Path):
    entorno = dict(
        os.environ,
        PAES_DATA_DIR=str(RAIZ),
        PAES_PROGRESO_DB=str(progreso_db),
        PYTHONPATH=str(RAIZ),
    )
    parametros = StdioServerParameters(
        command=sys.executable, args=["-m", "paes_mcp"], env=entorno
    )
    return stdio_client(parametros)


def _correr(corutina):
    return asyncio.run(corutina)


def test_ciclo_completo_de_estudio(tmp_path: Path):
    async def escenario() -> None:
        async with await _sesion(tmp_path / "progreso.sqlite") as (lector, escritor):
            async with ClientSession(lector, escritor) as sesion:
                await sesion.initialize()

                herramientas = {t.name for t in (await sesion.list_tools()).tools}
                assert {"paes_obtener_pregunta", "paes_verificar_respuesta"} <= herramientas

                prompts = {p.name for p in (await sesion.list_prompts()).prompts}
                assert "tutor_socratico" in prompts

                # 1. Buscar una pregunta con diagrama.
                salida = await sesion.call_tool(
                    "paes_buscar_preguntas", {"requiere_diagrama": True, "limite": 1}
                )
                busqueda = json.loads(salida.content[0].text)
                assert busqueda["devueltas"] == 1
                assert "correcta" not in salida.content[0].text.lower()

                # 2. Obtener la pregunta: texto + imagen, nunca la clave.
                salida = await sesion.call_tool(
                    "paes_obtener_pregunta", {"id_unico": ID_GEOMETRIA}
                )
                tipos = [bloque.type for bloque in salida.content]
                assert tipos[0] == "text" and "image" in tipos
                assert "alternativa_correcta" not in salida.content[0].text

                # 3. Pedir una pista sin que aparezca la respuesta.
                salida = await sesion.call_tool(
                    "paes_solicitar_pista", {"id_unico": ID_GEOMETRIA, "nivel_pista": 1}
                )
                assert json.loads(salida.content[0].text)["tipo_pista"] == "concepto"

                # 4. Verificar: aqui, y solo aqui, sale la clave oficial.
                salida = await sesion.call_tool(
                    "paes_verificar_respuesta",
                    {"id_unico": ID_GEOMETRIA, "alternativa_seleccionada": "b"},
                )
                verificacion = json.loads(salida.content[0].text)
                assert verificacion["alternativa_correcta"] in ("A", "B", "C", "D")
                assert verificacion["intento_registrado"] is True

                # 5. El error se traduce a un mensaje legible, no a una excepcion.
                salida = await sesion.call_tool(
                    "paes_obtener_pregunta", {"id_unico": "NO_EXISTE"}
                )
                assert "error" in json.loads(salida.content[0].text)

                # 6. Recursos: ficha sin clave, imagen PNG y tabla con su estatus.
                ficha = await sesion.read_resource(f"paes://m1/preguntas/{ID_GEOMETRIA}")
                assert "alternativa_correcta" not in ficha.contents[0].text

                imagen = await sesion.read_resource(
                    f"paes://m1/imagenes/2024/{ID_GEOMETRIA}/enunciado"
                )
                assert imagen.contents[0].mime_type == "image/png"

                tabla = await sesion.read_resource("paes://m1/tabla-puntaje/2024")
                assert json.loads(tabla.contents[0].text)["es_oficial"] is False

                # 7. Prompt pedagogico.
                prompt = await sesion.get_prompt("tutor_socratico", {"contexto": "geometria"})
                assert "NUNCA anticipes" in prompt.messages[0].content.text

    _correr(escenario())
