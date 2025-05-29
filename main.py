import os
import time
import csv
import sqlite3
import logging
import pandas as pd
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
USERNAME = os.getenv("ECOMMERCE_USERNAME")
PASSWORD = os.getenv("ECOMMERCE_PASSWORD")
BASE_URL = "https://www.saucedemo.com"  # Example site

# Configure logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configure ChromeDriver
options = Options()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# SQLite setup
conn = sqlite3.connect("products.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS products
              (id TEXT PRIMARY KEY, name TEXT, price REAL)''')

# Login function
def login():
    logging.info("Attempting login...")
    driver.get(BASE_URL)
    time.sleep(2)
    driver.find_element(By.ID, "user-name").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "login-button").click()
    time.sleep(2)
    if "inventory" in driver.current_url:
        logging.info("Login successful")
    else:
        logging.error("Login failed")
        raise Exception("Login failed")

# Scraping function
def scrape_products():
    logging.info("Scraping products...")
    products = driver.find_elements(By.CLASS_NAME, "inventory_item")
    for product in products:
        try:
            name = product.find_element(By.CLASS_NAME, "inventory_item_name").text
            price = product.find_element(By.CLASS_NAME, "inventory_item_price").text
            product_id = product.find_element(By.CLASS_NAME, "inventory_item_img").find_element(By.TAG_NAME, "img").get_attribute("src")
            price = float(price.replace("$", ""))
            cursor.execute("INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)", (product_id, name, price))
            conn.commit()
        except Exception as e:
            logging.error(f"Error scraping product: {str(e)}")

# Report generation
def generate_report():
    logging.info("Generating report...")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    df.to_csv("products_report.csv", index=False)

    plt.figure(figsize=(10,6))
    plt.hist(df['price'], bins=10, color='skyblue', edgecolor='black')
    plt.title("Price Distribution")
    plt.xlabel("Price")
    plt.ylabel("Count")
    plt.savefig("price_distribution.png")
    plt.close()

# Main workflow
if __name__ == '__main__':
    try:
        login()
        scrape_products()
        generate_report()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        driver.quit()
        conn.close()
