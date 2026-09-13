# Procedencia y trazabilidad de los datos

## Fuente única

Publicaciones oficiales del **DEMRE (Universidad de Chile)**, de acceso libre y
gratuito: <https://demre.cl/publicaciones/>. Nada más. Sin material de
preuniversitarios, editoriales, plataformas de pago ni solucionarios de terceros.

## Contenido actual del dataset (`data/m1/paes_m1_dataset.sqlite`)

| Año del proceso | Ítems transcritos | Piloto | Con diagrama | Alternativas gráficas |
| :--- | ---: | ---: | ---: | ---: |
| 2024 | 65 | 5 | 26 | 2 |
| 2025 | 45 | 5 | 20 | 4 |
| 2026 | 45 | 4 | 22 | 3 |

La estructura oficial de M1 es de 65 ítems (60 válidos + 5 de pilotaje). Los años
con menos ítems reflejan **cobertura parcial del material transcrito**, no una
prueba más corta: `paes_estado_dataset` reporta la cobertura real y las
herramientas de ensayo advierten cuando no alcanzan a armar una prueba completa.

## Trazabilidad ítem a ítem

Cada fila conserva los datos para volver al documento original:

- `fuente` — publicación oficial exacta (p. ej. *PAES Regular 2024, Admisión 2024*).
- `forma` — forma del cuadernillo.
- `numero_en_fuente` — número del ítem en esa forma.
- `pagina_pdf` — página del PDF oficial.
- `alternativa_correcta` — clave del clavijero oficial publicado.

## Qué es dato oficial y qué es derivado

| Campo | Estatus |
| :--- | :--- |
| Enunciado, alternativas, figuras | Transcripción del documento oficial |
| `alternativa_correcta` | Clavijero oficial publicado |
| `pagina_pdf`, `forma`, `fuente` | Metadato de trazabilidad |
| `eje_tematico` | **Derivado**: heurística del servidor, no oficial |
| Pistas (`paes_solicitar_pista`) | **Generado** por el servidor, no oficial |
| Puntaje (`paes_calcular_puntaje`) | **Estimado** salvo que cargue tabla oficial |

Toda salida del servidor que incluya un campo derivado o generado lo declara
explícitamente. Ese es el compromiso: el estudiante siempre sabe qué está
leyendo, y ante discrepancias manda el documento oficial del DEMRE.

## Errores de transcripción

La extracción es automatizada y puede tener errores (símbolos matemáticos,
fracciones, recortes de figuras). Si detecta uno, abra un issue indicando
`id_unico`, `fuente` y `pagina_pdf`; se corrige contra el PDF oficial.
