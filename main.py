import os
import random
import feedparser
import requests

HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    print(f"Запрос к ИИ для: {title}")
    api_url = "https://api-inference.huggingface.co/models/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<s>[INST] Напиши короткий хайповый пост для Телеграм на русском про это: {title}. Добавь эмодзи. [/INST]"
    
    try:
        # Ждем ответ максимум 15 секунд, чтобы бот не зависал
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=15)
        if response.status_code == 200:
            result = response.json()
            raw_text = result[0]['generated_text'].split("[/INST]")[-1].strip()
            if raw_text:
                return raw_text
    except Exception as e:
        print(f"ИИ не ответил вовремя, использую заголовок. (Ошибка: {e})")
    
    return f"🤖 *AI НОВОСТЬ*\n\n{title}"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Проверяем, был ли пост
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых новостей нет.")
                return

    # Текст и картинка
    post_text = get_ai_text(entry.title)
    # Исправляем картинку, чтобы не было логотипа
    img_url = f"https://image.pollinations.ai/prompt/{entry.title.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
    
    caption = f"{post_text}\n\n[Читать в источнике]({entry.link})"
    
    # Отправка
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                      data={"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(entry.link)
        print("ГОТОВО! Пост в канале.")
    else:
        print(f"Ошибка Телеграм: {r.text}")

if __name__ == "__main__":
    main()
