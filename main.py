import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from datetime import datetime
import time

def create_driver():
    opts = Options()
    #opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    return driver

def quit_driver():
    if "driver" in st.session_state and st.session_state.driver is not None:
        st.session_state.driver.quit()
        st.session_state.driver = None

def login_instagram():
    driver = st.session_state.driver
    driver.get("https://www.instagram.com")

    username = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    password = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))

    username.clear()
    username.send_keys("smmagang1")
    password.clear()
    password.send_keys("Arextiar11")

    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Not now")]'))).click()

def scrape_instagram_posts(account_name):
    driver = st.session_state.driver
    driver.get(f"https://www.instagram.com/{account_name}/")

    data = []
    try:
        for i in range(1):  # Ambil maksimal 3 postingan saja
            try:
                post_divs = WebDriverWait(driver, 60).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "_aagv"))
                )

                post_div = post_divs[i]
                driver.execute_script("arguments[0].scrollIntoView();", post_div)
                driver.execute_script("arguments[0].click();", post_div)
                time.sleep(2)

                caption = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1._ap3a._aaco._aacu._aacx._aad7._aade"))
                ).text

                time_element = WebDriverWait(driver, 60).until(
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

            except Exception:
                continue
    except Exception as e:
        st.error(f"Kesalahan pada akun {account_name}: {e}")
    return data

# Sidebar UI untuk input akun
st.sidebar.title("Instagram Post Scraper 📸")
st.sidebar.write("Masukkan beberapa akun yang ingin Anda scrape sekaligus atau pilih dari dropdown.")

account_input = st.sidebar.text_input("Masukkan nama akun (pisahkan dengan koma jika lebih dari satu):")
account_select = st.sidebar.multiselect("Atau pilih akun dari daftar:", [
    "infokejadian_semarang", "infokejadian_genuk",
    "infokejadiansemarang.new", "infokejadiansemarang_atas", 
    "infokriminalsemarang", "relawangabungansemarang", "informasiseputarsemarang",
    "semarang.gallery", "hangoutsemarang"
])

st.sidebar.caption("Contoh masukan manual: `infokejadian_semarang, infokriminalsemarang, akun_lainnya`")
st.sidebar.markdown("---")

# Tombol untuk memulai scraping
scrape_button = st.sidebar.button("Scrape Postingan 📥")

# Main UI untuk menampilkan hasil
st.title("Instagram Post Scraper 📸")
st.write("Selamat datang di aplikasi Instagram Post Scraper! 🚀")

if scrape_button:
    if account_input or account_select:
        account_names = [name.strip() for name in account_input.split(",")] if account_input else account_select

        # Mulai scraping, jika belum login, login terlebih dahulu
        if "driver" not in st.session_state:
            st.session_state.driver = create_driver()
            login_instagram()

        all_results = []
        for account_name in account_names:
            with st.spinner(f"Sedang mengambil data dari akun @{account_name}..."):
                results = scrape_instagram_posts(account_name)
                all_results.extend(results)

        if all_results:
            st.success("Scrape berhasil! 🎉 Berikut ringkasan datanya:")

            # Tampilan yang lebih rapi dan terstruktur
            for account_name in account_names:
                st.markdown(f"## 📸 @{account_name}")

                account_posts = [row for row in all_results if row['Account'] == account_name]

                for idx, row in enumerate(account_posts):
                    with st.expander(f"📑 Post {idx + 1}"):
                        st.write(f"**Caption:**")
                        st.markdown(f"<div style='overflow-x: scroll; max-width: 100%;'>{row['Caption']}</div>", unsafe_allow_html=True)
                        st.write(f"**Waktu:** {row['Time']}")
                        st.write(f"**Link:** [Lihat Postingan]({row['Link']})")
            
        else:
            st.error("Tidak ada data yang berhasil diambil 😞")
    else:
        st.error("Mohon masukkan nama akun Instagram!")

# Footer
st.markdown("---")
st.write("Developed by **Mesakh Besta Anugrah** 🚀")

