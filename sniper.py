import asyncio, requests, time, re, os
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALVO_DESCONTO_MIN = 50 # Só avisa se desconto > 50%
ALVO_PRECO_MAX = {
    "iPhone 15": 700,
    "iPhone 14": 550,
    "PS5 Slim": 420,
    "MacBook Air M2": 950,
    "AirPods Pro 2": 190,
    "Nintendo Switch": 270,
    "Xiaomi Scooter 4": 320,
}

PRODUTOS = {
    "iPhone 15": {"normal": 979},
    "iPhone 14": {"normal": 829},
    "PS5 Slim": {"normal": 549},
    "MacBook Air M2": {"normal": 1249},
    "AirPods Pro 2": {"normal": 279},
    "Nintendo Switch": {"normal": 329},
    "Xiaomi Scooter 4": {"normal": 499},
}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def extrair_preco(texto):
    numeros = re.findall(r'[\d.,]+', texto.replace('.', '').replace(' ', ''))
    return float(numeros[0].replace(',', '.')) if numeros else 0

async def checar_amazon(page):
    """Amazon ES - Promoções"""
    for produto, dados in PRODUTOS.items():
        print(f"🔍 Amazon: {produto}")
        try:
            await page.goto(f"https://www.amazon.es/s?k={produto.replace(' ', '+')}", timeout=30000)
            await page.wait_for_timeout(4000)
            items = await page.query_selector_all('div[data-component-type="s-search-result"]')
            
            for item in items[:3]:
                try:
                    preco_el = await item.query_selector('.a-price-whole')
                    if not preco_el: continue
                    preco_txt = await preco_el.inner_text()
                    preco = float(preco_txt.replace('.', '').replace(',', '.'))
                    
                    link_el = await item.query_selector('h2 a')
                    link = "https://www.amazon.es" + await link_el.get_attribute('href')
                    titulo = await link_el.inner_text()
                    
                    desconto = ((dados["normal"] - preco) / dados["normal"]) * 100
                    
                    if preco <= ALVO_PRECO_MAX[produto] and desconto >= ALVO_DESCONTO_MIN:
                        enviar_telegram(f"🚨 *PROMO AMAZON* 🚨\n\n*Item:* {titulo[:60]}\n*Preço:* {preco:.2f}€\n*Preço normal:* {dados['normal']}€\n*Desconto:* {desconto:.0f}%\n\n{link}")
                        await asyncio.sleep(3)
                except: continue
            await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Erro Amazon {produto}: {e}")

async def checar_worten(page):
    """Worten PT - Promoções"""
    for produto, dados in PRODUTOS.items():
        print(f"🔍 Worten: {produto}")
        try:
            await page.goto(f"https://www.worten.pt/search?query={produto.replace(' ', '%20')}", timeout=30000)
            await page.wait_for_timeout(4000)
            items = await page.query_selector_all('.product-card')
            
            for item in items[:3]:
                try:
                    preco_el = await item.query_selector('.price-current')
                    if not preco_el: continue
                    preco_txt = await preco_el.inner_text()
                    preco = extrair_preco(preco_txt)
                    
                    link_el = await item.query_selector('a.product-card__link')
                    link = "https://www.worten.pt" + await link_el.get_attribute('href')
                    titulo = await (await item.query_selector('.product-card__title')).inner_text()
                    
                    desconto = ((dados["normal"] - preco) / dados["normal"]) * 100
                    
                    if preco <= ALVO_PRECO_MAX[produto] and desconto >= ALVO_DESCONTO_MIN:
                        enviar_telegram(f"🚨 *PROMO WORTEN* 🚨\n\n*Item:* {titulo[:60]}\n*Preço:* {preco:.2f}€\n*Preço normal:* {dados['normal']}€\n*Desconto:* {desconto:.0f}%\n\n{link}")
                        await asyncio.sleep(3)
                except: continue
            await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Erro Worten {produto}: {e}")

async def checar_fnac(page):
    """Fnac PT"""
    for produto, dados in PRODUTOS.items():
        print(f"🔍 Fnac: {produto}")
        try:
            await page.goto(f"https://www.fnac.pt/SearchResult/ResultList.aspx?SCat=0&Search={produto.replace(' ', '+')}", timeout=30000)
            await page.wait_for_timeout(4000)
            items = await page.query_selector_all('.Article-item')
            
            for item in items[:3]:
                try:
                    preco_el = await item.query_selector('.userPrice')
                    if not preco_el: continue
                    preco_txt = await preco_el.inner_text()
                    preco = extrair_preco(preco_txt)
                    
                    link_el = await item.query_selector('.Article-desc a')
                    link = "https://www.fnac.pt" + await link_el.get_attribute('href')
                    titulo = await link_el.inner_text()
                    
                    desconto = ((dados["normal"] - preco) / dados["normal"]) * 100
                    
                    if preco <= ALVO_PRECO_MAX[produto] and desconto >= ALVO_DESCONTO_MIN:
                        enviar_telegram(f"🚨 *PROMO FNAC* 🚨\n\n*Item:* {titulo[:60]}\n*Preço:* {preco:.2f}€\n*Preço normal:* {dados['normal']}€\n*Desconto:* {desconto:.0f}%\n\n{link}")
                        await asyncio.sleep(3)
                except: continue
            await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Erro Fnac {produto}: {e}")

async def main():
    enviar_telegram("🤖 *JARVIS SNIPER V4 ONLINE*\nVasculhando: Amazon | Worten | Fnac\nRoda a cada 1h")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        print(f"\n=== INICIANDO VASCULHA {time.strftime('%H:%M:%S')} ===")
        try:
            await checar_amazon(page)
            await checar_worten(page)
            await checar_fnac(page)
        except Exception as e:
            print(f"❌ Erro geral: {e}")
        
        await browser.close()
        print("✅ Vasculha completa. Encerrando.")

if __name__ == "__main__":
    asyncio.run(main())
