import os, random, feedparser, requests, urllib.parse

# 1. КАПКАН НА КЛЮЧИ
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("--- [DEBUG] ПРОВЕРКА ОБКРУЖЕНИЯ ---")
print(f"Ключ Groq: {'✅ ОК' if GROQ_KEY else '❌ ОТСУТСТВУЕТ'}")
print(f"Токен TG: {'✅ ОК' if TG_TOKEN else '❌ ОТСУТСТВУЕТ'}")
print(f"ID Чата: {'✅ ОК' if CHAT_ID else '❌ ОТСУТСТВУЕТ'}")

def get_ai_text(title):
    if not GROQ_KEY:
        print("--- [DEBUG] ПРОПУСК ИИ: Ключ не найден ---")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Напиши пост для Телеграм на русском (2 предложения) про это: {title}. Добавь 2 эмодзи."}]
    }
    
    try:
        print(f"--- [DEBUG] ЗАПРОС К GROQ: {title[:40]}... ---")
        r = requests.post(url, headers=headers, json=data, timeout=25)
        print(f"--- [DEBUG] СТАТУС GROQ: {r.status_code} ---")
        if r.status_code == 200:
            text = r.json()['choices'][0]['message']['content'].strip()
            print(f"--- [DEBUG] ИИ СГЕНЕРИРОВАЛ: {text[:50]}... ---")
            return text
        print(f"--- [DEBUG] ОШИБКА GROQ RAW: {r.text} ---")
    except Exception as e:
        print(f"--- [DEBUG] СБОЙ СЕТИ ИИ: {e} ---")
    return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Капкан на повторы (для теста можно удалить файл last_link.txt в репозитории)
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("--- [DEBUG] НОВОСТЬ УЖЕ БЫЛА. ВЫХОД. ---")
                return

    ai_text = get_ai_text(entry.title)
    post_text = ai_text if ai_text else f"🤖 *НОВОСТЬ ИИ*\n\n{entry.title}"

    # 2. КАПКАН НА КАРТИНКУ
    img_url = f"https://image.pollinations.ai/prompt/cyberpunk%20style%20{urllib.parse.quote(entry.title[:30])}?width=1024&height=1024&seed={random.randint(1,999)}"
    print(f"--- [DEBUG] ПЫТАЮСЬ ВЗЯТЬ КАРТИНКУ: {img_url} ---")
    
    photo_sent = False
    try:
        img_data = requests.get(img_url, timeout=30).content
        print(f"--- [DEBUG] РАЗМЕР КАРТИНКИ: {len(img_data)} байт ---")
        
        if len(img_data) > 5000:
            with open('p.jpg', 'wb') as f: f.write(img_data)
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                    files={"photo": photo}
                )
                print(f"--- [DEBUG] ОТВЕТ TG (PHOTO): {r_tg.status_code} ---")
                if r_tg.status_code == 200: photo_sent = True
    except Exception as e:
        print(f"--- [DEBUG] ОШИБКА ФОТО: {e} ---")

    # 3. КАПКАН НА ТЕКСТОВУЮ ОТПРАВКУ
    if not photo_sent:
        print("--- [DEBUG] ПЛАН Б: ОТПРАВКА ТЕКСТОМ ---")
        r_txt = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"}
        )
        print(f"--- [DEBUG] ОТВЕТ TG (TEXT): {r_txt.status_code} ---")

    with open("last_link.txt", "w") as f: f.write(entry.link)
    print("--- [DEBUG] ЗАВЕРШЕНО УСПЕШНО ---")

if __name__ == "__main__":
    main()
