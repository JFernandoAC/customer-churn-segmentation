---
name: stage-notes
description: Write or update the Spanish study note for a project stage in notas/NN-tema.md. Use whenever a stage of the churn project is created or changed, or when the user asks for an explanation of a stage, file or concept to keep.
---

# Notas de estudio por etapa

Las notas son para que José pueda explicar el proyecto en una entrevista
técnica. Viven en `notas/` (ignorada por git) y van en **español sencillo**.

## Nombre del archivo
`notas/NN-tema-corto.md` con número de dos dígitos según el orden del
pipeline (ver `notas/00-indice.md`). Si cambias una etapa existente, edita su
nota; no crees otra.

## Secciones obligatorias (en este orden)
1. **Qué construimos y para qué sirve** — 3 a 6 líneas, sin jerga. Qué problema
   del negocio resuelve esta etapa.
2. **Paso a paso** — archivo por archivo, en el orden en que se crearon, con el
   comando para correrlo y qué debe salir en pantalla.
3. **El código explicado** — bloque por bloque. Copia el fragmento real (corto)
   y debajo explica qué hace cada línea importante y por qué. Que lo entienda
   alguien que sabe pandas pero nunca vio la librería.
4. **Conceptos clave** — cada término técnico con una definición de una o dos
   frases y un ejemplo con los datos del proyecto.
5. **Decisiones que tomamos** — tabla o lista: decisión, alternativa
   descartada, por qué.
6. **Resultados reales** — números que salieron al correrlo. Nunca inventados:
   si no se ha corrido, escribe "pendiente de correr".
7. **Preguntas de entrevista** — 4 a 6 preguntas probables con respuesta corta
   (2-4 frases) en primera persona, como las diría José.

## Reglas de estilo
- Todo término técnico se define la primera vez que aparece en la nota.
- Frases cortas. Ejemplos con datos del proyecto (clientes, facturas, libras).
- Los nombres de código (`recency_days`, `build_features`) se quedan en inglés
  y entre backticks.
- No repitas teoría que no se usa en el código.
