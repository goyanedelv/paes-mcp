# paes-mcp — Tutor PAES vía Model Context Protocol

**Software libre, abierto y gratuito** para estudiar las pruebas PAES de Chile
con cualquier asistente de IA que hable [MCP](https://modelcontextprotocol.io)
(Claude Desktop, Claude Code, Cursor, LibreChat, Open WebUI, agentes propios…).

> 🆓 Código MIT · sin costo, sin cuentas, sin publicidad, sin telemetría.
> 📴 **Funciona sin internet**: dataset, imágenes y corrección son locales.
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

## Estado de las pruebas

| Prueba | Tipo | Estado | Material disponible |
| :--- | :--- | :--- | :--- |
| **Competencia Matemática 1 (M1)** | Obligatoria | ✅ **Implementada** | 155 ítems — **todos los publicados** (2024: 65/65 · 2025: 45/45 · 2026: 45/45), 68 con diagrama |
| Competencia Lectora | Obligatoria | ⬜ No implementada | — |
| Competencia Matemática 2 (M2) | Electiva | ⬜ No implementada | — |
| Ciencias | Electiva | ⬜ No implementada | — |
| Historia y Ciencias Sociales | Electiva | ⬜ No implementada | — |

**"No implementada" no significa "no soportada".** El servidor no sabe de M1 en
particular: lee pruebas declaradas en `paes_mcp/data/pruebas/*.json`. Lo que
falta para cada fila de arriba es el **dataset** construido desde las
publicaciones oficiales del DEMRE, no código nuevo.

Dos matices que conviene saber antes de usarlo:

- La prueba oficial tiene 65 ítems, pero **el DEMRE no publica los 65**: los
  cuadernillos de 2025 y 2026 traen 45 cada uno y los 20 restantes quedan
  reservados por el organismo (el clavijero sí lista las 65 claves). Esos ítems
  **no existen en ninguna fuente oficial y no se inventan aquí**.
  `paes_estado_dataset` distingue explícitamente lo `no_publicados_por_el_demre`
  de lo `pendientes_de_transcribir` —hoy, cero— y `paes_generar_ensayo` avisa
  cuando el material no alcanza para una prueba completa.
- Las pruebas no matemáticas necesitan además sus propios ejes de habilidad
  (por ejemplo *localizar*, *interpretar*, *evaluar* en Competencia Lectora) en
  `paes_mcp/ejes.py`. Es un diccionario de palabras clave, no un rediseño.

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

## Funciona sin conexión

El servidor es **completamente offline**: no importa ninguna biblioteca de red,
no consulta APIs, no descarga nada y no envía nada. Las preguntas, las imágenes,
el clavijero y el progreso del estudiante están en su disco.

Esto importa para estudiar con datos móviles limitados o conexión intermitente:
lo único que necesita internet es su cliente de IA, si el modelo que usa es
remoto. Con un modelo local (Ollama, LM Studio y similares), el sistema completo
funciona sin conexión.

Dos pruebas lo hacen exigible en vez de prometerlo: `tests/test_sin_red.py`
ejecuta el ciclo completo de estudio con toda salida de red inutilizada, y
verifica que ningún módulo del paquete importe `socket`, `http`, `urllib`,
`requests`, `httpx` ni similares.

> El único caso en que se abre un puerto es si usted lo pide explícitamente con
> `PAES_TRANSPORTE=sse` o `streamable-http`, pensado para servir el MCP en una
> red local (una sala de clases, por ejemplo). El valor por defecto, `stdio`, no
> usa red en absoluto: el cliente habla con el servidor por entrada y salida
> estándar.

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

## Cómo contribuir

Toda ayuda sirve, y **no hace falta saber programar** para aportar lo que más
falta: material transcrito desde las publicaciones oficiales.

### Por dónde empezar

| Si usted quiere… | Haga esto |
| :--- | :--- |
| Reportar un ítem mal transcrito | Abra un issue con `id_unico`, `fuente` y `pagina_pdf`; se corrige contra el PDF oficial. |
| Agregar un proceso nuevo (2027…) | Extraiga el cuadernillo oficial con su clavijero y súmelo con trazabilidad completa. |
| Sumar una prueba nueva | Siga [`docs/AGREGAR_PRUEBA.md`](docs/AGREGAR_PRUEBA.md): un JSON y un dataset, sin tocar el código. |
| Aportar una tabla oficial de puntaje | Déjela en `paes_mcp/data/puntajes/` **citando su fuente**; reemplaza la estimación actual. |
| Mejorar la pedagogía | Afine las pistas (`pistas.py`), los prompts (`plantillas.py`) o la heurística de ejes (`ejes.py`). |
| Mejorar el código | Corrija bugs, agregue pruebas, mejore mensajes de error. |

### Entorno de desarrollo

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

### Reglas que no se negocian

Son las que mantienen al proyecto legítimo y útil; un PR que las rompa se cierra:

1. **Solo material oficial y gratuito.** Nada de preuniversitarios, editoriales,
   plataformas de pago ni solucionarios de terceros.
2. **Trazabilidad.** Cada ítem debe declarar `fuente`, `forma`,
   `numero_en_fuente` y `pagina_pdf` para poder verificarse contra el original.
3. **Nada inventado que parezca oficial.** Ni preguntas "al estilo PAES", ni
   tablas de puntaje aproximadas presentadas como del DEMRE.
4. **Anti-spoiler intacto.** La clave no puede salir por ninguna vía que no sea
   `paes_verificar_respuesta`.
5. **Cero telemetría.** Sin analítica, sin cuentas, sin envíos de datos del
   estudiante a servicios externos.

El detalle completo está en [`CONTRIBUTING.md`](CONTRIBUTING.md). Al enviar un PR
usted acepta que su aporte de **código** se distribuya bajo MIT.

## Licencia

Código y documentación: **MIT** ([`LICENSE`](LICENSE)).
Contenido de las pruebas: **obra del DEMRE / Universidad de Chile**, incorporado
desde publicaciones oficiales gratuitas, con atribución y fines educativos. Este
proyecto no reclama derechos sobre él y atiende solicitudes de retiro.
