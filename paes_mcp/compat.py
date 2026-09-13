"""Compatibilidad entre el SDK oficial de Python 1.x (FastMCP) y 2.x (MCPServer).

El servidor se escribe una sola vez y funciona en ambas versiones del SDK.
"""

from __future__ import annotations

from typing import Any

try:  # SDK 2.x
    from mcp.server.mcpserver import Image, MCPServer as _Servidor  # type: ignore

    VERSION_SDK = "2.x"
except ModuleNotFoundError:  # pragma: no cover - depende del entorno
    try:  # SDK 1.x
        from mcp.server.fastmcp import FastMCP as _Servidor, Image  # type: ignore

        VERSION_SDK = "1.x"
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ModuleNotFoundError(
            "No se encontro el SDK de MCP. Instale las dependencias con "
            "`pip install -e .` o `pip install 'mcp>=1.2'`."
        ) from exc


def crear_servidor(**kwargs: Any):
    """Instancia el servidor MCP disponible en el entorno."""
    return _Servidor(**kwargs)


__all__ = ["crear_servidor", "Image", "VERSION_SDK"]
