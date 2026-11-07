FROM python:3.11-slim

# Spark necesita Java: se instala el kit de desarrollo de Java.
RUN apt-get update && apt-get install -y default-jdk && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY SistemadeAlertas.xlsx .

EXPOSE 7860
CMD ["python", "app.py"]