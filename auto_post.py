import os
from groq import Groq
from telegram_poster import TelegramPoster
from linkedin_poster import LinkedinPoster
from dotenv import load_dotenv

load_dotenv()

def generate_post(topic):
    groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"Создай пост для социальных сетей на тему: {topic}. Пост должен быть информативным, engaging и не длиннее 200 символов."
    response = groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def main():
    topic = "Искусственный интеллект в бизнесе"  # Можно сделать параметром или случайным
    post_content = generate_post(topic)

    # Постинг в Telegram
    tg_poster = TelegramPoster()
    tg_result = tg_poster.post_text(post_content)
    print("Telegram post result:", tg_result)

    # Постинг в LinkedIn
    li_poster = LinkedinPoster()
    li_result = li_poster.post_text(post_content)
    print("LinkedIn post result:", li_result)

if __name__ == "__main__":
    main()