import os, random, feedparser, requests, urllib.parse

GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    if not GROQ_KEY: return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # Используем тройные кавычки для многострочного текста, чтобы не было SyntaxError
    prompt = f"""Напиши крутой пост для Telegram про новость: {title}.
    Сделай его живым и интересным.
    
    Структура поста:
    1. Краткий кликбейтный заголовок с парой эмодзи.
    2. Основная суть новости (4-6 предложений) понятным языком.
    3. Риторический вопрос (например: 'А вы что думаете?', 'Попробуете?') в конце.
    
    Пиши на русском. Используй Markdown для оформления."""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=25)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
    except: pass
    return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link: return

    ai_text = get_ai_text(entry.title)
    post_text = ai_text if ai_text else f"🔥 *{entry.title}*\n\nСвежие новости технологий уже здесь!"

    # Улучшенная генерация картинки: берем ключевые слова из заголовка
    # Ограничиваем длину и убираем лишние символы
    words = [w for w in entry.title.split() if len(w) > 3][:5]
    img_tags = "_".join(words)
    img_url = f"https://image.pollinations.ai/prompt/cyber_digital_art_{img_tags}?width=1024&height=1024&seed={random.randint(1,999)}&nologo=true"
    
    photo_sent = False
    try:
        img_res = requests.get(img_url, timeout=30)
        if img_res.status_code == 200 and len(img_res.content) > 1000:
            with open('p.jpg', 'wb') as f: f.write(img_res.content)
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                    files={"photo": photo}
                )
                if r_tg.status_code == 200: photo_sent = True
    except: pass

    if not photo_sent:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})

    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
