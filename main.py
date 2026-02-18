import os, random, feedparser, requests, urllib.parse, time

HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # НОВЫЙ АДРЕС (router вместо api-inference), как требует ошибка 410
    api_url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Добавляем параметры, чтобы ИИ не возвращал пустой текст
    payload = {
        "inputs": f"<s>[INST] Ты крутой ИИ-блогер. Напиши краткий пост (2 предложения) на русском для Телеграм про новость: '{title}'. Добавь 2 эмодзи. [/INST]",
        "parameters": {"max_new_tokens": 250, "return_full_text": False}
    }
    
    try:
        print(f"--- Запрос к ИИ: {title} ---")
        # Делаем 2 попытки, если первая не удалась
        for _ in range(2):
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # Извлекаем текст (формат ответа может быть списком или словарем)
                text = result[0]['generated_text'].strip() if isinstance(result, list) else result.get('generated_text', '').strip()
                if text: return text
            time.sleep(3)
        print(f"ИИ не ответил (Код {response.status_code})")
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
    
    # Если ИИ совсем упал, добавляем хоть какой-то текст, чтобы не был голый заголовок
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}\n\nСледим за развитием событий в мире нейросетей! 🔥"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых постов нет.")
                return

    # Получаем ТЕКСТ
    post_text = get_ai_text(entry.title)
    
    # Генерация картинки (упростил запрос для стабильности)
    img_prompt = urllib.parse.quote(f"futuristic technology ai {entry.title[:40]}")
    img_url = f"https://image.pollinations.ai/prompt/{img_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(1,1000)}"
    
    try:
        print("Скачиваю картинку...")
        img_res = requests.get(img_url, timeout=40)
        # Если это реально картинка и она не пустая
        if img_res.status_code == 200 and len(img_res.content) > 15000:
            with open('photo.jpg', 'wb') as f: f.write(img_res.content)
            with open('photo.jpg', 'rb') as photo:
                r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                 data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                                 files={"photo": photo})
                if r.status_code == 200:
                    print("УСПЕХ!")
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                    return
        print("Картинка битая или сервис занят.")
    except: pass

    # План Б - шлем текст (теперь он будет с описанием, а не только заголовком)
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                 data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
