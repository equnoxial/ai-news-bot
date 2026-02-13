import os
import feedparser
import google.generativeai as genai
import requests
import random

# Настройки
RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/" # Можно заменить
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    item = feed.entries[0]
    return item.title, item.link

def rewrite_and_image_prompt(title):
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Напиши пост для Telegram канала 'Алгоритмы будущего' на основе новости: {title}.
    Сделай пост коротким (до 500 символов), интересным, с эмодзи. 
    В конце добавь ОДНУ строку 'IMAGE_PROMPT: [описание картинки на английском для генерации]'.
    """
    response = model.generate_content(prompt)
    text = response.text
    
    # Разделяем текст и промпт для картинки
    if "IMAGE_PROMPT:" in text:
        post_text, img_prompt = text.split("IMAGE_PROMPT:")
        return post_text.strip(), img_prompt.strip()
    return text, "futuristic artificial intelligence technology"

def send_to_telegram(text, img_prompt):
    # Генерация картинки через Pollinations.ai
    seed = random.randint(1, 100000)
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&model=flux"
    
    # Отправка фото в ТГ
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    data = {"chat_id": TG_CHAT_ID, "photo": img_url, "caption": text, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# Проверка, чтобы не постить одно и то же
def main():
    title, link = get_latest_news()
    
    # Простая проверка через файл
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read() == link:
                print("Новых новостей нет.")
                return

    post_text, img_prompt = rewrite_and_image_prompt(title)
    send_to_telegram(f"{post_text}\n\n[Источник]({link})", img_prompt)
    
    with open("last_link.txt", "w") as f:
        f.write(link)

if __name__ == "__main__":
    main()
