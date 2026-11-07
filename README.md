# Analista de datos con IA generativa y Spark — Sistema de Alertas

Asistente que convierte preguntas en lenguaje natural en código **PySpark** ejecutable y responde con una tabla y un gráfico. Proyecto integrador del curso *Computación en la Nube* — Maestría en Ciencia de Datos, Universidad Santo Tomás.

**Demo:** [Hugging Face Space](https://huggingface.co/spaces/Adrian0812/analista-datos-ia) (requiere que el Space esté activo)

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
| `app/app.py` | Aplicación Gradio extraída del notebook: carga en Spark, llamada al LLM, validación y ejecución del código generado |
| `app/Dockerfile` | Imagen usada en Hugging Face Spaces (Python 3.11 + Java para Spark) |
| `docs/informe_proyecto_integrador.pdf` | Informe final del proyecto |
| `requirements.txt` | Versiones usadas |

## Ejecución

1. Abrir el notebook en Google Colab.
2. Subir `SistemadeAlertas.xlsx` al entorno (o definir `ALERTAS_XLSX`).
3. Ingresar la API key de Z.ai cuando se solicite (se pide con `getpass`, nunca queda en el código).
4. Opcional: token *Write* de Hugging Face para publicar el Space.

## Ejecución local de la app

```bash
cd app
pip install -r requirements.txt          # requiere Java 17+ para PySpark
export ZAI_API_KEY="tu_clave"            # nunca se escribe en el código
export ALERTAS_XLSX="/ruta/SistemadeAlertas.xlsx"
python app.py                            # abre la interfaz en http://localhost:7860
```

## Limitaciones y seguridad

- **Ejecución de código generado por un LLM.** El código se ejecuta con `exec` sin *builtins* y tras una lista de patrones prohibidos (`import`, `open(`, `eval(`, `__`, etc.). Es una mitigación razonable para un prototipo académico, pero una lista negra no es una frontera de seguridad: en producción conviene validar el árbol sintáctico (AST) con una lista blanca de operaciones de DataFrame y ejecutar en un proceso aislado con límites de tiempo y memoria.
- **Sin evaluación sistemática.** No se midió la exactitud del código generado frente a un conjunto de preguntas de referencia; un siguiente paso es construir ese banco de preguntas con respuestas esperadas y reportar la tasa de aciertos.
- **Datos en la imagen.** El `Dockerfile` copia el Excel dentro del contenedor. Si el Space es público, cualquiera puede descargar el archivo; para datos sensibles conviene un Space privado o cargar los datos desde almacenamiento con control de acceso.
- Las respuestas dependen del modelo GLM de Z.ai y pueden variar entre ejecuciones.

## Datos

El archivo de datos **no se incluye** en este repositorio porque contiene información sensible de estudiantes. Para reproducir el proyecto se requiere acceso autorizado a la fuente.

## Tecnologías

PySpark · Gradio · OpenAI SDK (GLM de Z.ai) · Docker · Hugging Face Spaces

## Licencia

El contenido de este repositorio (código, documentos y figuras propias) se publica bajo la licencia [Creative Commons Atribución 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.es): puede compartirse y adaptarse citando a los autores. Ver [`LICENSE`](LICENSE). El archivo de datos `SistemadeAlertas.xlsx` no forma parte del repositorio ni de esta licencia.
