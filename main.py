import os
import random
import feedparser
import requests

# Секреты
HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    print(f"Генерирую текст для: {title}")
    api_url = "https://api-inference.huggingface.co/models/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    prompt = f"<s>[INST] Напиши короткий и хайповый пост для Телеграм на русском языке на основе этой новости: {title}. Используй эмодзи. [/INST]"
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 250}})
        result = response.json()
        text = result[0]['generated_text'].split("[/INST]")[-1].strip()
        return text
    except:
        return f"🤖 *Новость ИИ*\n\n{title}"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых новостей нет.")
                return

    # Текст и картинка
    post_text = get_ai_text(entry.title)
    # Используем проверенный генератор картинок
    img_url = f"https://image.pollinations.ai/prompt/{entry.title.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
    
    caption = f"{post_text}\n\n[Читать оригинал]({entry.link})"
    
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                      data={"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(entry.link)
        print("ПОСТ ОПУБЛИКОВАН!")

if __name__ == "__main__":
    main()
