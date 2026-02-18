import os
from google import genai
import feedparser
import requests
import random

# 1. Настройки (берем из секретов GitHub)
RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"
GEMINI_KEY = os.getenv('GEMINI_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

# 2. Инициализация клиента Gemini (НОВЫЙ СТАНДАРТ)
client = genai.Client(api_key=GEMINI_KEY)

def get_latest_news():
    """Получаем самую свежую новость из RSS"""
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None, None
    item = feed.entries[0]
    return item.title, item.link

def rewrite_and_image_prompt(title):
    """Рерайт новости через ИИ и создание промпта для картинки"""
    prompt = f"""
    Напиши короткий, захватывающий пост для Telegram на русском языке на основе новости: {title}.
    Используй эмодзи. Сделай текст интересным.
    В конце добавь ОДНУ строку 'IMAGE_PROMPT: [описание картинки на английском для генерации]'.
    """
    
    try:
        # Генерация контента через новую библиотеку
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text
        
        if "IMAGE_PROMPT:" in text:
            post_text, img_prompt = text.split("IMAGE_PROMPT:")
            return post_text.strip(), img_prompt.strip()
        
        return text, "futuristic artificial intelligence technology"
    
    except Exception as e:
        print(f"ОШИБКА GEMINI: {e}")
        # Если ИИ упал, возвращаем заголовок как есть
        return f"🔥 {title}", "artificial intelligence futuristic"

def send_to_telegram(text, img_prompt, link):
    """Генерация картинки и отправка поста в Telegram"""
    seed = random.randint(1, 100000)
    # Используем Pollinations для генерации картинки на лету
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&model=flux"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    data = {
        "chat_id": TG_CHAT_ID, 
        "photo": img_url, 
        "caption": f"{text}\n\n[Читать новость]({link})", 
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print(f"Ошибка Telegram: {r.text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def main():
    title, link = get_latest_news()
    if not title: 
        print("Не удалось получить новости.")
        return

    # Проверка на дубликаты (память бота)
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новых новостей нет.")
                return

    print(f"Обрабатываю новость: {title}")
    post_text, img_prompt = rewrite_and_image_prompt(title)
    send_to_telegram(post_text, img_prompt, link)

    # Запоминаем ссылку
    with open("last_link.txt", "w") as f:
        f.write(link)
    print("Пост успешно отправлен!")

if __name__ == "__main__":
    main()
