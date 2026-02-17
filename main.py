import os
import feedparser
import google.generativeai as genai
import requests
import random

# Настройки (берем из секретов GitHub для безопасности)
RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"
GEMINI_KEY = os.getenv('GEMINI_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None, None
    item = feed.entries[0]
    return item.title, item.link

def rewrite_and_image_prompt(title):
    genai.configure(api_key=GEMINI_KEY)
    # На GitHub эта модель работает идеально
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Напиши короткий, захватывающий пост для Telegram на русском языке на основе новости: {title}.
    Используй эмодзи. Сделай текст интересным для экспертов.
    В конце добавь ОДНУ строку 'IMAGE_PROMPT: [описание картинки на английском для генерации]'.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "IMAGE_PROMPT:" in text:
            post_text, img_prompt = text.split("IMAGE_PROMPT:")
            return post_text.strip(), img_prompt.strip()
        return text, "futuristic artificial intelligence technology"
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        return f"🔥 {title}", "artificial intelligence futuristic"

def send_to_telegram(text, img_prompt, link):
    seed = random.randint(1, 100000)
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&model=flux"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    data = {
        "chat_id": TG_CHAT_ID, 
        "photo": img_url, 
        "caption": f"{text}\n\n[Читать новость]({link})", 
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

def main():
    title, link = get_latest_news()
    if not title: return

    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read() == link:
                print("Новых новостей нет.")
                return

    post_text, img_prompt = rewrite_and_image_prompt(title)
    send_to_telegram(post_text, img_prompt, link)

    with open("last_link.txt", "w") as f:
        f.write(link)

if __name__ == "__main__":
    main()
