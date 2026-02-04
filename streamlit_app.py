import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime, timedelta
import calendar

# Заголовок приложения
st.title("Post History Manager 🚀")

# Настройка Gemini API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.warning("⚠️ GEMINI_API_KEY не настроен в secrets.toml. Функция AI Strategy Generator будет недоступна.")

# Базовый URL вашего Flask API
BASE_URL = "http://127.0.0.1:5000"  # Замените на свой URL, если используется другое API

# Выбор действия в интерфейсе
menu = st.sidebar.selectbox("Menu", ["Create Post", "View History", "AI Strategy Generator"])

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

elif menu == "AI Strategy Generator":
    st.header("🤖 AI Strategy Generator")
    st.markdown("Генерируйте месячный план контент-стратегии с помощью AI")
    
    # Проверка наличия API ключа
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.error("❌ GEMINI_API_KEY не настроен. Пожалуйста, добавьте его в .streamlit/secrets.toml")
        st.stop()
    
    # Форма ввода данных
    with st.form("strategy_form"):
        st.subheader("📝 Параметры генерации")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme_product = st.text_input(
                "Тема/Продукт",
                placeholder="Например: VYUD AI - конструктор курсов",
                help="Опишите ваш продукт или тему контента"
            )
            
            target_audience = st.text_input(
                "Целевая аудитория",
                placeholder="Например: Предприниматели, создающие онлайн-курсы",
                help="Кто ваша целевая аудитория?"
            )
        
        with col2:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            year = st.number_input(
                "Год",
                min_value=2024,
                max_value=2030,
                value=current_year,
                step=1
            )
            
            month = st.selectbox(
                "Месяц",
                options=list(range(1, 13)),
                index=current_month - 1,
                format_func=lambda x: calendar.month_name[x]
            )
        
        context_materials = st.text_area(
            "Дополнительные контекстные материалы",
            placeholder="Добавьте любую информацию, которая поможет AI лучше понять контекст...",
            height=150,
            help="Дополнительная информация о продукте, особенностях аудитории, tone of voice и т.д."
        )
        
        submitted = st.form_submit_button("🚀 Сгенерировать план", type="primary")
    
    if submitted:
        if not theme_product or not target_audience:
            st.error("❌ Пожалуйста, заполните обязательные поля: Тема/Продукт и Целевая аудитория")
        else:
            # Генерация плана
            with st.spinner("🤖 AI генерирует контент-стратегию... Это может занять до минуты..."):
                try:
                    plan_data = generate_monthly_plan(
                        theme_product=theme_product,
                        target_audience=target_audience,
                        year=year,
                        month=month,
                        context=context_materials
                    )
                    
                    if plan_data:
                        st.success("✅ План успешно сгенерирован!")
                        
                        # Сохранение данных в session state
                        st.session_state['generated_plan'] = plan_data
                        st.session_state['plan_params'] = {
                            'theme': theme_product,
                            'audience': target_audience,
                            'year': year,
                            'month': month
                        }
                        
                except Exception as e:
                    st.error(f"❌ Ошибка при генерации плана: {str(e)}")
                    st.error("Попробуйте еще раз или проверьте настройки API.")
    
    # Отображение сгенерированного плана
    if 'generated_plan' in st.session_state and st.session_state['generated_plan']:
        st.markdown("---")
        st.subheader("📊 Сгенерированный контент-план")
        
        # Информация о параметрах
        params = st.session_state.get('plan_params', {})
        if params:
            st.info(f"**Тема:** {params.get('theme')} | **ЦА:** {params.get('audience')} | **Период:** {calendar.month_name[params.get('month')]} {params.get('year')}")
        
        # Создание DataFrame
        df = pd.DataFrame(st.session_state['generated_plan'])
        
        # Убедимся, что все необходимые колонки присутствуют
        required_columns = ['date', 'platform', 'content_text', 'media_type', 'media_description', 'media_url']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Переупорядочивание колонок
        df = df[required_columns]
        
        # Отображение редактируемой таблицы
        st.markdown("**💡 Совет:** Вы можете редактировать любые поля, особенно добавьте ссылки на медиа в колонку `media_url`")
        
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn(
                    "Дата",
                    format="YYYY-MM-DD",
                    help="Дата публикации поста"
                ),
                "platform": st.column_config.SelectboxColumn(
                    "Платформа",
                    options=["LinkedIn", "Telegram", "Instagram", "Facebook"],
                    help="Выберите платформу для публикации"
                ),
                "content_text": st.column_config.TextColumn(
                    "Текст поста",
                    help="Содержание поста",
                    width="large"
                ),
                "media_type": st.column_config.SelectboxColumn(
                    "Тип медиа",
                    options=["image", "video", "carousel", "none"],
                    help="Тип медиа-контента"
                ),
                "media_description": st.column_config.TextColumn(
                    "Описание медиа",
                    help="Что должно быть на изображении/видео"
                ),
                "media_url": st.column_config.TextColumn(
                    "URL медиа",
                    help="Вставьте ссылку на Google Drive, S3 или другое хранилище"
                )
            }
        )
        
        # Обновление session state
        st.session_state['edited_plan'] = edited_df
        
        # Кнопки действий
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("✅ Approve & Schedule", type="primary"):
                success_count = 0
                error_count = 0
                
                with st.spinner("Сохранение постов..."):
                    for _, row in edited_df.iterrows():
                        try:
                            response = requests.post(
                                f"{BASE_URL}/post",
                                json={
                                    "platform": row['platform'],
                                    "content": row['content_text'],
                                    "status": "scheduled",
                                    "timestamp": str(row['date']),
                                },
                            )
                            if response.status_code == 201:
                                success_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Ошибка при сохранении поста: {str(e)}")
                
                if success_count > 0:
                    st.success(f"✅ Успешно сохранено постов: {success_count}")
                if error_count > 0:
                    st.warning(f"⚠️ Ошибок при сохранении: {error_count}")
        
        with col2:
            # Экспорт в CSV
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Скачать CSV",
                data=csv,
                file_name=f"content_plan_{params.get('year')}_{params.get('month'):02d}.csv",
                mime="text/csv",
            )
        
        with col3:
            if st.button("🗑️ Очистить"):
                del st.session_state['generated_plan']
                del st.session_state['plan_params']
                if 'edited_plan' in st.session_state:
                    del st.session_state['edited_plan']
                st.rerun()


def generate_monthly_plan(theme_product: str, target_audience: str, year: int, month: int, context: str = "") -> list:
    """
    Генерирует месячный контент-план с помощью Gemini API.
    
    Args:
        theme_product: Тема или продукт
        target_audience: Целевая аудитория
        year: Год для планирования
        month: Месяц для планирования (1-12)
        context: Дополнительный контекст
    
    Returns:
        List of dictionaries с постами или None при ошибке
    """
    try:
        # Получаем список рабочих дней месяца
        weekdays = get_weekdays_in_month(year, month)
        weekdays_str = ", ".join([d.strftime("%Y-%m-%d") for d in weekdays])
        
        # Формирование промпта с Chain of Thought
        prompt = f"""Ты - эксперт по контент-маркетингу и SMM-стратегии. Твоя задача - создать детальный месячный план публикаций.

**ШАГИ АНАЛИЗА (Chain of Thought):**

1. **Анализ темы и продукта:**
   - Тема/Продукт: {theme_product}
   - Что это за продукт? Какие его основные преимущества?
   - Какие боли решает?

2. **Анализ целевой аудитории:**
   - ЦА: {target_audience}
   - Каковы их потребности и интересы?
   - Какой контент будет для них ценным?

3. **Разработка стратегии:**
   - Предложи стратегию публикаций (например, "3 дня образовательного контента + 1 день продающего", "принцип 80/20", "сториттелинг + кейсы + продажи")
   - Обоснуй выбранную стратегию для данной ЦА

4. **Генерация контента:**
   - Создай посты для каждого будничного дня месяца
   - Рабочие дни месяца {calendar.month_name[month]} {year}: {weekdays_str}
   - Каждый пост должен быть уникальным и следовать выбранной стратегии
   - Учитывай различные форматы: советы, кейсы, статистика, вопросы к аудитории, storytelling

**Дополнительный контекст:**
{context if context else "Не предоставлен"}

**КРИТИЧЕСКИ ВАЖНО:**
Верни ТОЛЬКО валидный JSON массив, БЕЗ дополнительного текста до или после. Формат:

[
  {{
    "date": "YYYY-MM-DD",
    "platform": "LinkedIn",
    "content_text": "Текст поста с эмодзи и форматированием для LinkedIn",
    "media_type": "image",
    "media_description": "Детальное описание того, что должно быть на изображении/видео",
    "media_url": ""
  }}
]

**Требования к постам:**
- Текст должен быть вовлекающим и ценным
- Используй эмодзи для улучшения читаемости
- Для LinkedIn: профессиональный тон, но дружелюбный
- Варьируй длину постов (короткие, средние, длинные)
- Варьируй типы медиа (image, video, carousel, none)
- Давай конкретные описания для media_description, чтобы дизайнер понял, что создавать

Начинай генерацию!"""

        # Инициализация модели
        # Попробуем сначала gemini-2.0-flash, если не получится - gemini-1.5-pro-latest
        models_to_try = ["gemini-2.0-flash-exp", "gemini-1.5-pro-latest", "gemini-1.5-pro"]
        
        response_text = None
        used_model = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.8,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=8192,
                    )
                )
                response_text = response.text
                used_model = model_name
                break
            except Exception as e:
                if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                    continue
                else:
                    raise e
        
        if not response_text:
            raise Exception("Не удалось получить ответ от Gemini API")
        
        # Парсинг JSON из ответа
        # Иногда модель может вернуть текст до/после JSON, поэтому нужно его извлечь
        json_str = extract_json_from_text(response_text)
        
        if not json_str:
            raise ValueError("Не удалось извлечь JSON из ответа модели")
        
        # Парсинг JSON
        posts = json.loads(json_str)
        
        # Валидация структуры
        if not isinstance(posts, list):
            raise ValueError("Ответ должен быть массивом постов")
        
        # Валидация каждого поста
        required_fields = ['date', 'platform', 'content_text', 'media_type', 'media_description', 'media_url']
        for post in posts:
            for field in required_fields:
                if field not in post:
                    post[field] = ""
        
        return posts
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Ошибка парсинга JSON: {str(e)}")
        st.error("Модель вернула невалидный JSON. Попробуйте еще раз.")
        return None
    except Exception as e:
        st.error(f"❌ Ошибка при генерации плана: {str(e)}")
        return None


def extract_json_from_text(text: str) -> str:
    """
    Извлекает JSON из текста, который может содержать дополнительный текст.
    """
    # Удаляем markdown code blocks если есть
    text = text.strip()
    
    # Если текст начинается с ```json или ```
    if text.startswith("```"):
        lines = text.split("\n")
        # Удаляем первую строку с ```
        lines = lines[1:]
        # Удаляем последнюю строку с ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    # Пытаемся найти начало и конец JSON массива
    start_idx = text.find("[")
    end_idx = text.rfind("]")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    return text


def get_weekdays_in_month(year: int, month: int) -> list:
    """
    Возвращает список рабочих дней (понедельник-пятница) в указанном месяце.
    """
    # Первый день месяца
    first_day = datetime(year, month, 1)
    
    # Последний день месяца
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    weekdays = []
    current_day = first_day
    
    while current_day <= last_day:
        # 0 = Monday, 6 = Sunday
        if current_day.weekday() < 5:  # Monday to Friday
            weekdays.append(current_day)
        current_day += timedelta(days=1)
    
    return weekdays
