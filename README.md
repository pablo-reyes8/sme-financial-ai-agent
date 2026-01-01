# SME Finance AI Agent

Chatbot para PyMEs en Colombia con Flask + LangChain. Incluye un modulo de conocimiento local, recuperacion semantica con Chroma y un flujo conversacional con respuestas estructuradas.

## Caracteristicas

- **Conocimiento local versionado** en `sme_agent/knowledge` para asegurar estabilidad y despliegues reproducibles.
- **Recuperacion semantica** con umbral de similitud y ventanas de memoria conversacional.
- **Prompts profesionales** con protocolo de asesoria y manejo de cortesia.
- **UI moderna** con modo oscuro, respuestas rapidas y animaciones sutiles.

## Estructura del proyecto

```
.
- app.py
- sme_agent/
  - factory.py
  - main.py
  - chains.py
  - config.py
  - prompts.py
  - services/
  - templates/
  - static/
  - knowledge/
- tests/
- data/
```

## Configuracion

1) Crea un `.env` desde `.env.example` y define `OPENAI_API_KEY`.
2) Instala dependencias:

```bash
pip install -r requirements.txt
```

3) Ejecuta la app:

```bash
python app.py
```

Opcionalmente puedes correr con Flask:

```bash
flask --app sme_agent.main run
```

## Ajustes recomendados

- `ENABLE_WEB_SOURCES=true` para agregar fuentes web (se recomienda rebuild).
- `REBUILD_VECTORSTORE=true` si cambias los documentos de conocimiento.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

## Despliegue con Docker

```bash
docker build -t sme-agent .
docker run -p 8000:8000 --env-file .env sme-agent
```

## Notas

Este proyecto da orientacion general. Para temas legales o tributarios complejos, valida con profesionales y entidades oficiales.
