import cloudscraper
import requests
import re
import os
import time

# Регулярка для выдирания прокси из любой каши текста
PROXY_REGEX = re.compile(r'(tg://proxy\?server=[a-zA-Z0-9\.\-]+&port=\d+&secret=[a-zA-Z0-9]+|https://t\.me/proxy\?server=[a-zA-Z0-9\.\-]+&port=\d+&secret=[a-zA-Z0-9]+)')

# Внешние источники (каналы, сайты), которые будем пробивать cloudscraper'ом
EXTERNAL_SOURCES = [
    "https://t.me/s/mtproto_proxies",
    "https://t.me/s/proxy_mtproto",
    "https://t.me/s/proxymtproto"
]

# Создаем "пробивной" скрапер
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def get_external_proxies():
    print("[*] Начинаем парсинг внешних сайтов с обходом защиты...")
    proxies = set()
    for url in EXTERNAL_SOURCES:
        try:
            response = scraper.get(url, timeout=15)
            found = PROXY_REGEX.findall(response.text)
            print(f"[+] С сайта {url} вытащено: {len(found)}")
            proxies.update(found)
        except Exception as e:
            print(f"[-] Ошибка пробива {url}: {e}")
    return proxies

def get_github_proxies():
    print("\n[*] Начинаем поиск по репозиториям GitHub...")
    proxies = set()
    # Берем токен, который GitHub Actions выдает автоматически
    gh_token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
    
    # Ищем файлы, содержащие tg://proxy, отсортированные по недавним обновлениям
    search_url = "https://api.github.com/search/code?q=tg://proxy+extension:txt&sort=indexed&order=desc"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            print(f"[+] Найдено {len(items)} перспективных файлов на GitHub.")
            
            for item in items[:10]: # Ограничиваем, чтобы не словить бан
                raw_url = item.get("html_url").replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                try:
                    # Парсим сырой код файлов из чужих репозиториев
                    raw_resp = scraper.get(raw_url, timeout=10)
                    found = PROXY_REGEX.findall(raw_resp.text)
                    proxies.update(found)
                    time.sleep(1) # Небольшая пауза
                except Exception:
                    continue
        else:
            print(f"[-] Ошибка API GitHub: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[-] Ошибка доступа к GitHub API: {e}")
        
    return proxies

def main():
    all_proxies = set()
    
    # Собираем со всех источников
    all_proxies.update(get_external_proxies())
    all_proxies.update(get_github_proxies())
    
    print(f"\n[!] ИТОГО уникальных прокси собрано: {len(all_proxies)}")
    
    if all_proxies:
        # Перезаписываем файл со свежими прокси
        with open("proxies.txt", "w", encoding="utf-8") as f:
            for p in all_proxies:
                f.write(p + "\n")
        print("[+] Файл proxies.txt успешно обновлен.")
    else:
        print("[-] Прокси не найдены, файл не обновлен.")

if __name__ == "__main__":
    main()

