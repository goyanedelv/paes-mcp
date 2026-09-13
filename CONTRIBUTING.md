# Cómo contribuir

Gracias por querer aportar. Este proyecto es libre, gratuito y hecho para que
cualquier estudiante de Chile pueda prepararse sin pagar nada.

## Lo que sí se acepta

- Correcciones de transcripción contra el PDF oficial (indique `id_unico`,
  `fuente` y `pagina_pdf`).
- Nuevas pruebas construidas **solo** desde publicaciones oficiales gratuitas
  (ver `docs/AGREGAR_PRUEBA.md`).
- Tablas oficiales de conversión de puntaje del DEMRE, con su fuente citada.
- Mejoras a la heurística de ejes temáticos, a las pistas y a las pruebas.
- Traducciones y mejoras de documentación.

## Lo que no se acepta (se cierra sin debate)

- Material de preuniversitarios, editoriales, plataformas de pago o
  solucionarios de terceros.
- Preguntas inventadas presentadas como si fueran oficiales.
- Tablas de puntaje "aproximadas" presentadas como oficiales.
- Telemetría, analítica, cuentas de usuario o cualquier envío de datos del
  estudiante a servicios externos.
- Cualquier cosa que rompa el diseño anti-spoiler (filtrar la clave fuera de
  `paes_verificar_respuesta`).

## Flujo

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Mantenga el estilo del código existente: módulos cortos, nombres en español,
docstrings que expliquen el *porqué*, y una prueba por cada comportamiento nuevo.
Toda salida nueva que sea derivada o generada debe declararlo en su propio JSON.

Al enviar un PR usted acepta que su aporte de **código** se distribuya bajo MIT.
