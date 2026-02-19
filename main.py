import os, random, feedparser, requests, urllib.parse

# Капкан №1: Проверка окружения
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("--- [DEBUG] ПРОВЕРКА КЛЮЧЕЙ ---")
print(f"TG_TOKEN: {'✅ Найдено' if TG_TOKEN else '❌ ПУСТО'}")
print(f"CHAT_ID: {'✅ Найдено' if CHAT_ID else '❌ ПУСТО'}")
print(f"GROQ_KEY: {'✅ Найдено (' + GROQ_KEY[:5] + '...)' if GROQ_KEY else '❌ ПУСТО'}")

def get_ai_text(title):
    if not GROQ_KEY:
        print("--- [DEBUG] ОШИБКА: Groq ключ не дошел до кода! ---")
        return None
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Напиши пост для Телеграм на русском (2 предложения) про новость: {title}. Добавь 2 эмодзи."}]
    }
    
    try:
        print(f"--- [DEBUG] ОТПРАВЛЯЮ ЗАПРОС К GROQ ДЛЯ: {title[:30]}... ---")
        r = requests.post(url, headers=headers, json=data, timeout=25)
        
        # Капкан №2: Анализ ответа ИИ
        print(f"--- [DEBUG] ОТВЕТ GROQ (Status: {r.status_code}) ---")
        if r.status_code == 200:
            res_json = r.json()
            content = res_json['choices'][0]['message']['content'].strip()
            print(f"--- [DEBUG] ТЕКСТ ОТ ИИ: {content} ---")
            return content
        else:
            print(f"--- [DEBUG] RAW ERROR FROM GROQ: {r.text} ---")
    except Exception as e:
        print(f"--- [DEBUG] ОШИБКА СЕТИ ПРИ ЗАПРОСЕ К ИИ: {e} ---")
    
    return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: 
        print("--- [DEBUG] Лента новостей пуста ---")
        return
    
    entry = feed.entries[0]
    print(f"--- [DEBUG] ПОСЛЕДНЯЯ НОВОСТЬ: {entry.title} ---")

    # Проверка дубликата
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("--- [DEBUG] Новость уже была опубликована. Выход. ---")
                return

    # Получаем текст
    ai_text = get_ai_text(entry.title)
    
    # Капкан №3: Если ИИ не ответил, используем заголовок, но помечаем это
    if not ai_text:
        print("--- [DEBUG] ИИ не дал текст, использую запасной вариант (заголовок) ---")
        post_text = f"🤖 *НОВОСТЬ ИИ*\n\n{entry.title}"
    else:
        post_text = ai_text

    # Работа с картинкой
    img_prompt = urllib.parse.quote(f"futuristic technology {entry.title[:50]}")
    img_url = f"https://image.pollinations.ai/prompt/{img_prompt}?width=1024&height=1024&seed={random.randint(1,1000)}"
    
    print(f"--- [DEBUG] ПРОБУЮ СКАЧАТЬ КАРТИНКУ: {img_url} ---")
    
    photo_sent = False
    try:
        img_res = requests.get(img_url, timeout=30)
        print(f"--- [DEBUG] СТАТУС КАРТИНКИ: {img_res.status_code}, РАЗМЕР: {len(img_res.content)} байт ---")
        
        if img_res.status_code == 200 and len(img_res.content) > 5000:
            with open('debug_photo.jpg', 'wb') as f:
                f.write(img_res.content)
            
            print("--- [DEBUG] ОТПРАВЛЯЮ ФОТО В ТЕЛЕГРАМ ---")
            with open('debug_photo.jpg', 'rb') as photo:
                r_tg = requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                    files={"photo": photo}
                )
                print(f"--- [DEBUG] ОТВЕТ ТЕЛЕГРАМА (ФОТО): {r_tg.text} ---")
                if r_tg.status_code == 200: photo_sent = True
        else:
            print("--- [DEBUG] Картинка слишком маленькая или битая ---")
    except Exception as e:
        print(f"--- [DEBUG] СБОЙ ПРИ ОБРАБОТКЕ КАРТИНКИ: {e} ---")

    # Если фото не ушло — шлем текст
    if not photo_sent:
        print("--- [DEBUG] ОТПРАВЛЯЮ ТОЛЬКО ТЕКСТ (ПЛАН Б) ---")
r_txt = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"}
        )
        print(f"--- [DEBUG] ОТВЕТ ТЕЛЕГРАМА (ТЕКСТ): {r_txt.text} ---")

    # Сохраняем ссылку
    with open("last_link.txt", "w") as f:
        f.write(entry.link)
    print("--- [DEBUG] РАБОТА ЗАВЕРШЕНА ---")

if name == "__main__":
    main()
