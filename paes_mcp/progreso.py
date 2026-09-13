"""Telemetria local del estudiante (repeticion espaciada y bitacora de errores).

Todo queda en un SQLite local del propio estudiante. El servidor no envia datos
a ningun servicio externo: no hay telemetria remota, ni analitica, ni cuentas.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import CONFIG

ESQUEMA = """
CREATE TABLE IF NOT EXISTS intentos (
    id_intento        INTEGER PRIMARY KEY AUTOINCREMENT,
    prueba            TEXT NOT NULL DEFAULT 'm1',
    id_unico          TEXT NOT NULL,
    fecha_hora        TEXT NOT NULL,
    alternativa       TEXT NOT NULL,
    acierto           INTEGER NOT NULL,
    tiempo_segundos   INTEGER,
    nivel_pista_usada INTEGER DEFAULT 0,
    eje_tematico      TEXT,
    sesion_id         TEXT
);

CREATE TABLE IF NOT EXISTS bitacora_errores (
    prueba            TEXT NOT NULL DEFAULT 'm1',
    id_unico          TEXT NOT NULL,
    veces_fallada     INTEGER DEFAULT 0,
    veces_acertada    INTEGER DEFAULT 0,
    estado_dominio    TEXT CHECK(estado_dominio IN ('pendiente','en_repaso','dominada')) DEFAULT 'pendiente',
    ultimo_intento    TEXT,
    PRIMARY KEY (prueba, id_unico)
);

CREATE TABLE IF NOT EXISTS sesiones (
    sesion_id     TEXT PRIMARY KEY,
    prueba        TEXT NOT NULL,
    modalidad     TEXT NOT NULL,
    creada        TEXT NOT NULL,
    ids_preguntas TEXT NOT NULL,
    cerrada       TEXT
);

CREATE INDEX IF NOT EXISTS idx_intentos_pregunta ON intentos(prueba, id_unico);
CREATE INDEX IF NOT EXISTS idx_intentos_sesion   ON intentos(sesion_id);
CREATE INDEX IF NOT EXISTS idx_bitacora_estado   ON bitacora_errores(estado_dominio);
"""


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Progreso:
    """Persistencia local del avance del estudiante."""

    def __init__(self, ruta: Path | None = None) -> None:
        self.ruta = Path(ruta) if ruta else CONFIG.progreso_db
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as con:
            con.executescript(ESQUEMA)

    @contextmanager
    def _conectar(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.ruta)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------ escritura

    def registrar_intento(
        self, prueba: str, id_unico: str, alternativa: str, acierto: bool,
        tiempo_segundos: int | None = None, nivel_pista_usada: int = 0,
        eje_tematico: str | None = None, sesion_id: str | None = None,
    ) -> int:
        ahora = _ahora()
        with self._conectar() as con:
            cur = con.execute(
                """INSERT INTO intentos
                   (prueba, id_unico, fecha_hora, alternativa, acierto,
                    tiempo_segundos, nivel_pista_usada, eje_tematico, sesion_id)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (prueba, id_unico, ahora, alternativa, int(acierto),
                 tiempo_segundos, nivel_pista_usada, eje_tematico, sesion_id),
            )
            con.execute(
                """INSERT INTO bitacora_errores (prueba, id_unico, veces_fallada, veces_acertada, ultimo_intento)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(prueba, id_unico) DO UPDATE SET
                     veces_fallada  = veces_fallada  + excluded.veces_fallada,
                     veces_acertada = veces_acertada + excluded.veces_acertada,
                     ultimo_intento = excluded.ultimo_intento""",
                (prueba, id_unico, int(not acierto), int(acierto), ahora),
            )
            con.execute(
                """UPDATE bitacora_errores
                      SET estado_dominio = CASE
                            WHEN veces_fallada = 0 THEN 'dominada'
                            WHEN veces_acertada >= veces_fallada THEN 'en_repaso'
                            ELSE 'pendiente' END
                    WHERE prueba = ? AND id_unico = ?""",
                (prueba, id_unico),
            )
            return int(cur.lastrowid or 0)

    def crear_sesion(self, prueba: str, modalidad: str, ids_preguntas: list[str]) -> str:
        sesion_id = f"{prueba}-{modalidad}-{uuid.uuid4().hex[:8]}"
        with self._conectar() as con:
            con.execute(
                "INSERT INTO sesiones (sesion_id, prueba, modalidad, creada, ids_preguntas) VALUES (?,?,?,?,?)",
                (sesion_id, prueba, modalidad, _ahora(), ",".join(ids_preguntas)),
            )
        return sesion_id

    def cerrar_sesion(self, sesion_id: str) -> None:
        with self._conectar() as con:
            con.execute("UPDATE sesiones SET cerrada = ? WHERE sesion_id = ?", (_ahora(), sesion_id))

    def reiniciar(self, prueba: str | None = None) -> dict[str, int]:
        """Borra el historial local (derecho del estudiante sobre sus propios datos)."""
        with self._conectar() as con:
            if prueba:
                borrados = con.execute("DELETE FROM intentos WHERE prueba = ?", (prueba,)).rowcount
                con.execute("DELETE FROM bitacora_errores WHERE prueba = ?", (prueba,))
                con.execute("DELETE FROM sesiones WHERE prueba = ?", (prueba,))
            else:
                borrados = con.execute("DELETE FROM intentos").rowcount
                con.execute("DELETE FROM bitacora_errores")
                con.execute("DELETE FROM sesiones")
        return {"intentos_borrados": max(borrados, 0)}

    # ------------------------------------------------------------------- lectura

    def resumen(self, prueba: str | None = None) -> dict[str, Any]:
        filtro, params = ("WHERE prueba = ?", (prueba,)) if prueba else ("", ())
        with self._conectar() as con:
            total = con.execute(f"SELECT COUNT(*) c, SUM(acierto) a, AVG(tiempo_segundos) t FROM intentos {filtro}", params).fetchone()
            por_eje = con.execute(
                f"""SELECT eje_tematico, COUNT(*) intentos, SUM(acierto) aciertos
                      FROM intentos {filtro} GROUP BY eje_tematico ORDER BY intentos DESC""",
                params,
            ).fetchall()
        intentos = total["c"] or 0
        aciertos = total["a"] or 0
        return {
            "prueba": prueba,
            "total_intentos": intentos,
            "aciertos": aciertos,
            "porcentaje_acierto": round(100 * aciertos / intentos, 1) if intentos else None,
            "tiempo_promedio_segundos": round(total["t"], 1) if total["t"] else None,
            "por_eje_tematico": [
                {
                    "eje_tematico": f["eje_tematico"] or "sin_clasificar",
                    "intentos": f["intentos"],
                    "aciertos": f["aciertos"] or 0,
                    "porcentaje_acierto": round(100 * (f["aciertos"] or 0) / f["intentos"], 1),
                }
                for f in por_eje
            ],
            "almacenamiento": str(self.ruta),
            "privacidad": "Datos locales del estudiante; el servidor no los transmite a terceros.",
        }

    def pendientes(self, prueba: str | None = None, limite: int = 20) -> list[dict[str, Any]]:
        filtro, params = ("WHERE prueba = ?", [prueba]) if prueba else ("", [])
        with self._conectar() as con:
            filas = con.execute(
                f"""SELECT * FROM bitacora_errores {filtro}
                     {'AND' if filtro else 'WHERE'} estado_dominio != 'dominada'
                     ORDER BY veces_fallada DESC, ultimo_intento ASC LIMIT ?""",
                [*params, limite],
            ).fetchall()
        return [dict(f) for f in filas]

    def ejes_debiles(self, prueba: str | None = None, minimo_intentos: int = 3) -> list[str]:
        resumen = self.resumen(prueba)
        candidatos = [
            e for e in resumen["por_eje_tematico"]
            if e["intentos"] >= minimo_intentos and e["porcentaje_acierto"] < 70
        ]
        candidatos.sort(key=lambda e: e["porcentaje_acierto"])
        return [e["eje_tematico"] for e in candidatos]
