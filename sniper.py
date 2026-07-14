import asyncio, requests, time, re
from playwright.async_api import async_playwright

import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALVO_LUCRO_MIN = 50
CHECK_INTERVAL = 1800

PRODUTOS = {
    "iPhone 13": {"compra_max": 150, "venda_media": 450},
    "iPhone 12": {"compra_max": 100, "venda_media": 300},
    "PS5": {"compra_max": 180, "venda_media": 350},
    "MacBook Air M1": {"compra_max": 250, "venda_media": 650},
    "Xiaomi Scooter": {"compra_max": 80, "venda_media": 200},
}

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def extrair_preco(texto):
    numeros = re.findall(r'[\d.,]+', texto.replace('.', ''))
    return float(numeros[0].replace(',', '.')) if numeros else 0

async def checar_vinted(page):
    """VINTED - MELHOR PRA iPHONE BARATO"""
    for produto, regras in PRODUTOS.items():
        try:
            url = f"https://www.vinted.pt/catalog?search_text={produto}&order=newest_first&price_to={regras['compra_max']}"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(5000)
            items = await page.query_selector_all('div[data-testid="grid-item"]')
            
            for item in items[:3]:
                try:
                    preco = extrair_preco(await (await item.query_selector('p[data-testid*="price"]')).inner_text())
                    link = "https://www.vinted.pt" + await (await item.query_selector('a')).get_attribute('href')
                    titulo = await (await item.query_selector('p[data-testid*="description"]')).inner_text()
                    lucro = regras["venda_media"] - preco - 20
                    
                    if preco <= regras["compra_max"] and lucro >= ALVO_LUCRO_MIN:
                        enviar_telegram(f"🚨 *VINTED*\n*{titulo[:50]}*\n*Preço:* {preco}€ | *Lucro:* +{lucro:.0f}€\n{link}")
                        await asyncio.sleep(3)
                except: continue
        except: continue

async def checar_olx(page):
    """OLX - SEGUNDO MELHOR"""
    for produto, regras in PRODUTOS.items():
        try:
            url = f"https://www.olx.pt/ads/q-{produto.replace(' ', '-')}/?search[filter_float_price:to]={regras['compra_max']}"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(4000)
            items = await page.query_selector_all('div[data-cy="l-card"]')
            
            for item in items[:3]:
                try:
                    preco = extrair_preco(await (await item.query_selector('p[data-testid="ad-price"]')).inner_text())
                    link = await (await item.query_selector('a')).get_attribute('href')
                    titulo = await (await item.query_selector('h6')).inner_text()
                    lucro = regras["venda_media"] - preco - 20
                    
                    if preco <= regras["compra_max"] and lucro >= ALVO_LUCRO_MIN:
                        enviar_telegram(f"🚨 *OLX*\n*{titulo[:50]}*\n*Preço:* {preco}€ | *Lucro:* +{lucro:.0f}€\n{link}")
                        await asyncio.sleep(3)
                except: continue
        except: continue

async def checar_wallapop(page):
    """WALLAPOP - BOM PRA ESPANHA/PT"""
    for produto, regras in PRODUTOS.items():
        try:
            url = f"https://pt.wallapop.com/app/search?keywords={produto}&filters={{%22price_max%22:{regras['compra_max']}}}"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(5000)
            items = await page.query_selector_all('a[href*="/item/"]')
            
            for item in items[:3]:
                try:
                    preco = extrair_preco(await (await item.query_selector('.ItemCard__price')).inner_text())
                    link = "https://pt.wallapop.com" + await item.get_attribute('href')
                    titulo = await (await item.query_selector('.ItemCard__title')).inner_text()
                    lucro = regras["venda_media"] - preco - 20
                    
                    if preco <= regras["compra_max"] and lucro >= ALVO_LUCRO_MIN:
                        enviar_telegram(f"🚨 *WALLAPOP*\n*{titulo[:50]}*\n*Preço:* {preco}€ | *Lucro:* +{lucro:.0f}€\n{link}")
                        await asyncio.sleep(3)
                except: continue
        except: continue

async def checar_backmarket(page):
    """BACKMARKET - RECONDICIONADOS"""
    for produto, regras in PRODUTOS.items():
        if "iPhone" not in produto and "MacBook" not in produto: continue
        try:
            url = f"https://www.backmarket.pt/search?q={produto}"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(5000)
            items = await page.query_selector_all('div[data-test="productCard"]')
            
            for item in items[:2]:
                try:
                    preco = extrair_preco(await (await item.query_selector('span[data-test="product-price"]')).inner_text())
                    link = "https://www.backmarket.pt" + await (await item.query_selector('a')).get_attribute('href')
                    titulo = await (await item.query_selector('h2')).inner_text()
                    lucro = regras["venda_media"] - preco - 30
                    
                    if preco <= regras["compra_max"] and lucro >= ALVO_LUCRO_MIN:
                        enviar_telegram(f"🚨 *BACKMARKET*\n*{titulo[:50]}*\n*Preço:* {preco}€ | *Lucro:* +{lucro:.0f}€\n{link}")
                        await asyncio.sleep(3)
                except: continue
        except: continue

async def main():
    enviar_telegram("🤖 *JARVIS SNIPER V3 ONLINE*\nSites: Vinted | OLX | Wallapop | BackMarket\nCiclo: 30min\nLucro min: 50€")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        while True:
            print(f"\n=== CICLO {time.strftime('%H:%M:%S')} ===")
            try:
                await checar_vinted(page)
                await checar_olx(page)
                await checar_wallapop(page)
                await checar_backmarket(page)
            except Exception as e:
                print(f"Erro geral: {e}")
            
            print(f"😴 Dormindo 30min...")
            await asyncio.sleep(CHECK_INTERVAL)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())