FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт запускаемым (ОБЯЗАТЕЛЬНО)
RUN chmod +x run.sh

EXPOSE 8501

# Запускаем скрипт-посредник
ENTRYPOINT ["./run.sh"]
