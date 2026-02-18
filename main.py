import os
import random
import feedparser
import requests
import urllib.parse

HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    print(f"Запрос к ИИ для: {title}")
    api_url = "https://api-inference.huggingface.co/models/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<s>[INST] Напиши очень короткий пост для Телеграм на русском про это: {title}. Используй эмодзи. [/INST]"
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=15)
        if response.status_code == 200:
            result = response.json()
            text = result[0]['generated_text'].split("[/INST]")[-1].strip()
            if text: return text
    except:
        pass
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых новостей нет.")
                return

    post_text = get_ai_text(entry.title)
    
    # Кодируем заголовок для ссылки на картинку
    clean_title = urllib.parse.quote(entry.title)
    img_url = f"https://image.pollinations.ai/prompt/cyberpunk%20style%20{clean_title}?width=1080&height=1080&nologo=true&seed={random.randint(1,1000)}"
    
    # ТЕПЕРЬ БЕЗ ИСТОЧНИКА:
    caption = post_text
    
    print("Отправляю в Telegram...")
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                      data={"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(entry.link)
        print("ПОБЕДА! Пост опубликован без источника.")
    else:
        print(f"Ошибка: {r.text}")
        # Запасной вариант только текстом
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown"})

if __name__ == "__main__":
    main()
