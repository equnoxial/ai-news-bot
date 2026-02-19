import os, random, feedparser, requests, urllib.parse, time

GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # Используем Groq - он сейчас стабильнее всех
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Напиши пост для Телеграм на русском (2 предложения) про это: {title}. Добавь эмодзи."}]
    }
    
    try:
        print(f"--- Запрос к Groq для: {title} ---")
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        print(f"Groq ошибка: {response.status_code}")
    except Exception as e:
        print(f"Ошибка связи: {e}")
    
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}\n\nМир технологий не стоит на месте! 🔥"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Проверка на дубликат
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link: return

    post_text = get_ai_text(entry.title)
    
    # Генерация картинки через стабильный промпт
    img_url = f"https://image.pollinations.ai/prompt/cyberpunk%20tech%20ai%20{urllib.parse.quote(entry.title[:30])}?width=1024&height=1024&seed={random.randint(1,999)}"
    
    print("Пробую отправить пост...")
    # Сначала пробуем с картинкой
    try:
        img_data = requests.get(img_url, timeout=30).content
        if len(img_data) > 10000:
            with open('p.jpg', 'wb') as f: f.write(img_data)
            with open('p.jpg', 'rb') as photo:
                r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                 data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                                 files={"photo": photo})
                if r.status_code == 200:
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                    return
    except: pass

    # Если картинка не прошла - только текст
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                 data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
