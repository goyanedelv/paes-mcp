# Tablas oficiales de conversión de puntaje

Este directorio está **vacío a propósito**.

El proyecto no incluye tablas de transformación oficiales del DEMRE porque no
las reproduce ni las inventa. Si usted necesita el puntaje oficial exacto,
descargue la tabla publicada por el DEMRE para el proceso correspondiente y
guárdela aquí como `<prueba>_<anio>.json`:

```json
{
  "_nota": "Tabla oficial DEMRE, proceso de admisión 2024, M1.",
  "0": 100,
  "1": 103,
  "60": 1000
}
```

Mientras no exista ese archivo, `paes_calcular_puntaje` devuelve un valor
**estimado** por interpolación entre puntos ancla públicos, marcado con
`"es_oficial": false`.
