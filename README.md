# paes-mcp — Tutor PAES vía Model Context Protocol

**Software libre, abierto y gratuito** para estudiar las pruebas PAES de Chile
con cualquier asistente de IA que hable [MCP](https://modelcontextprotocol.io)
(Claude Desktop, Claude Code, Cursor, LibreChat, Open WebUI, agentes propios…).

> 🆓 Código MIT · sin costo, sin cuentas, sin publicidad, sin telemetría.
> 📚 El contenido proviene **solo** de las publicaciones oficiales, públicas y
> gratuitas del DEMRE. Ver [`AVISO_LEGAL.md`](AVISO_LEGAL.md).
> 🏛️ Proyecto independiente, **no afiliado** al DEMRE ni a ninguna universidad.

Hoy cubre **Matemática 1 (M1)**; la arquitectura es multi-prueba desde el primer
día: agregar M2, Competencia Lectora, Ciencias o Historia es dejar caer un JSON
y un dataset, sin tocar el código ([`docs/AGREGAR_PRUEBA.md`](docs/AGREGAR_PRUEBA.md)).

---

## Por qué existe

Pedirle ejercicios PAES a un LLM a secas falla de tres maneras:

1. **Alucina la corrección.** Resuelve el ítem al vuelo y, si se equivoca,
   corrige mal al estudiante. Aquí la clave sale del **clavijero oficial**, no
   del modelo.
2. **Hace spoiler.** Entrega la solución completa de inmediato. Aquí la clave
   está *retenida en el servidor* hasta que el estudiante responde.
3. **Está ciego.** Buena parte de M1 son figuras, tablas y gráficos. Aquí cada
   pregunta viaja con su recorte PNG como contenido multimodal.

## Instalación

```bash
git clone https://github.com/goyanedelv/paes-mcp.git
cd paes-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Conéctelo a su cliente MCP (`claude_desktop_config.json` o equivalente):

```json
{
  "mcpServers": {
    "paes-tutor": {
      "command": "python3",
      "args": ["-m", "paes_mcp"],
      "cwd": "/ruta/a/paes-mcp",
      "env": { "PAES_PRUEBA_DEFAULT": "m1" }
    }
  }
}
```

Pruébelo sin cliente:

```bash
python -m paes_mcp          # servidor stdio
pytest                      # núcleo + verificación end-to-end vía MCP
```

## Cómo se usa (conversación típica)

> **Estudiante:** quiero practicar geometría con figuras.
> **Tutor:** *(busca, entrega enunciado + diagrama, no la clave)* ¿Qué representa `h` aquí?
> **Estudiante:** creo que es la A.
> **Tutor:** *(verifica contra el clavijero oficial)* Correcto. Ahora explícame por qué la C falla…

## Herramientas expuestas

| Herramienta | Qué hace |
| :--- | :--- |
| `paes_listar_pruebas` | Pruebas soportadas y disponibilidad de su dataset. |
| `paes_buscar_preguntas` | Filtra por año, texto, eje temático, diagrama, alternativas gráficas. |
| `paes_obtener_pregunta` | Enunciado + alternativas + imágenes. **Nunca la clave.** |
| `paes_verificar_respuesta` | Corrige contra el clavijero oficial y registra el intento. |
| `paes_solicitar_pista` | Andamiaje socrático en 3 niveles, sin revelar la respuesta. |
| `paes_calcular_puntaje` | Bruto → escala 100-1000, declarando si es oficial o estimado. |
| `paes_generar_ensayo` | `completo`, `minisensayo`, `focalizado`, `repaso_errores`. |
| `paes_resumen_progreso` | Aciertos, tiempos y desempeño por eje temático (local). |
| `paes_preguntas_pendientes` | Bitácora de errores para repetición espaciada. |
| `paes_reiniciar_progreso` | Borra el historial local (requiere confirmación). |
| `paes_estado_dataset` | Cobertura real del material disponible, por año. |
| `paes_procedencia_y_licencia` | De dónde sale el material y bajo qué licencia. |

**Recursos:** `paes://pruebas`, `paes://{prueba}/preguntas/{id}`,
`paes://{prueba}/imagenes/{año}/{id}/{recurso}`, `paes://{prueba}/tabla-puntaje/{año}`,
`paes://estudiante/resumen`, `paes://estudiante/pendientes`, `paes://proyecto/licencia`.

**Prompts:** `tutor_socratico`, `analisis_distractores`, `simulacro`, `plan_de_estudio`.

## Configuración

| Variable | Por defecto | Para qué |
| :--- | :--- | :--- |
| `PAES_DATA_DIR` | raíz del repo | Raíz desde la que se resuelve `data/`. |
| `PAES_SPECS_DIR` | `paes_mcp/data/pruebas` | Definiciones de prueba. |
| `PAES_PROGRESO_DB` | `data/progreso_estudiante.sqlite` | Historial local del estudiante. |
| `PAES_PRUEBA_DEFAULT` | `m1` | Prueba usada si no se especifica. |
| `PAES_MAX_BYTES_IMAGEN` | `4194304` | Tope por imagen servida. |
| `PAES_TRANSPORTE` | `stdio` | `stdio`, `sse` o `streamable-http`. |

## Honestidad del proyecto

- Los **puntajes** son estimados por interpolación mientras no cargue una tabla
  oficial del DEMRE en `paes_mcp/data/puntajes/`; la respuesta lo dice con
  `"es_oficial": false`. **No inventamos tablas oficiales.**
- La clasificación por **eje temático** es heurística del servidor, no oficial.
- El dataset local **puede no cubrir la prueba completa**: `paes_estado_dataset`
  muestra la cobertura real por año.
- Ante cualquier discrepancia, **manda el documento oficial del DEMRE**.

## Documentación

- [`MCP_DESIGN.md`](MCP_DESIGN.md) — diseño arquitectónico completo.
- [`AVISO_LEGAL.md`](AVISO_LEGAL.md) — licencias, procedencia y takedown.
- [`docs/PROCEDENCIA_DATOS.md`](docs/PROCEDENCIA_DATOS.md) — trazabilidad ítem a ítem.
- [`docs/AGREGAR_PRUEBA.md`](docs/AGREGAR_PRUEBA.md) — sumar M2, Lectora, Ciencias…
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — cómo aportar.

## Estructura del repositorio

```
paes_mcp/        código del servidor (+ data/pruebas: definiciones declarativas)
data/            contenido: un directorio por prueba (data/m1/…) y progreso local
docs/            procedencia de los datos y guía para agregar pruebas
tests/           pruebas del núcleo y verificación end-to-end vía MCP
```

## Licencia

Código y documentación: **MIT** ([`LICENSE`](LICENSE)).
Contenido de las pruebas: **obra del DEMRE / Universidad de Chile**, incorporado
desde publicaciones oficiales gratuitas, con atribución y fines educativos. Este
proyecto no reclama derechos sobre él y atiende solicitudes de retiro.
