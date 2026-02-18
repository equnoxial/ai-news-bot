import os
import random
import feedparser
import requests
from google import genai

# Настройки
GEMINI_KEY = os.getenv('GEMINI_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Инициализация нового клиента
client = genai.Client(api_key=GEMINI_KEY)

def get_ai_content(title):
    # Используем стабильную 1.5 Flash
    model_id = "gemini-1.5-flash"
    prompt = f"Напиши короткий пост для Telegram на русском про: {title}. В конце добавь IMAGE_PROMPT: [описание картинки на английском для генерации]"
    
    try:
        print(f"Запрос к {model_id}...")
        response = client.models.generate_content(model=model_id, contents=prompt)
        text = response.text
        
        if "IMAGE_PROMPT:" in text:
            parts = text.split("IMAGE_PROMPT:")
            return parts[0].strip(), parts[1].strip()
        return text, "high-tech digital art"
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        return title, "artificial intelligence"

def main():
    # Парсим новости
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Проверка дублей
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новость уже была.")
                return

    print(f"Работаем с: {entry.title}")
    post_text, img_p = get_ai_content(entry.title)
    
    # Генерация картинки
    img_url = f"https://pollinations.ai/p/{img_p.replace(' ', '%20')}?width=1024&height=1024&seed={random.randint(1,999)}&model=flux"
    
    # Отправка
    msg = f"🤖 *AI NEWS*\n\n{post_text}\n\n[Читать оригинал]({entry.link})"
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                      data={"chat_id": CHAT_ID, "photo": img_url, "caption": msg, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(entry.link)
        print("Пост в канале!")

if __name__ == "__main__":
    main()
