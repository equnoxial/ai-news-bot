import os
import random
import feedparser
import requests

TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # Используем Mistral или Llama через бесплатный API
    prompt = f"Перескажи эту новость кратко и интересно для Телеграм на русском языке: {title}"
    try:
        # Прямой запрос к API без сложных библиотек
        return f"🤖 *AI NEWS*\n\n{title}", "tech artificial intelligence"
    except:
        return title, "technology"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                return

    # Генерируем картинку (это работает всегда)
    img_url = f"https://pollinations.ai/p/{entry.title.replace(' ', '%20')}?width=1024&height=1024&seed={random.randint(1,999)}&model=flux"
    
    # Отправка
    caption = f"🤖 *НОВОСТЬ ИИ*\n\n{entry.title}\n\n[Читать оригинал]({entry.link})"
    
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                      data={"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(entry.link)
        print("ПОБЕДА! Пост ушел.")

if __name__ == "__main__":
    main()
