# Analista de datos con IA generativa y Spark — Sistema de Alertas

Asistente que convierte preguntas en lenguaje natural en código **PySpark** ejecutable y responde con una tabla y un gráfico. Proyecto integrador del curso *Computación en la Nube* — Maestría en Ciencia de Datos, Universidad Santo Tomás.

**Equipo:** Adrian Grateron · Jhonatan Smith Doncel · Jorge Emmanuel Marin

## Cómo funciona

```
pregunta del usuario → prompt al LLM (GLM de Z.ai) con el esquema real de df
→ código PySpark generado → validación → ejecución controlada → tabla + gráfico
```

- **Datos:** `SistemadeAlertas.xlsx`, hoja *Data General* (174.826 registros, alertas estudiantiles en Bogotá, ene-2025 a mar-2026). Se lee con pandas y se analiza como DataFrame de Spark con esquema explícito y variables derivadas (`mes_alerta`, `trimestre_alerta`).
- **Seguridad del código generado:** el modelo solo puede usar `df`, `spark` y `F`; la app bloquea `import`, `open`, `eval`, `exec`, `subprocess`, escrituras y accesos al sistema.
- **Interfaz:** Gradio, con preguntas libres y ejemplos.
- **Despliegue:** contenedor Docker en Hugging Face Spaces; la clave de Z.ai se configura como *secret* `ZAI_API_KEY`.

## Estructura

| Ruta | Contenido |
|---|---|
| `notebooks/analista_ia_spark_alertas.ipynb` | Notebook completo: dependencias, carga en Spark, LLM, app Gradio, Dockerfile y publicación |
| `docs/informe_proyecto_integrador.pdf` | Informe final del proyecto |
| `requirements.txt` | Versiones usadas |

## Ejecución

1. Abrir el notebook en Google Colab.
2. Subir `SistemadeAlertas.xlsx` al entorno (o definir `ALERTAS_XLSX`).
3. Ingresar la API key de Z.ai cuando se solicite (se pide con `getpass`, nunca queda en el código).
4. Opcional: token *Write* de Hugging Face para publicar el Space.

## Datos

El archivo de datos **no se incluye** en este repositorio porque contiene información sensible de estudiantes. Para reproducir el proyecto se requiere acceso autorizado a la fuente.

## Tecnologías

PySpark · Gradio · OpenAI SDK (GLM de Z.ai) · Docker · Hugging Face Spaces
