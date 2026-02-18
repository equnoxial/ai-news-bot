import os
import random
import feedparser
import requests
import urllib.parse
import time

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
    except: pass
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
    
    # 1. Генерируем ссылку
    short_title = " ".join(entry.title.split()[:4])
    encoded_prompt = urllib.parse.quote(f"cyberpunk aesthetic {short_title}")
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(1,9999)}"
    
    # 2. САМЫЙ ВАЖНЫЙ ЭТАП: Скачиваем картинку сами
    print(f"Скачиваю картинку: {img_url}")
    try:
        img_data = requests.get(img_url, timeout=30).content
        with open('photo.jpg', 'wb') as handler:
            handler.write(img_data)
        
        # 3. Отправляем ФАЙЛ, а не ссылку
        print("Отправляю файл в Telegram...")
        with open('photo.jpg', 'rb') as photo:
            r = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                files={"photo": photo}
            )
        
        if r.status_code == 200:
            with open("last_link.txt", "w") as f: f.write(entry.link)
            print("УСПЕХ! Пост опубликован.")
        else:
            print(f"Ошибка при отправке файла: {r.text}")
            # Запасной вариант (только текст)
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                         data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
            
    except Exception as e:
        print(f"Не удалось скачать картинку: {e}")
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    main()
