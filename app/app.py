# Esta celda crea el archivo app.py: la aplicación que luego se despliega en Hugging Face.
# (%%writefile guarda en un archivo todo lo que está debajo; no lo ejecuta aquí.)
"""
Analista de datos con IA generativa y Spark sobre el Sistema de Alertas.
El usuario escribe una pregunta en lenguaje natural; el modelo GLM de Z.ai traduce esa
pregunta a código PySpark, el código se ejecuta sobre los datos reales y se muestra el resultado.
La interfaz es web con Gradio. La clave de Z.ai se lee desde la variable de entorno ZAI_API_KEY.
"""
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gradio as gr
from openai import OpenAI
from pyspark.sql import SparkSession, functions as F, types as T

# ---------- 1) Iniciar Spark ----------
spark = (
    SparkSession.builder
    .appName("analista-alertas")
    .master("local[*]")
    .config("spark.ui.enabled", "false")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# ---------- 1b) Cargar datos reales desde Excel ----------
# En Hugging Face el archivo viaja dentro del contenedor porque el Dockerfile lo copia a /app.
# En Colab o ejecución local, el archivo debe estar en el mismo directorio o se puede definir ALERTAS_XLSX.
ARCHIVO_XLSX = Path(os.environ.get("ALERTAS_XLSX", "SistemadeAlertas.xlsx"))
HOJA_XLSX = os.environ.get("ALERTAS_HOJA", "Data General")

COLUMNAS_RENOMBRADAS = {
    "id": "id",
    "Tipo de Alerta": "tipo_alerta",
    "País": "pais",
    "Fecha nacimiento": "fecha_nacimiento",
    "Genero": "genero",
    "Víctima del Conflicto armado": "victima_conflicto_armado",
    "Discapacidad": "discapacidad",
    "Etnia": "etnia",
    "Estrato": "estrato",
    "Tipo colegio": "tipo_colegio",
    "Jornada": "jornada",
    "Grado": "grado",
    "Localidad": "localidad",
    "UPZ": "upz",
    "Fecha": "fecha_alerta",
    "FechaNacReal": "fecha_nac_real",
    "FechaAlrtReal": "fecha_alrt_real",
    "Edad_caso": "edad_caso",
    "Edad_Real": "edad_real",
    "Nom_Loca": "localidad_nombre",
    "NivelAcad": "nivel_academico",
    "Año": "anio",
    "Semestre": "semestre",
    "Características diferenciales": "caracteristicas_diferenciales",
}

COLUMNAS_FECHA = ["fecha_nacimiento", "fecha_alerta", "fecha_nac_real", "fecha_alrt_real"]
COLUMNAS_ENTERAS = ["id", "estrato", "edad_caso", "edad_real", "anio", "semestre"]
COLUMNAS_TEXTO = [
    "tipo_alerta", "pais", "genero", "victima_conflicto_armado", "discapacidad",
    "etnia", "tipo_colegio", "jornada", "grado", "localidad", "upz",
    "localidad_nombre", "nivel_academico", "caracteristicas_diferenciales"
]

SCHEMA_ALERTAS = T.StructType([
    T.StructField("id", T.LongType(), True),
    T.StructField("tipo_alerta", T.StringType(), True),
    T.StructField("pais", T.StringType(), True),
    T.StructField("fecha_nacimiento", T.DateType(), True),
    T.StructField("genero", T.StringType(), True),
    T.StructField("victima_conflicto_armado", T.StringType(), True),
    T.StructField("discapacidad", T.StringType(), True),
    T.StructField("etnia", T.StringType(), True),
    T.StructField("estrato", T.IntegerType(), True),
    T.StructField("tipo_colegio", T.StringType(), True),
    T.StructField("jornada", T.StringType(), True),
    T.StructField("grado", T.StringType(), True),
    T.StructField("localidad", T.StringType(), True),
    T.StructField("upz", T.StringType(), True),
    T.StructField("fecha_alerta", T.DateType(), True),
    T.StructField("fecha_nac_real", T.DateType(), True),
    T.StructField("fecha_alrt_real", T.DateType(), True),
    T.StructField("edad_caso", T.IntegerType(), True),
    T.StructField("edad_real", T.IntegerType(), True),
    T.StructField("localidad_nombre", T.StringType(), True),
    T.StructField("nivel_academico", T.StringType(), True),
    T.StructField("anio", T.IntegerType(), True),
    T.StructField("semestre", T.IntegerType(), True),
    T.StructField("caracteristicas_diferenciales", T.StringType(), True),
])


def _convertir_fecha_excel(serie: pd.Series) -> pd.Series:
    """Convierte columnas de fecha leídas desde Excel a objetos date o None."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        fechas = pd.to_datetime(serie, errors="coerce")
    else:
        serie_num = pd.to_numeric(serie, errors="coerce")
        proporcion_numerica = serie_num.notna().mean()
        if proporcion_numerica > 0.80:
            fechas = pd.to_datetime(serie_num, unit="D", origin="1899-12-30", errors="coerce")
        else:
            fechas = pd.to_datetime(serie, errors="coerce")

    return fechas.apply(lambda x: None if pd.isna(x) else x.date())


def _entero_nullable(serie: pd.Series) -> pd.Series:
    serie_num = pd.to_numeric(serie, errors="coerce")
    return pd.Series([int(x) if pd.notna(x) else None for x in serie_num], index=serie.index, dtype="object")


def _texto_nullable(serie: pd.Series) -> pd.Series:
    def limpiar(x):
        if pd.isna(x):
            return None
        valor = str(x).strip()
        return valor if valor else None
    return serie.apply(limpiar)


def cargar_alertas_excel(ruta_excel: Path = ARCHIVO_XLSX, hoja: str = HOJA_XLSX):
    """Lee el Excel real, normaliza columnas, aplica tipos y devuelve un DataFrame de Spark."""
    if not ruta_excel.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta_excel}. El archivo debe subirse al Space o al entorno local."
        )

    pdf = pd.read_excel(ruta_excel, sheet_name=hoja, engine="openpyxl")
    pdf = pdf.rename(columns=COLUMNAS_RENOMBRADAS)

    columnas_esperadas = list(COLUMNAS_RENOMBRADAS.values())
    faltantes = [c for c in columnas_esperadas if c not in pdf.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas esperadas en el Excel: {faltantes}")

    pdf = pdf[columnas_esperadas].copy()

    for columna in COLUMNAS_FECHA:
        pdf[columna] = _convertir_fecha_excel(pdf[columna])
    for columna in COLUMNAS_ENTERAS:
        pdf[columna] = _entero_nullable(pdf[columna])
    for columna in COLUMNAS_TEXTO:
        pdf[columna] = _texto_nullable(pdf[columna])

    df_spark = spark.createDataFrame(pdf, schema=SCHEMA_ALERTAS)
    df_spark = (
        df_spark
        .withColumn("mes_alerta", F.month("fecha_alerta"))
        .withColumn("trimestre_alerta", F.quarter("fecha_alerta"))
    )
    return df_spark


df = cargar_alertas_excel()
ESQUEMA = ", ".join([f"{c} ({t})" for c, t in df.dtypes])

# ---------- 2) El LLM que escribe el código (GLM de Z.ai) ----------
MODELO_LLM = "glm-4.5-flash"

_cliente = None
def _get_cliente():
    """Crea el cliente OpenAI -> Z.ai la primera vez que se usa."""
    global _cliente
    if _cliente is None:
        api_key = os.environ.get("ZAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("Falta la variable de entorno ZAI_API_KEY. Configúrala como Secret en Hugging Face.")
        _cliente = OpenAI(api_key=api_key, base_url="https://api.z.ai/api/paas/v4")
    return _cliente

INSTRUCCION = f"""Eres un analista de datos experto en PySpark.
Existe un DataFrame de Spark llamado df con datos reales del Sistema de Alertas.
Columnas disponibles: {ESQUEMA}.
Escribe código PySpark que responda la pregunta del usuario.
Reglas estrictas:
- Usa únicamente df, spark y F (pyspark.sql.functions). No leas ni escribas archivos.
- Usa exactamente los nombres de columnas disponibles en el esquema.
- Para conteos usa F.count("*") y para promedios usa F.avg().
- Asigna SIEMPRE el resultado final a una variable llamada resultado.
- Si el resultado es una tabla, deja resultado como un DataFrame de Spark y no uses .show().
- No importes librerías, no uses os, no uses open, no leas ni escribas archivos.
- Devuelve SOLO el código Python, sin explicaciones ni bloques de markdown."""


def generar_codigo(pregunta):
    """Pide al modelo GLM el código PySpark para la pregunta y limpia la respuesta."""
    r = _get_cliente().chat.completions.create(
        model=MODELO_LLM,
        messages=[
            {"role": "system", "content": INSTRUCCION},
            {"role": "user", "content": pregunta},
        ],
    )
    codigo = r.choices[0].message.content.strip()
    if codigo.startswith("```"):
        codigo = codigo.strip("`")
        if codigo.lstrip().startswith("python"):
            codigo = codigo.lstrip()[len("python"):]
    return codigo.strip()

# ---------- 3) Ejecutar el código generado ----------
PROHIBIDO = [
    "import ", "__", "open(", "exec(", "eval(", "subprocess", "os.", "sys.",
    "read.", ".read(", "write.", ".write(", "saveAs", "to_csv", "to_excel"
]


def validar_codigo(codigo: str):
    codigo_min = codigo.lower()
    encontrados = [patron for patron in PROHIBIDO if patron.lower() in codigo_min]
    if encontrados:
        raise ValueError(f"El código generado usa instrucciones no permitidas: {encontrados}")


def ejecutar(codigo):
    """Ejecuta el código en un entorno controlado y devuelve 'resultado' como tabla."""
    validar_codigo(codigo)
    entorno = {"spark": spark, "df": df, "F": F, "resultado": None}
    exec(codigo, {"__builtins__": {}}, entorno)
    res = entorno["resultado"]
    if res is None:
        return None
    if hasattr(res, "toPandas"):
        return res.limit(50).toPandas()
    return pd.DataFrame({"resultado": [res]})

# ---------- 4) Unir todo: pregunta -> código -> resultado ----------
def analizar(pregunta):
    if not pregunta or not pregunta.strip():
        return "", None, None
    try:
        codigo = generar_codigo(pregunta)
    except Exception as e:
        return f"# Error al generar el código: {e}", None, None
    try:
        tabla = ejecutar(codigo)
    except Exception as e:
        return codigo, pd.DataFrame({"Error": [str(e)]}), None

    fig = None
    if tabla is not None and tabla.shape[1] == 2 and pd.api.types.is_numeric_dtype(tabla.iloc[:, 1]):
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.bar(tabla.iloc[:, 0].astype(str), tabla.iloc[:, 1])
        ax.set_ylabel(tabla.columns[1])
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
    return codigo, tabla, fig

# ---------- 5) Interfaz web ----------
EJEMPLOS = [
    "¿Cuántas alertas hay por tipo_alerta?",
    "Muestra las 10 localidades con más alertas en 2025",
    "¿Cuál es la distribución de alertas por genero?",
    "Calcula el promedio de edad_caso por nivel_academico",
    "Compara el número de alertas por anio y semestre",
]

with gr.Blocks(title="Analista de datos con IA - Sistema de Alertas") as demo:
    gr.Markdown(
        "# Analista de datos con IA y Spark\n"
        "Escribe una pregunta en lenguaje natural. La IA escribe el análisis en PySpark, "
        "se ejecuta sobre el Sistema de Alertas y se muestra el resultado."
    )
    pregunta = gr.Textbox(label="Tu pregunta", placeholder="¿Cuántas alertas hay por localidad_nombre?")
    btn = gr.Button("Analizar", variant="primary")
    gr.Examples(EJEMPLOS, inputs=pregunta)
    codigo_out = gr.Code(label="Código PySpark que escribió la IA", language="python")
    tabla_out = gr.Dataframe(label="Resultado")
    chart_out = gr.Plot(label="Gráfico, si aplica")
    btn.click(analizar, inputs=pregunta, outputs=[codigo_out, tabla_out, chart_out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
