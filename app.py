import streamlit as st
import os
from datetime import datetime
from groq import Groq
from telegram_poster import TelegramPoster
from linkedin_poster import LinkedinPoster
from dotenv import load_dotenv

load_dotenv()

# Инициализация Groq
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

st.title("VYUD AI Scheduler")
st.subheader("Автопостинг для Telegram и LinkedIn с AI-генерацией контента")

# Табы
tab1, tab2, tab3 = st.tabs(["Календарь", "Создать пост", "Настройки"])

with tab1:
    st.header("Календарь постов")
    # Простой календарь (можно улучшить)
    st.write("Запланированные посты:")
    # Здесь можно добавить логику для отображения постов

with tab2:
    st.header("Создать пост")
    platform = st.selectbox("Платформа", ["telegram", "linkedin"])
    topic = st.text_input("Тема для генерации поста")
    if st.button("🤖 Сгенерировать"):
        if topic:
            with st.spinner("Генерация поста..."):
                prompt = f"Создай пост для {platform} на тему: {topic}. Пост должен быть информативным, engaging и не длиннее 200 символов."
                response = groq.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200
                )
                generated_post = response.choices[0].message.content.strip()
            st.text_area("Сгенерированный пост", generated_post, height=100)
            if st.button("Опубликовать"):
                if platform == "telegram":
                    poster = TelegramPoster()
                elif platform == "linkedin":
                    poster = LinkedinPoster()
                result = poster.post_text(generated_post)
                st.success("Пост опубликован!")
                st.json(result)
        else:
            st.error("Введите тему")

with tab3:
    st.header("Настройки")
    st.write("API ключи настроены в .env файле")
    # Здесь можно добавить форму для ввода ключей, но для безопасности лучше в .env