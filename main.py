import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import pandas as pd
import time

# Initialize WebDriver with correct timeout settings
def init_webdriver():
    try:
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set timeouts explicitly as integers or None
        driver.set_page_load_timeout(30)  # Timeout for page load in seconds
        driver.implicitly_wait(10)        # Implicit wait for elements (in seconds)
        
        return driver
    except Exception as e:
        st.error(f"Error initializing WebDriver: {e}")
        return None

# Scrape a single website
def scrape_website(url, driver):
    scraped_data = []
    try:
        st.write(f"Scraping: {url}")
        driver.get(url)
        time.sleep(3)  # Allow the page to fully load

        # Example selectors (Adjust these to match website structure)
        products = driver.find_elements(By.CSS_SELECTOR, ".product-item")  # Update as needed
        for product in products:
            try:
                product_url = urljoin(url, product.find_element(By.CSS_SELECTOR, "a").get_attribute("href"))
                product_title = product.find_element(By.CSS_SELECTOR, "h2").text.strip()
                product_description = (
                    product.find_element(By.CSS_SELECTOR, ".description").text.strip() if product.find_elements(By.CSS_SELECTOR, ".description") else "N/A"
                )
                product_price = (
                    product.find_element(By.CSS_SELECTOR, ".price").text.strip() if product.find_elements(By.CSS_SELECTOR, ".price") else "N/A"
                )
                product_stock = "In Stock" if "in stock" in product.text.lower() else "Out of Stock"

                # Extract images and tags
                product_images = [
                    img.get_attribute("src")
                    for img in product.find_elements(By.CSS_SELECTOR, "img")
                ]
                product_tags = ", ".join(
                    [tag.text for tag in product.find_elements(By.CSS_SELECTOR, ".tag")]
                )

                scraped_data.append({
                    "Title": product_title,
                    "Description": product_description,
                    "Price": product_price,
                    "Stock": product_stock,
                    "Tags": product_tags,
                    "Images": "; ".join(product_images),
                    "URL": product_url,
                })
            except Exception as inner_e:
                st.warning(f"Error scraping product: {inner_e}")

    except Exception as e:
        st.error(f"Failed to scrape {url}: {e}")
    return scraped_data

# Streamlit UI
st.title("High-End Clothing Brands Product Scraper")

# Input brand URLs
brand_urls = st.text_area(
    "Enter the URLs of the clothing brand websites (one URL per line):",
    placeholder="https://www.examplebrand.com\nhttps://www.anotherbrand.com"
)

if st.button("Scrape Products"):
    if brand_urls.strip():
        urls = brand_urls.splitlines()
        all_scraped_data = []
        driver = init_webdriver()  # Initialize WebDriver
        if driver:
            for url in urls:
                data = scrape_website(url, driver)
                all_scraped_data.extend(data)

            # Close WebDriver
            driver.quit()

            if all_scraped_data:
                # Convert to DataFrame
                df = pd.DataFrame(all_scraped_data)

                # Display results and allow download
                st.write("Scraping completed successfully!")
                st.dataframe(df)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="scraped_products.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data was scraped. Ensure the selectors are correct for the websites.")
        else:
            st.error("WebDriver initialization failed.")
    else:
        st.error("Please enter at least one URL.")
