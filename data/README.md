# `data/` — contenido y datos locales

Aquí vive todo lo que **no es código**: los datasets de cada prueba, sus activos
visuales y el progreso local del estudiante. La raíz del repositorio queda solo
con código y documentación.

```
data/
├── m1/                                  una carpeta por prueba
│   ├── paes_m1_dataset.sqlite           fuente canónica que consume el servidor
│   ├── assets/images/{año}/*.png        recortes de figuras, tablas y gráficos
│   └── exports/                         mismas preguntas en otros formatos
│       ├── paes_m1_dataset.csv
│       ├── paes_m1_dataset.json
│       └── paes_m1_dataset.js
└── progreso_estudiante.sqlite           datos locales del estudiante (no se versiona)
```

## Reglas

- **El SQLite manda.** Es lo único que lee el servidor. Los archivos de
  `exports/` son copias de conveniencia para usar el dataset fuera de este
  proyecto; si regenera el dataset, regenérelos también.
- **Rutas de imagen relativas.** Dentro del dataset las imágenes se guardan como
  `assets/images/{año}/{archivo}.png`, relativas a la carpeta de la prueba. Así
  el dataset sigue siendo válido aunque mueva `data/` completa de lugar.
- **Una carpeta por prueba.** Al agregar M2, Competencia Lectora, Ciencias o
  Historia, cree `data/<prueba>/` con la misma forma y apunte allí el JSON de
  la prueba en `paes_mcp/data/pruebas/`. Ver [`../docs/AGREGAR_PRUEBA.md`](../docs/AGREGAR_PRUEBA.md).
- **`progreso_estudiante.sqlite` es privado.** Está en `.gitignore`: es el
  historial del estudiante y nunca se versiona ni se transmite.

Sobre la procedencia de este contenido —publicaciones oficiales y gratuitas del
DEMRE—, ver [`../AVISO_LEGAL.md`](../AVISO_LEGAL.md) y
[`../docs/PROCEDENCIA_DATOS.md`](../docs/PROCEDENCIA_DATOS.md).

> No confundir `data/` (contenido de las pruebas) con `paes_mcp/data/`
> (definiciones de prueba y tablas de puntaje, que son datos del paquete).
