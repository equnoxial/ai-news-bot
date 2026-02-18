import os, random, feedparser, requests, urllib.parse, time

HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # Используем одну из самых стабильных моделей на HF
    api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<|system|>\nТы — ИИ-журналист. Напиши пост для Telegram на русском.<|user|>\nНапиши короткий (2-3 предложения) пост про это: {title}. Добавь эмодзи.<|assistant|>\n"
    
    try:
        print(f"--- Запрос к ИИ для: {title} ---")
        response = requests.post(api_url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 200}}, timeout=30)
        if response.status_code == 200:
            res = response.json()
            # Извлекаем только ответ нейросети
            raw_text = res[0]['generated_text']
            clean_text = raw_text.split("<|assistant|>\n")[-1].strip()
            if clean_text: 
                print("ИИ ответил успешно!")
                return clean_text
        print(f"ИИ выдал ошибку {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Ошибка связи с ИИ: {e}")
    
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}\n\nПохоже, нейросеть сегодня не в духе, но новость важная!"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Чтобы не спамить одной новостью
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых новостей пока нет.")
                return

    post_text = get_ai_text(entry.title)
    
    # Генерация картинки
    short_title = " ".join(entry.title.split()[:4])
    encoded = urllib.parse.quote(f"digital artificial intelligence high-tech {short_title}")
    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=800&nologo=true&seed={random.randint(1,999)}"
    
    print(f"Скачиваю картинку: {img_url}")
    try:
        img_res = requests.get(img_url, timeout=40)
        # Проверяем: это реально картинка или мусор?
        if img_res.status_code == 200 and len(img_res.content) > 5000:
            with open('photo.jpg', 'wb') as f: f.write(img_res.content)
            
            print("Отправляю в Telegram...")
            with open('photo.jpg', 'rb') as photo:
                r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                 data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                                 files={"photo": photo})
                if r.status_code == 200:
                    print("ПОБЕДА! Пост с картинкой и текстом ушел.")
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                    return
        else:
            print("Картинка не скачалась или битая.")
    except:
        print("Ошибка при работе с картинкой.")

    # Если с картинкой не вышло — шлем только текст
    print("План Б: шлю только текст...")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                 data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
