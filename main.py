import os, random, feedparser, requests, urllib.parse

GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    if not GROQ_KEY: return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = f"""Напиши крутой пост для Telegram канала про новость: {title}.
    Сделай заголовок с эмодзи, разбор сути с интересом простыми словами (4-6 предложений).
    Пиши на русском. Используй Markdown, отступы для каждого абзаца, выделения для некоторых ключевых словосочетаний или предложений."""
    
    try:
        r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}, timeout=25)
        return r.json()['choices'][0]['message']['content'].strip() if r.status_code == 200 else None
    except: return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link: return

    # Сначала готовим текст
    ai_text = get_ai_text(entry.title)
    if not ai_text: return # Нет текста от ИИ — выходим

    # Готовим картинку
    clean_title = "".join(c for c in entry.title if c.isalnum() or c == " ")
    keywords = "+".join(clean_title.split()[:5])
    img_url = f"https://image.pollinations.ai/prompt/cyber_digital_art_style_{keywords}?width=1024&height=1024&nologo=true&seed={random.randint(1,1000)}"
    
    try:
        print(f"--- Проверка картинки для: {keywords} ---")
        img_res = requests.get(img_url, timeout=30)
        
        # ЖЕСТКАЯ ПРОВЕРКА: только если статус 200 и размер больше 5000 байт
        if img_res.status_code == 200 and len(img_res.content) > 5000:
            with open('p.jpg', 'wb') as f: f.write(img_res.content)
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": ai_text, "parse_mode": "Markdown"},
                    files={"photo": photo}
                )
                
                if r_tg.status_code == 200:
                    print("--- Успех: Пост с картинкой отправлен ---")
                    # Сохраняем ссылку ТОЛЬКО если пост реально ушел
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                else:
                    print(f"--- Ошибка Телеграма: {r_tg.text} ---")
        else:
            print(f"--- Отмена: Картинка не скачалась (размер {len(img_res.content)} байт) ---")
            
    except Exception as e:
        print(f"--- Критическая ошибка: {e} ---")

if __name__ == "__main__":
    main()
