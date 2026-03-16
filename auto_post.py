import os
from google import genai
from telegram_poster import TelegramPoster
from linkedin_poster import LinkedinPoster
from dotenv import load_dotenv

load_dotenv()

def get_gemini_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None

def generate_post(topic):
    api_key = get_gemini_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment or .streamlit/secrets.toml")
        
    client = genai.Client(api_key=api_key)
    prompt = f"Создай пост для социальных сетей на тему: {topic}. Пост должен быть информативным, engaging и не длиннее 200 символов."
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text.strip()

def main():
    topic = "Искусственный интеллект в бизнесе"  # Можно сделать параметром или случайным
    try:
        post_content = generate_post(topic)
    except Exception as e:
        print(f"Error generating post: {e}")
        return

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