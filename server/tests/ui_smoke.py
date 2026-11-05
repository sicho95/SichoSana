"""Smoke test SichoSana sur trois mises en page; exécuter avec le serveur local lancé."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HOST = "http://127.0.0.1:18765"
CASES = [
    ("iphone", 390, 844, "bottom"),
    ("ipad", 820, 1180, "tablet"),
    ("desktop", 1440, 900, "sidebar"),
]

def run():
    folder=Path("screenshots")
    folder.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        for label,width,height,layout in CASES:
            context=browser.new_context(viewport={"width":width,"height":height},
                                        locale="fr-FR", device_scale_factor=1)
            page=context.new_page()
            errors=[]
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(HOST, wait_until="networkidle")
            page.get_by_role("heading", name="Un moment pour soi").wait_for()
            if layout == "sidebar":
                assert page.locator(".sidebar").is_visible()
                assert not page.locator("#bottomnav").is_visible()
                nav=page.locator(".sidebar")
            else:
                assert page.locator("#bottomnav").is_visible()
                assert not page.locator(".sidebar").is_visible()
                nav=page.locator("#bottomnav")
                if layout == "tablet":
                    assert page.locator("#bottomnav").evaluate("(el) => getComputedStyle(el).position")=="sticky"
                else:
                    assert page.locator("#bottomnav").evaluate("(el) => getComputedStyle(el).position")=="fixed"
            page.screenshot(path=str(folder / (label+"-accueil.png")), full_page=True)
            nav.locator('[data-id="yoga"]').click()
            page.get_by_role("heading", name="Le yoga à ton rythme").wait_for()
            assert page.locator(".routine-card").count() == 6
            page.screenshot(path=str(folder / (label+"-yoga.png")), full_page=True)
            nav.locator('[data-id="meditate"]').click()
            page.get_by_role("heading", name="Ton espace de méditation").wait_for()
            assert page.locator(".cards .card").count() == 6
            nav.locator('[data-id="astro"]').click()
            page.get_by_role("heading", name="Ton ciel intérieur").wait_for()
            assert page.locator('#sign-select').input_value()==""
            nav.locator('[data-id="profile"]').click()
            page.get_by_role("heading", name="Ton chemin, ton rythme").wait_for()
            page.locator('[data-action="newProfile"]').click()
            assert page.locator("#new-profile-form").is_visible()
            page.locator("#new-profile-name").fill("Deuxième profil")
            page.locator("#new-profile-form button[type=submit]").click()
            page.get_by_text("Deuxième profil", exact=True).first.wait_for(timeout=5000)
            page.locator('[data-action="theme"][data-id="horizon"]').click()
            assert page.locator("html").get_attribute("data-theme")=="horizon"
            page.screenshot(path=str(folder / (label+"-profil.png")), full_page=True)
            page.reload(wait_until="networkidle")
            page.get_by_role("heading", name="Un moment pour soi").wait_for()
            assert page.locator("html").get_attribute("data-theme")=="horizon"
            assert not errors, (label,errors)
            context.close()
        browser.close()
    print("SichoSana UI smoke : iPhone / iPad / desktop OK")

if __name__ == "__main__":
    run()
