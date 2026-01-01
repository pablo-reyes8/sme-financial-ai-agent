# SME Finance AI Agent

Chatbot para PyMEs en Colombia con Flask + LangChain. Incluye un modulo de conocimiento local, recuperacion semantica con Chroma y un flujo conversacional con respuestas estructuradas y eficientes.

## Caracteristicas

- **Conocimiento local versionado** en `sme_agent/knowledge` para asegurar estabilidad y despliegues reproducibles.
- **Recuperacion semantica** con umbral de similitud y ventanas de memoria conversacional.
- **Prompts profesionales** con protocolo de asesoria y manejo de cortesia.
- **UI moderna** con modo oscuro, respuestas rapidas y animaciones sutiles.
- **Persistencia** de conversaciones y preferencias del usuario en SQLite.
- **Calculadoras financieras** basicas para punto de equilibrio, liquidez, margenes y flujo de caja.

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
- `DATABASE_URL=sqlite:///data/app.db` para persistir conversaciones y preferencias.
- `ENABLE_METRICS=true` para exponer `/metrics` con estadisticas basicas.

## Guardar datos del usuario

Puedes guardar datos con mensajes como:

```
guardar: sector=alimentos
guardar: ciudad=Bogota
```

Para verlos, escribe: `mis datos`.

## Calculadoras rapidas

Ejemplos de consultas que activan calculos automaticos:

```
calcular punto de equilibrio: costos fijos 1000000, precio 12000, costo variable 5000
flujo de caja con ingresos 2000000 y gastos 1500000
margen bruto con ventas 5000000 y costo de ventas 3000000
razon corriente con activo corriente 4000000 y pasivo corriente 2500000
```

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
