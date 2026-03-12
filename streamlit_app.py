import calendar
import os
import streamlit as st
import requests
from collections import defaultdict
from datetime import datetime, date, time
from dotenv import load_dotenv

load_dotenv()

MAX_PREVIEW_LENGTH = 100
REQUEST_TIMEOUT = 10

# Заголовок приложения
st.title("Post History Manager 🚀")

# Базовый URL вашего Flask API
BASE_URL = "http://127.0.0.1:5000"  # Замените на свой URL, если используется другое API

# Выбор действия в интерфейсе
menu = st.sidebar.selectbox("Menu", ["Create Post", "View History", "Calendar", "Configuration Status"])

if menu == "Create Post":
    st.header("Create a New Post")

    # Форма для создания нового поста
    platform = st.selectbox("Platform", ["Telegram", "LinkedIn"])
    content = st.text_area("Content", "Write your post here...")
    status = st.selectbox("Status", ["success", "failed"])
    post_date = st.date_input("Date", value=date.today())
    post_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0))

    if st.button("Create Post"):
        # Combine date and time into a full ISO 8601 timestamp
        combined_dt = datetime.combine(post_date, post_time)
        # Отправка данных через API к Flask
        response = requests.post(
            f"{BASE_URL}/post",
            json={
                "platform": platform,
                "content": content,
                "status": status,
                "timestamp": combined_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 201:
            st.success("Post created successfully!")
        else:
            st.error(f"Failed to create post: {response.text}")

elif menu == "View History":
    st.header("Post History")

    # Получение истории через API
    response = requests.get(f"{BASE_URL}/post/history", timeout=REQUEST_TIMEOUT)
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

elif menu == "Calendar":
    st.header("Posts Calendar 📅")

    # Получение истории через API
    response = requests.get(f"{BASE_URL}/post/history", timeout=REQUEST_TIMEOUT)
    if response.status_code == 200:
        history = response.json()
        if history:
            # Группировка постов по датам
            posts_by_date = defaultdict(list)
            for entry in history:
                _id, platform, content, status, raw_ts = entry
                try:
                    # ISO 8601 date: take the date portion before any 'T' separator
                    post_date = datetime.strptime(raw_ts.split("T")[0], "%Y-%m-%d").date()
                    posts_by_date[post_date].append(entry)
                except (ValueError, TypeError, AttributeError):
                    pass

            if posts_by_date:
                all_dates = sorted(posts_by_date.keys())

                # Формирование списка месяцев с постами
                seen = set()
                months = []
                for d in all_dates:
                    key = (d.year, d.month)
                    if key not in seen:
                        seen.add(key)
                        months.append(date(d.year, d.month, 1))

                month_labels = [m.strftime("%B %Y") for m in months]
                selected_label = st.selectbox("Select Month", month_labels)
                selected_month = months[month_labels.index(selected_label)]

                year = selected_month.year
                month = selected_month.month

                # Заголовки дней недели
                day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                header_cols = st.columns(7)
                for i, name in enumerate(day_names):
                    header_cols[i].markdown(f"**{name}**")

                # Сетка календаря
                for week in calendar.monthcalendar(year, month):
                    week_cols = st.columns(7)
                    for i, day in enumerate(week):
                        if day == 0:
                            week_cols[i].write("")
                        else:
                            cell_date = date(year, month, day)
                            if cell_date in posts_by_date:
                                day_posts = posts_by_date[cell_date]
                                count = len(day_posts)
                                with week_cols[i].expander(f"**{day}** 📌 {count}"):
                                    for post in day_posts:
                                        _id, platform, content, status, raw_ts = post
                                        st.write(f"**{platform}** — {status}")
                                        preview = content[:MAX_PREVIEW_LENGTH] + ("..." if len(content) > MAX_PREVIEW_LENGTH else "")
                                        st.write(preview)
                                        st.write("---")
                            else:
                                week_cols[i].write(str(day))
            else:
                st.info("No posts with valid dates found.")
        else:
            st.info("No posts in history.")
    else:
        st.error("Failed to fetch history.")

elif menu == "Configuration Status":
    st.header("Configuration Status ⚙️")
    st.write("Shows which API keys are loaded from your `.env` file. Actual values are never displayed.")

    required_vars = [
        ("GROQ_API_KEY", "Groq AI — content generation"),
        ("TELEGRAM_BOT_TOKEN", "Telegram — bot token"),
        ("TELEGRAM_CHAT_ID", "Telegram — channel/chat ID"),
        ("LINKEDIN_ACCESS_TOKEN", "LinkedIn — OAuth access token"),
        ("LINKEDIN_PROFILE_ID", "LinkedIn — profile/organization ID"),
    ]

    all_set = True
    for var, description in required_vars:
        value = os.environ.get(var)
        if value:
            st.success(f"✅ **{var}** — {description}")
        else:
            st.error(f"❌ **{var}** — {description} *(not set)*")
            all_set = False

    st.write("---")
    if all_set:
        st.success("All required environment variables are configured. You're good to go! 🚀")
    else:
        st.warning(
            "Some variables are missing. Open `.env` in your terminal and fill in the missing values:\n\n"
            "```bash\n"
            "nano .env\n"
            "```"
        )
