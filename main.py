import os, random, feedparser, requests, urllib.parse, time

HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # ОБНОВЛЕННЫЙ АДРЕС (реакция на ошибку 410)
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<s>[INST] Ты — ИИ-блогер. Напиши очень короткий (2 предложения) пост для Телеграм на русском про это: {title}. Используй эмодзи. [/INST]"
    
    try:
        print(f"--- Запрос к ИИ для: {title} ---")
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=25)
        
        # Если 410 или другие ошибки — пробуем резервный хаб
        if response.status_code != 200:
             api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
             response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=25)

        if response.status_code == 200:
            res = response.json()
            raw_text = res[0]['generated_text']
            clean_text = raw_text.split("[/INST]")[-1].strip()
            if clean_text: return clean_text
            
        print(f"ИИ не ответил (Код {response.status_code})")
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
    
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Чтобы не дублировать посты
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Новых постов нет.")
                return

    post_text = get_ai_text(entry.title)
    
    # Генерация картинки (максимально просто)
    short_q = urllib.parse.quote(entry.title[:50])
    img_url = f"https://image.pollinations.ai/prompt/robot%20ai%20technology%20{short_q}?width=1024&height=1024&nologo=true&seed={random.randint(1,999)}"
    
    print(f"Скачиваю картинку...")
    try:
        img_data = requests.get(img_url, timeout=30).content
        if len(img_data) > 10000: # Проверка, что это не пустой файл
            with open('photo.jpg', 'wb') as f: f.write(img_data)
            with open('photo.jpg', 'rb') as photo:
                r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                 data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                                 files={"photo": photo})
                if r.status_code == 200:
                    print("УСПЕХ!")
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                    return
    except: pass

    # Запасной вариант - только текст
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                 data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
