import os
import random
import feedparser
import requests
from google import genai

# 1. Считываем секреты
API_KEY = os.getenv('GEMINI_KEY')
BOT_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 2. Настройка ИИ (только новый формат)
client = genai.Client(api_key=API_KEY)

def get_ai_content(title):
    prompt = f"Напиши короткий пост для Telegram на русском языке про новость: {title}. В самом конце сообщения напиши текст 'IMAGE_PROMPT: ' и добавь короткое описание картинки для этой новости на английском языке."
    try:
        # Используем современную модель flash
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        full_text = response.text
        
        if "IMAGE_PROMPT:" in full_text:
            post_parts = full_text.split("IMAGE_PROMPT:")
            return post_parts[0].strip(), post_parts[1].strip()
        return full_text, "artificial intelligence futuristic"
    except Exception as e:
        print(f"ОШИБКА GEMINI: {e}")
        return title, "tech news"

def main():
    # Получаем свежую новость
    url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    feed = feedparser.parse(url)
    if not feed.entries: return
    
    first_news = feed.entries[0]
    title, link = first_news.title, first_news.link

    # Проверка на повторы
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новых новостей пока нет.")
                return

    print(f"Обрабатываю: {title}")
    text, img_p = get_ai_content(title)
    
    # Генерация картинки
    img_url = f"https://pollinations.ai/p/{img_p.replace(' ', '%20')}?width=1080&height=1080&seed={random.randint(1,99999)}&model=flux"
    
    # Отправка в Telegram
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": CHAT_ID,
        "photo": img_url,
        "caption": f"{text}\n\n[Источник]({link})",
        "parse_mode": "Markdown"
    }
    
    res = requests.post(send_url, data=data)
    
    if res.status_code == 200:
        with open("last_link.txt", "w") as f:
            f.write(link)
        print("Успешно отправлено!")
    else:
        print(f"Ошибка Telegram: {res.text}")

if __name__ == "__main__":
    main()
