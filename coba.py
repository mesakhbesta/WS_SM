import streamlit as st
import asyncio
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import aiohttp
from bs4 import BeautifulSoup

# Web Scraping setup
media_urls = {
    "kompas": "https://www.kompas.com/",
    "detik": "https://www.detik.com/terpopuler?utm_source=wpmdetikcom&utm_medium=boxmostpop&utm_campaign=mostpop",
    "cnn": "https://www.cnnindonesia.com/nasional",
    "liputan6": "https://www.liputan6.com/",
    "suaramerdeka": "https://www.suaramerdeka.com/",
    "republika": "https://www.republika.co.id/",
    "tempo": "https://www.tempo.co/",
    "ayobandung": "https://www.ayobandung.com/",
    "jawapos": "https://www.jawapos.com/",
}

def class_filter(media_name):
    mapping = {
        "kompas": ("mostWrap", "div"),
        "detik": ("list-content", "div"),
        "cnn": ("overflow-y-auto relative h-[322px]", "div"),
        "liputan6": ("aside-list popular-analisis", "ul"),
        "suaramerdeka": ("most__wrap", "div"),
        "republika": ("table table-striped", "table"),
        "tempo": ("lg:divide-y-0 basis-1/2 lg:w-full grid divide-y divide-neutral-500", "div"),
        "ayobandung": ("most__wrap", "div"),
        "jawapos": ("most__wrap", "div"),
    }
    return mapping.get(media_name, (None, None))

async def fetch_with_bs4(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 403:
                return None
            html = await response.text()
            return BeautifulSoup(html, "html.parser")

async def scrape_news(name):
    try:
        url = media_urls.get(name)
        if not url:
            return f"URL not found for {name}"

        class_name, element_selector = class_filter(name)
        if not class_name:
            return f"Class name not defined for {name}"

        soup = await fetch_with_bs4(url)
        if not soup:
            return f"Error scraping {name}"

        container = soup.find(element_selector, class_=class_name)
        if not container:
            return f"Could not find container for {name}"

        headlines = container.find_all("h2")  # General headline selector for simplicity
        return [headline.text.strip() for headline in headlines][:5]

async def scrape_all_news(sources):
    tasks = [scrape_news(source) for source in sources]
    return await asyncio.gather(*tasks)

# Instagram Scraping setup
def create_driver():
    opts = Options()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    return driver

def login_instagram(driver):
    driver.get("https://www.instagram.com")
    username = WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password = WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
    username.clear()
    username.send_keys("your_username")
    password.clear()
    password.send_keys("your_password")
    WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Not now")]'))).click()

def scrape_instagram_posts(driver, account_name):
    driver.get(f"https://www.instagram.com/{account_name}/")
    data = []
    try:
        for i in range(3):  # Scrape 3 posts
            post_divs = WebDriverWait(driver, 200).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "_aagv"))
            )
            post_div = post_divs[i]
            driver.execute_script("arguments[0].scrollIntoView();", post_div)
            driver.execute_script("arguments[0].click();", post_div)
            time.sleep(2)

            caption = WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1._ap3a._aaco._aacu._aacx._aad7._aade"))
            ).text

            time_element = WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.TAG_NAME, "time"))
            )
            post_time = time_element.get_attribute("datetime")
            post_time = datetime.fromisoformat(post_time)

            post_link = driver.current_url

            data.append({
                "Account": account_name,
                "Caption": caption,
                "Time": post_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Link": post_link
            })
            driver.back()
            time.sleep(5)
    except Exception as e:
        st.error(f"Error with account {account_name}: {e}")
    return data

# Streamlit UI setup
st.set_page_config(page_title="News Comparison & Instagram Scraper", page_icon="📰", layout="wide")
st.sidebar.title("Choose Scraper Type")
scraper_type = st.sidebar.radio("Select scraper:", ["Scrape Web", "Scrape Instagram"])

if scraper_type == "Scrape Web":
    st.title("📰 News Scraper")
    st.markdown("This tool scrapes the latest headlines from various news outlets.")
    selected_sources = st.sidebar.multiselect(
        "Choose media to scrape:",
        options=list(media_urls.keys()),
        default=["kompas", "detik", "cnn"]
    )

    if st.sidebar.button("Scrape News"):
        if not selected_sources:
            st.warning("Please select at least one media source.")
        else:
            st.write("### Scraping Results")
            with st.spinner("Scraping news..."):
                all_news = {}
                results = asyncio.run(scrape_all_news(selected_sources))
                for i, source in enumerate(selected_sources):
                    all_news[source] = results[i]
                for source, headlines in all_news.items():
                    st.markdown(f"### {source.capitalize()}")
                    st.write(headlines)
            
elif scraper_type == "Scrape Instagram":
    st.title("📸 Instagram Post Scraper")
    account_input = st.sidebar.text_input("Enter Instagram account names (comma separated):")
    if st.sidebar.button("Scrape Posts"):
        if account_input:
            driver = create_driver()
            login_instagram(driver)
            accounts = [account.strip() for account in account_input.split(",")]
            all_posts = []
            for account in accounts:
                posts = scrape_instagram_posts(driver, account)
                all_posts.extend(posts)
            driver.quit()
            
            if all_posts:
                st.write("### Instagram Posts")
                for post in all_posts:
                    st.write(f"**{post['Account']}** - {post['Caption']} [{post['Link']}]")
            else:
                st.error("No posts found.")
        else:
            st.warning("Please enter Instagram account names.")
    
st.markdown("---")
st.write("Developed by **Mesakh Besta Anugrah** 🛡️")
