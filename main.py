import os
import random
import feedparser
import requests
from google import genai

# Настройки из Secrets
GEMINI_KEY = os.getenv('GEMINI_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Инициализация ИИ
client = genai.Client(api_key=GEMINI_KEY)

def rewrite_news(title):
    prompt = f"Напиши короткий пост для Telegram на русском про: {title}. В конце добавь IMAGE_PROMPT: [описание картинки на английском]"
    try:
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        full_text = response.text
        if "IMAGE_PROMPT:" in full_text:
            text, img_p = full_text.split("IMAGE_PROMPT:")
            return text.strip(), img_p.strip()
        return full_text, "artificial intelligence futuristic"
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        return title, "tech news"

def main():
    # 1. Получаем новость
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    title, link = feed.entries[0].title, feed.entries[0].link

    # 2. Проверка дубликатов
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новых новостей нет.")
                return

    # 3. Обработка
    print(f"Обрабатываю: {title}")
    post_text, img_prompt = rewrite_news(title)
    
    # 4. Генерация картинки и отправка
    seed = random.randint(1, 1000)
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={seed}"
    
    tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": img_url,
        "caption": f"{post_text}\n\n[Источник]({link})",
        "parse_mode": "Markdown"
    }
    
    r = requests.post(tg_url, data=payload)
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(link)
        print("Пост отправлен!")
    else:
        print(f"Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    main()
