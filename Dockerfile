FROM python:3.9-slim

# Installera nödvändiga beroenden
RUN apt-get update && apt-get install -y wget libnss3 libatk-bridge2.0-0 libxcomposite1 libxrandr2 libxdamage1 libgbm-dev libasound2

# Installera Python-paket
COPY requirements.txt .
RUN pip install -r requirements.txt

# Installera Playwright-webbläsare
RUN playwright install

# Kopiera appen
COPY . /app
WORKDIR /app

# Starta Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
