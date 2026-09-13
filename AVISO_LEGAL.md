# Aviso legal, licencias y procedencia del material

Este documento explica, sin letra chica, **qué es libre aquí, de dónde sale cada
cosa y qué NO hacemos**.

## 1. El software es libre, abierto y gratuito

- Todo el código de este repositorio está bajo **licencia MIT** (ver `LICENSE`).
- Es **gratis**: no hay versión de pago, ni suscripción, ni funciones bloqueadas,
  ni cuenta de usuario, ni publicidad.
- Es **abierto**: puede leerlo, copiarlo, modificarlo, redistribuirlo y usarlo en
  su colegio, preuniversitario, fundación o proyecto personal.
- **No recolecta datos**: el progreso del estudiante se guarda en un archivo
  SQLite local en su propio computador. El servidor no envía nada a ningún
  servicio externo, no tiene telemetría y no llama a ninguna API remota.

## 2. De dónde viene el contenido de las preguntas

Todo el material de preguntas proviene de **publicaciones oficiales del DEMRE
(Universidad de Chile), de acceso libre y gratuito**: los modelos de prueba,
las pruebas oficiales publicadas tras cada proceso de admisión y sus claves de
corrección, que el propio DEMRE difunde públicamente en
<https://demre.cl/publicaciones/> para que cualquier persona estudie con ellas.

- No se usa material de preuniversitarios, editoriales ni plataformas de pago.
- No se incluyen solucionarios, resoluciones ni guías de terceros.
- No se copian contenidos desde sitios que restrinjan su uso.
- No se inventan preguntas "al estilo PAES" haciéndolas pasar por oficiales.

## 3. Lo que este proyecto sí hace con ese material

Lo que se distribuye en `data/<prueba>/` —el SQLite, sus exportaciones y los
recortes de `assets/`— es una **transcripción
estructurada** de esas publicaciones oficiales: texto de enunciados y
alternativas, recortes de las figuras que acompañan a cada pregunta y la clave
publicada por el DEMRE, todo con metadatos de trazabilidad (año, fuente, forma,
número de pregunta y página del documento original) para que cualquiera pueda
verificar cada ítem contra el PDF oficial.

## 4. Lo que este proyecto NO afirma

Sería deshonesto decir que aquí "no hay obra de terceros". La afirmación
correcta y verificable es esta:

- Las pruebas PAES, sus enunciados, figuras y claves son **obra del DEMRE /
  Universidad de Chile**. El proyecto **no reclama ningún derecho** sobre ellas.
- Este material se incorpora **desde fuentes oficiales, públicas y gratuitas**,
  con **atribución expresa**, **sin ánimo de lucro** y con **fin exclusivamente
  educativo** (estudio y preparación de estudiantes).
- La licencia MIT del repositorio **no se extiende** a ese contenido: quien
  reutilice el dataset debe respetar los derechos del titular original.

Si usted necesita certeza jurídica para un uso comercial o institucional
distinto del estudio personal y educativo, consulte directamente al DEMRE.

## 5. Independencia

Proyecto **independiente**, hecho por y para estudiantes. **No está afiliado,
patrocinado, revisado ni avalado** por el DEMRE, la Universidad de Chile, el
Ministerio de Educación ni ninguna institución oficial. Las marcas "PAES" y
"DEMRE" se mencionan únicamente de forma descriptiva y referencial.

## 6. Exactitud y límites

- Las claves de corrección son las publicadas oficialmente, pero la
  transcripción es automatizada: **puede contener errores**. Ante cualquier
  diferencia, **manda el documento oficial del DEMRE**.
- Los puntajes entregados por `paes_calcular_puntaje` son **estimaciones** por
  interpolación mientras no se cargue una tabla oficial completa; la propia
  respuesta lo declara con `"es_oficial": false`.
- La clasificación por eje temático es una **heurística del servidor**, no una
  clasificación oficial del temario.

## 7. Solicitudes de retiro (takedown)

Si usted representa al DEMRE, a la Universidad de Chile o a cualquier titular de
derechos y considera que algún contenido de este repositorio no debe estar aquí,
**abra un issue o escriba a quien mantiene el repositorio**: el material
señalado se retirará a la brevedad, sin discusión previa. La intención del
proyecto es dar acceso libre al estudio, nunca disputar la titularidad del
material ni sustituir a la fuente oficial.
