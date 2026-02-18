import os
import random
import feedparser
import requests
from google import genai  # ИСПОЛЬЗУЕМ ТОЛЬКО ЭТОТ ИМПОРТ

# Считываем секреты
API_KEY = os.getenv('GEMINI_KEY')
BOT_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Инициализируем клиента
client = genai.Client(api_key=API_KEY)

def get_ai_content(title):
    prompt = f"Напиши пост для Telegram на русском про: {title}. В конце добавь IMAGE_PROMPT: [описание для картинки]"
    try:
        # ОБРАТИ ВНИМАНИЕ: здесь нет models/ в начале названия
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text, "technology"
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return title, "tech"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    
    entry = feed.entries[0]
    title, link = entry.title, entry.link

    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новостей нет.")
                return

    print(f"Обрабатываю: {title}")
    text, img_p = get_ai_content(title)
    
    # Генерация картинки через Flux модель
    seed = random.randint(1, 1000000)
    img_url = f"https://pollinations.ai/p/{img_p.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": img_url,
        "caption": f"🤖 *НОВОСТЬ ИИ*\n\n{text}\n\n[Источник]({link})",
        "parse_mode": "Markdown"
    }
    
    r = requests.post(send_url, data=payload)
    if r.status_code == 200:
        with open("last_link.txt", "w") as f:
            f.write(link)
        print("Готово!")
    else:
        print(f"Ошибка ТГ: {r.text}")

if __name__ == "__main__":
    main()
