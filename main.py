import os, random, feedparser, requests, urllib.parse

# 1. ЗАБИРАЕМ КЛЮЧИ (Капкан на проверку окружения)
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_content(title):
    if not GROQ_KEY:
        print("--- [ОШИБКА] GitHub не видит GROQ_API_KEY! ---")
        return None, None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # Промпт для крутого текста и английских тегов для картинки
    prompt = f"""Новость: {title}
    1. Напиши пост для Telegram на русском (заголовок, 3-5 предложений, вопрос).
    2. Напиши через разделитель '|||' короткий промпт для картинки (3-4 английских слова).
    Пример: Текст поста... ||| robotic artificial intelligence"""

    try:
        r = requests.post(url, headers=headers, json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6
        }, timeout=25)
        
        if r.status_code == 200:
            res = r.json()['choices'][0]['message']['content'].strip()
            if "|||" in res:
                text, img_p = res.split("|||")
                return text.strip(), img_p.strip()
        print(f"--- [ОШИБКА ИИ] Код: {r.status_code}, Ответ: {r.text} ---")
    except Exception as e:
        print(f"--- [ОШИБКА СЕТИ ИИ] {e} ---")
    return None, None

def main():
    # Читаем ленту
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Проверка на дубликаты
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("--- Новость уже была опубликована ---")
                return

    # Получаем контент
    print(f"--- Обработка новости: {entry.title} ---")
    post_text, img_tags = get_ai_content(entry.title)
    
    if not post_text or not img_tags:
        print("--- [ОТМЕНА] Не удалось получить текст или теги от ИИ ---")
        return

    # ГЕНЕРАЦИЯ КАРТИНКИ (Исправлено: /prompt/, знаки & и очистка текста)
    img_tags_clean = "".join(c for c in img_tags if c.isalnum() or c == " ").replace(" ", "_")
    img_url = f"https://image.pollinations.ai/prompt/cyberpunk_digital_art_{img_tags_clean}?width=1024&height=1024&nologo=true&seed={random.randint(1,999)}"
    
    try:
        print(f"--- Запрос картинки: {img_url} ---")
        img_res = requests.get(img_url, timeout=30)
        
        # Капкан на размер: если 16 байт или статус не 200 — отменяем
        if img_res.status_code == 200 and len(img_res.content) > 5000:
            with open('p.jpg', 'wb') as f:
                f.write(img_res.content)
            
            # Отправка в Telegram
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                    files={"photo": photo}
                )
                
                if r_tg.status_code == 200:
                    print("--- УСПЕХ: Пост опубликован! ---")
                    with open("last_link.txt", "w") as f:
                        f.write(entry.link)
                    return
                else:
                    print(f"--- [ОШИБКА TG] {r_tg.text} ---")
        else:
            print(f"--- [ОТМЕНА] Картинка не прошла проверку (Размер: {len(img_res.content)} байт) ---")
            
    except Exception as e:
        print(f"--- [КРИТИЧЕСКАЯ ОШИБКА] {e} ---")

if __name__ == "__main__":
    main()
