# Используем легкий образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения
COPY . .

# Создаем директорию для Streamlit конфигурации
RUN mkdir -p /root/.streamlit

# Копируем конфигурацию Streamlit
COPY .streamlit/config.toml /root/.streamlit/config.toml

# Открываем порт 8501 для Streamlit
EXPOSE 8501

# Проверка здоровья контейнера
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Команда запуска Streamlit приложения
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
