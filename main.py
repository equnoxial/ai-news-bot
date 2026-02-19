import os, random, feedparser, requests, urllib.parse

GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    if not GROQ_KEY:
        print("--- [ОШИБКА] Нет ключа Groq! ---")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # Тот самый промпт, который дал крутой результат
    prompt = f"""Напиши захватывающий пост для Telegram про новость: {title}.
    Используй структуру:
    1. Интригующий заголовок с эмодзи.
    2. Разбор сути (3-5 предложений) — почему это важно для будущего?
    3. Призыв к обсуждению в конце.
    Пиши на русском в профессиональном, но живом стиле. Используй Markdown."""

    try:
        r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}, timeout=25)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
        print(f"--- [ОШИБКА ИИ] Код: {r.status_code} ---")
    except Exception as e:
        print(f"--- [ОШИБКА СЕТИ] {e} ---")
    return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("--- Новость уже была ---")
                return

    ai_text = get_ai_text(entry.title)
    post_text = ai_text if ai_text else f"🔥 *{entry.title}*"

    # КАПКАН НА КАРТИНКУ: Делаем максимально простой запрос
    # Оставляем только буквы и берем первые 5 слов
    clean_words = "".join(c for c in entry.title if c.isalnum() or c == " ").split()
    img_tags = "_".join(clean_words[:5])
    img_url = f"https://image.pollinations.ai/prompt/cyber_tech_art_{img_tags}?width=1024&height=1024&seed={random.randint(1,999)}&nologo=true"
    
    photo_sent = False
    try:
        print(f"--- Пробую скачать картинку: {img_tags} ---")
        img_res = requests.get(img_url, timeout=30)
        if img_res.status_code == 200 and len(img_res.content) > 2000:
            with open('p.jpg', 'wb') as f: f.write(img_res.content)
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                    files={"photo": photo})
                if r_tg.status_code == 200: 
                    photo_sent = True
                    print("--- Пост с ФОТО отправлен! ---")
        else:
            print(f"--- [ОШИБКА ФОТО] Размер: {len(img_res.content)} байт ---")
    except Exception as e:
        print(f"--- [ОШИБКА ТЕЛЕГРАМА] {e} ---")

    if not photo_sent:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
        print("--- Отправлен только ТЕКСТ ---")

    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
