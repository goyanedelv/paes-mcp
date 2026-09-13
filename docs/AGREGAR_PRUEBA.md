# Agregar una nueva prueba (M2, Competencia Lectora, Ciencias, Historia…)

El servidor es multi-prueba por construcción: la prueba M1 no está escrita en el
código, sino declarada en `paes_mcp/data/pruebas/m1.json`. Sumar otra prueba son
tres pasos y **cero líneas de código**.

## Paso 0 — Ubicación

Cada prueba vive en su propia carpeta bajo `data/`, con la misma forma que `data/m1/`:

```
data/<prueba>/
├── paes_<prueba>_dataset.sqlite
├── assets/images/{año}/*.png
└── exports/            (opcional: csv/json/js de conveniencia)
```

## Paso 1 — Construir el dataset

Cree un SQLite con la tabla `preguntas` y este esquema mínimo (las columnas de
alternativa pueden llegar hasta `e` si la prueba tiene cinco opciones):

```sql
CREATE TABLE preguntas (
    id_unico                 TEXT PRIMARY KEY,  -- p. ej. PAES_2025_M2_Q07
    año                      INTEGER,
    fuente                   TEXT,              -- publicación oficial exacta
    disciplina               TEXT,
    forma                    TEXT,
    numero_en_fuente         INTEGER,
    es_piloto                BOOLEAN,
    pagina_pdf               INTEGER,           -- trazabilidad al PDF oficial
    enunciado_pregunta       TEXT,
    tiene_imagen_enunciado   BOOLEAN,
    imagen_enunciado         TEXT,              -- ruta relativa: assets/images/{año}/…
    imagen_pregunta_completa TEXT,
    alternativa_a_texto      TEXT,
    alternativa_a_imagen     TEXT,
    -- … b, c, d (y e si corresponde) …
    alternativa_correcta     TEXT               -- clavijero oficial
);
```

Reglas no negociables del proyecto:

- El material debe provenir de **publicaciones oficiales, públicas y gratuitas**.
- Cada ítem debe quedar **trazable**: `fuente`, `forma`, `numero_en_fuente` y
  `pagina_pdf` deben permitir volver al documento original.
- Nada de material de preuniversitarios, editoriales ni solucionarios de terceros.

## Paso 2 — Declarar la prueba

Copie `paes_mcp/data/pruebas/_plantilla.json` a `<id>.json` y complete:

```json
{
  "id": "m2",
  "nombre": "PAES Matemática 2 (M2)",
  "estado": "activa",
  "dataset": { "sqlite": "data/m2/paes_m2_dataset.sqlite", "tabla": "preguntas", "assets_base": "data/m2/assets" },
  "estructura_oficial": { "preguntas_totales": 55, "preguntas_piloto": 5, "preguntas_validas": 50, "alternativas": ["A","B","C","D"], "duracion_minutos": 140, "escala_puntaje": [100, 1000] },
  "ejes_tematicos": ["numeros", "algebra_y_funciones", "geometria", "probabilidad_y_estadistica"],
  "tablas_puntaje": { "_meta": { "es_oficial": false, "nota": "…" } },
  "fuente_oficial": { "organismo": "DEMRE - Universidad de Chile", "url": "https://demre.cl/publicaciones/" }
}
```

Los archivos que empiezan con `_` se ignoran al cargar el catálogo.

## Paso 3 — Ajustar la clasificación temática (opcional)

`paes_mcp/ejes.py` infiere el eje por palabras clave. Para pruebas no
matemáticas, agregue su propio diccionario de ejes (por ejemplo `localizar`,
`interpretar`, `evaluar` en Competencia Lectora) y declare esos ejes en el JSON.
La clasificación se reporta siempre como `"clasificacion_eje": "heuristica"`.

## Verificación

```bash
python -c "from paes_mcp.catalogo import CATALOGO; print(CATALOGO.ids())"
pytest
```

Todas las herramientas aceptan el parámetro `prueba`; el valor por defecto lo fija
`PAES_PRUEBA_DEFAULT`. Una prueba declarada sin dataset presente aparece en
`paes_listar_pruebas` con `"dataset_disponible": false` y falla con un mensaje
explícito en lugar de romper el servidor.
