import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from datetime import datetime
import time
import asyncio
from bs4 import BeautifulSoup
import aiohttp

# Media URLs for web scraping
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

# Function for Web Scraping
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
        container = soup.find(element_selector, class_=class_name)
        if not container:
            return f"Could not find container for {name}"

        if name == "kompas":
            headlines = container.find_all(class_="mostTitle")
        elif name == "detik":
            headlines = container.find_all(class_="media__title")
        elif name == "cnn":
            headlines = container.find_all("h2", class_="text-base text-cnn_black_light group-hover:text-cnn_red")
        elif name == "liputan6":
            headlines = container.find_all("h4", class_="article-snippet--numbered__title")
        elif name == "suaramerdeka":
            headlines = container.find_all("h2", class_="most__title")
        elif name == "republika":
            headlines = container.find_all("a", rel="tooltip")
        elif name == "tempo":
            headlines = container.find_all("a", class_="hover:opacity-75")
        elif name == "ayobandung" or name == "jawapos":
            headlines = container.find_all("h2", class_="most__title")

        return [headline.text.strip() for headline in headlines if headline.text.strip()][:5]

    except Exception as e:
        return [f"Error: {e}"]

async def scrape_all_news(sources):
    tasks = [scrape_news(source) for source in sources]
    return await asyncio.gather(*tasks)

# Instagram Scraping Functions
def create_driver():
    opts = Options()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    return driver

def login_instagram():
    driver = st.session_state.driver
    driver.get("https://www.instagram.com")
    username = WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password = WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
    username.clear()
    username.send_keys("your_username")
    password.clear()
    password.send_keys("your_password")
    WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    WebDriverWait(driver, 200).until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Not now")]'))).click()

def scrape_instagram_posts(account_name):
    driver = st.session_state.driver
    driver.get(f"https://www.instagram.com/{account_name}/")
    data = []
    for i in range(3):  # Ambil maksimal 3 postingan
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
    return data

# Streamlit UI
st.set_page_config(page_title="Scraping Comparison", page_icon="🔍")

# Tab Menu
menu = st.radio("Select Scraping Option", ("Web Scraping", "Instagram Scraping"))

# Web Scraping
if menu == "Web Scraping":
    st.title("Web Scraping")
    selected_sources = st.sidebar.multiselect("Choose media to scrape:", options=list(media_urls.keys()), default=list(media_urls.keys())[:3])
    if st.sidebar.button("Scrape News"):
        if not selected_sources:
            st.warning("Please select at least one media source.")
        else:
            st.write("### Scraping Results")
            with st.spinner('Scraping news...'):
                all_news = {}
                results = asyncio.run(scrape_all_news(selected_sources))
                for i, source in enumerate(selected_sources):
                    all_news[source] = results[i]
                for source, headlines in all_news.items():
                    st.markdown(f"📍 **{source.capitalize()}**")
                    for headline in headlines:
                        st.write(f"- {headline}")

# Instagram Scraping
elif menu == "Instagram Scraping":
    st.title("Instagram Post Scraper 📸")
    account_input = st.sidebar.text_input("Enter Instagram usernames (comma separated):")
    account_select = st.sidebar.multiselect("Or select accounts from the list:", [
        "infokejadian_semarang", "infokejadian_genuk",
        "infokejadiansemarang.new", "infokejadiansemarang_atas", 
        "infokriminalsemarang", "relawangabungansemarang", "informasiseputarsemarang",
        "semarang.gallery", "hangoutsemarang"
    ])
    if st.sidebar.button("Scrape Posts 📥"):
        if account_input or account_select:
            account_names = [name.strip() for name in account_input.split(",")] if account_input else account_select
            if "driver" not in st.session_state:
                st.session_state.driver = create_driver()
                login_instagram()
            all_results = []
            for account_name in account_names:
                with st.spinner(f"Scraping data from @{account_name}..."):
                    results = scrape_instagram_posts(account_name)
                    all_results.extend(results)
            if all_results:
                st.success("Scrape successful! 🎉")
                for account_name in account_names:
                    st.markdown(f"## @{account_name}")
                    account_posts = [row for row in all_results if row['Account'] == account_name]
                    for idx, row in enumerate(account_posts):
                        with st.expander(f"Post {idx + 1}"):
                            st.write(f"**Caption:** {row['Caption']}")
                            st.write(f"**Time:** {row['Time']}")
                            st.write(f"**Link:** [View Post]({row['Link']})")
            else:
                st.error("No data retrieved 😞")
        else:
            st.error("Please enter at least one Instagram account.")
