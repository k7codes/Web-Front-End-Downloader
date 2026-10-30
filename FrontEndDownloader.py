import os
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def download_full_frontend(target_url, output_dir="site_data"):
    # Yerel klasörleri hazırla
    css_dir = os.path.join(output_dir, "css")
    js_dir = os.path.join(output_dir, "js")
    img_dir = os.path.join(output_dir, "images")
    
    for folder in [output_dir, css_dir, js_dir, img_dir]:
        os.makedirs(folder, exist_ok=True)

    captured_resources = {}

    with sync_playwright() as p:
        print("[*] Tarayıcı başlatılıyor...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        # Ağ üzerinden yüklenen tüm CSS, JS ve Görselleri canlı yakalama
        def handle_response(response):
            try:
                url = response.url
                resource_type = response.request.resource_type
                status = response.status

                if status == 200 and resource_type in ["stylesheet", "script", "image"]:
                    parsed_url = urllib.parse.urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    
                    if not filename or filename.startswith("data:"):
                        return

                    # İlgili klasöre yerleştir
                    if resource_type == "stylesheet":
                        target_path = os.path.join(css_dir, filename)
                        rel_path = f"css/{filename}"
                    elif resource_type == "script":
                        target_path = os.path.join(js_dir, filename)
                        rel_path = f"js/{filename}"
                    elif resource_type == "image":
                        target_path = os.path.join(img_dir, filename)
                        rel_path = f"images/{filename}"

                    body = response.body()
                    with open(target_path, "wb") as f:
                        f.write(body)

                    captured_resources[url] = rel_path
                    print(f"[+] İndirildi ({resource_type}): {filename}")
            except Exception:
                pass

        page.on("response", handle_response)

        print(f"[*] Sayfaya bağlanılıyor: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded")
        
        print("[*] Sayfanın yüklenmesi ve doğrulama için bekleniyor (12 saniye)...")
        page.wait_for_timeout(12000)

        # HTML kaynağını alıp BeautifulSoup ile işleme
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        # Linkleri yerel dosya yollarıyla güncelleme
        for tag, attr in [("link", "href"), ("script", "src"), ("img", "src")]:
            for element in soup.find_all(tag):
                src = element.get(attr)
                if src:
                    full_url = urllib.parse.urljoin(target_url, src)
                    if full_url in captured_resources:
                        element[attr] = captured_resources[full_url]

        # Güncellenmiş HTML'i kaydetme
        index_path = os.path.join(output_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        print(f"\n[✔] Sayfa tüm kaynaklarıyla birlikte 'C:\\Users\\User Name\\{output_dir}' klasörüne indirildi!")
        browser.close()

if __name__ == "__main__":
    download_full_frontend("Site")
