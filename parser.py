import cloudscraper
import requests
import re
import os
import time

PROXY_REGEX = re.compile(r'(tg://proxy\?server=[a-zA-Z0-9\.\-]+&port=\d+&secret=[a-zA-Z0-9]+|https://t\.me/proxy\?server=[a-zA-Z0-9\.\-]+&port=\d+&secret=[a-zA-Z0-9]+)')

# База источников: каналы и сырые текстовые файлы с других репозиториев
SOURCES = [
    "https://t.me/s/mtproto_proxies",
    "https://t.me/s/proxy_mtproto",
    "https://t.me/s/proxymtproto",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/tg/mtproto.txt",
    "https://raw.githubusercontent.com/elliotwutingfeng/Inception-tg-proxy/main/tg-proxies.txt",
    "https://raw.githubusercontent.com/SlavaBashmakov/telegram-proxies/main/proxies.txt"
]

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def get_direct_proxies():
    print("[*] Парсинг прямых источников и баз...")
    proxies = set()
    for url in SOURCES:
        try:
            response = scraper.get(url, timeout=15)
            found = PROXY_REGEX.findall(response.text)
            print(f"[+] Источник {url.split('/')[-1]}: вытащено {len(found)}")
            proxies.update(found)
        except Exception as e:
            print(f"[-] Ошибка пробива {url}: {e}")
    return proxies

def get_github_search():
    print("\n[*] Поиск по API GitHub...")
    proxies = set()
    gh_token = os.environ.get("GITHUB_TOKEN")
    
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    } if gh_token else {}
    
    search_url = "https://api.github.com/search/code?q=tg://proxy+extension:txt&sort=indexed"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])
            for item in items[:5]: # Ограничиваем аппетиты, чтобы избежать бана
                raw_url = item.get("html_url").replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                try:
                    raw_resp = scraper.get(raw_url, timeout=10)
                    proxies.update(PROXY_REGEX.findall(raw_resp.text))
                    time.sleep(2)
                except:
                    continue
        elif response.status_code == 429:
            print("[-] API GitHub перегружен (ошибка 429). Пропускаем поиск по коду.")
        else:
            print(f"[-] Ошибка API: {response.status_code}")
    except Exception as e:
        print(f"[-] Ошибка доступа к GitHub API: {e}")
        
    return proxies

def main():
    all_proxies = set()
    
    # Собираем прокси со всех функций
    all_proxies.update(get_direct_proxies())
    all_proxies.update(get_github_search())
    
    print(f"\n[!] ИТОГО уникальных прокси собрано: {len(all_proxies)}")
    
    # Жестко создаем файл в любом случае, даже если прокси не нашлись
    with open("proxies.txt", "w", encoding="utf-8") as f:
        for p in all_proxies:
            f.write(p + "\n")
    print("[+] Файл proxies.txt успешно записан.")

if __name__ == "__main__":
    main()
