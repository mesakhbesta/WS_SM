import streamlit as st
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import pandas as pd

# Daftar URL sumber berita
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

# Mapping untuk filter class dan elemen selector
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

# Fungsi untuk mengambil HTML menggunakan BeautifulSoup dan aiohttp
async def fetch_with_bs4(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 403:
                return None
            html = await response.text()
            return BeautifulSoup(html, "html.parser")

# Menggunakan Firefox
def create_driver():
    firefox_options = Options()
    firefox_options.add_argument('--headless')  # Menggunakan mode headless
    firefox_options.add_argument('--disable-gpu')

    # Menggunakan Firefox WebDriver dengan GeckoDriverManager
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)
    return driver

# Fungsi untuk mengambil HTML menggunakan Selenium dengan Firefox
def fetch_with_selenium(url):
    driver = create_driver()
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return BeautifulSoup(html, "html.parser")

# Fungsi untuk mengscrape berita dari berbagai sumber
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
            soup = fetch_with_selenium(url)

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

# Fungsi untuk mengscrape berita dari semua sumber
async def scrape_all_news(sources):
    tasks = [scrape_news(source) for source in sources]
    return await asyncio.gather(*tasks)

# Streamlit layout
st.set_page_config(page_title="News Comparison", page_icon="📰", layout="wide")

st.title("📰 News Scrap & Comparison")

st.markdown(
    """
    This web allows you to compare top headlines from various media sources. Choose your preferred media outlets and click on **Scrape News** to get the latest updates.
    """
)

st.sidebar.header("🗂 Select News Sources")
selected_sources = st.sidebar.multiselect(
    "Choose media to scrape:",
    options=list(media_urls.keys()),
    default=list(media_urls.keys())[:3]
)

button_style = """
    <style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        padding: 10px 24px;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    </style>
"""
st.markdown(button_style, unsafe_allow_html=True)

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
                st.markdown(f"📍 <span style='font-size: 30px; font-weight: bold;'>{source.capitalize()}</span> - <a href='{media_urls[source]}' target='_blank' style='font-size: 15px;'>Read More</a>", unsafe_allow_html=True)
                
                headlines_data = []
                if isinstance(headlines, list):
                    for idx, headline in enumerate(headlines, start=1):
                        headlines_data.append({"Headline": headline})

                df = pd.DataFrame(headlines_data)
                df.reset_index(drop=True, inplace=True)
                df.index = df.index + 1 

                st.table(df)

st.markdown(
    """
    ---
    Developed by Mesakh Besta Anugrah🛡️.
    """
)
