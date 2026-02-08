import streamlit as st
import requests

# Заголовок приложения
st.title("Post History Manager 🚀")

# Базовый URL вашего Flask API
BASE_URL = "http://127.0.0.1:5000"  # Замените на свой URL, если используется другое API

# Выбор действия в интерфейсе
menu = st.sidebar.selectbox("Menu", ["Create Post", "View History"])

if menu == "Create Post":
    st.header("Create a New Post")

    # Форма для создания нового поста
    platform = st.selectbox("Platform", ["Telegram", "LinkedIn"])
    content = st.text_area("Content", "Write your post here...")
    status = st.selectbox("Status", ["success", "failed"])
    timestamp = st.text_input("Timestamp (e.g., 2026-02-03)")

    if st.button("Create Post"):
        # Отправка данных через API к Flask
        response = requests.post(
            f"{BASE_URL}/post",
            json={
                "platform": platform,
                "content": content,
                "status": status,
                "timestamp": timestamp,
            },
        )
        if response.status_code == 201:
            st.success("Post created successfully!")
        else:
            st.error(f"Failed to create post: {response.text}")

elif menu == "View History":
    st.header("Post History")

    # Получение истории через API
    response = requests.get(f"{BASE_URL}/post/history")
    if response.status_code == 200:
        history = response.json()
        if history:
            for entry in history:
                st.write(f"**Platform**: {entry[1]}")
                st.write(f"**Content**: {entry[2]}")
                st.write(f"**Status**: {entry[3]}")
                st.write(f"**Timestamp**: {entry[4]}")
                st.write("---")
        else:
            st.info("No posts in history.")
    else:
        st.error("Failed to fetch history.")
