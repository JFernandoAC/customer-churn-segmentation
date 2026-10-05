---
name: interview-prep
description: Prepare José for technical interview questions about this churn project. Use when he asks to practice, be quizzed, review a stage for an interview, or "how would I explain X".
---

# Práctica de entrevista técnica

Objetivo: que José pueda defender cada decisión del proyecto con sus propias
palabras. Todo en español, salvo nombres de código.

## Modos
- **Preguntas** (por defecto): dada una etapa o archivo, lee el código real y
  su nota en `notas/`, y genera 8 preguntas de entrevista de dificultad
  creciente: qué hace → por qué así → qué pasaría si → cómo lo mejorarías.
  Debajo de cada una, una respuesta modelo basada en el código y los números
  reales del proyecto (nunca inventados).
- **Quiz**: si José dice "quiz" o "pregúntame", haz UNA pregunta a la vez,
  espera su respuesta, califícala (bien / incompleta / incorrecta), explica lo
  que faltó y pasa a la siguiente. Al final, lista los temas débiles y qué nota
  repasar.

## Temas que casi seguro preguntan en este proyecto
- Cómo se definió churn sin suscripción (ventana de 90 días) y su límite
  (la ventana cae en la temporada navideña).
- Fuga de datos: por qué las features usan solo datos antes del corte.
- Por qué ROC-AUC y PR-AUC y no solo accuracy.
- Por qué una regresión logística como línea base; qué tan poco ganó XGBoost.
- Cómo leer un gráfico SHAP y qué es un valor SHAP en log-odds.
- KMeans: por qué log + escalado, cómo se eligió k=4.
- Qué guarda MLflow y para qué; por qué la API fija versiones de librerías.
- Qué hace cada línea del Dockerfile y docker-compose.

## Reglas
- Cita el archivo y la línea cuando la respuesta dependa del código.
- Si una pregunta destapa un error real en el proyecto, dilo y propón el
  arreglo en vez de inventar una defensa.
