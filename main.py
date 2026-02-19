import os, random, feedparser, requests, urllib.parse

GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    if not GROQ_KEY: return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # НОВЫЙ ПРОМПТ ДЛЯ УВЕЛИЧЕНИЯ ТЕКСТА И ИНТЕРЕСА
    prompt = (
        f"Напиши пост для Telegram-канала 'Алгоритмы будущего' на основе новости: {title}. "
        "Сделай его захватывающим и простыми словами. "
        "Структура: 
"
        "1. Яркий заголовок с эмодзи. 
"
        "2. Краткий разбор (4-6 предложений), почему это важно (Сделай текст интересным и завлекательным). 
"
        "3. Вопрос к подписчикам в конце, риторический. 
"
        "Пиши на русском, используй современный стиль, без лишней воды."
    )

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7 # Немного креативности
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
    
    # Если ИИ не ответил, делаем хотя бы базовое форматирование
    if not ai_text:
        post_text = f"🔥 *НОВОСТЬ ИИ: {entry.title}*\n\nТехнологии не стоят на месте! Читайте подробности в источнике."
    else:
        post_text = ai_text

    # Исправленный блок картинки (короткий промпт для стабильности)
    clean_title = "".join(x for x in entry.title[:30] if x.isalnum() or x == " ")
    img_prompt = clean_title.replace(" ", "_")
    img_url = f"https://image.pollinations.ai/prompt/cyber_concept_{img_prompt}?width=1024&height=1024&seed={random.randint(1,999)}&nologo=true"
    
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
