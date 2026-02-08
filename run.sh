#!/bin/bash

# 1. Запускаем Flask (мозги) в фоновом режиме (&)
python3 app.py &

# 2. Ждем 5 секунд, чтобы Flask успел проснуться
sleep 5

# 3. Запускаем Streamlit (лицо)
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
