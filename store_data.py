import os
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import streamlit as st
import pandas as pd

# Part 1: Data Scraping with Selenium
def scrape_redbus_data():
    """Scrape bus data from Redbus website and return as a list of dictionaries."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome()
    driver.get("https://www.redbus.in/")
   

    time.sleep(5)  # Allow the page to load

    # Example interactions 
    buses = []
    
    # Perform scraping logic here
    # Example: Scraping bus details
    bus_elements = driver.find_elements(By.CSS_SELECTOR, '.clearfix bus-item')
    for bus_element in bus_elements:
        try:
            route_name = bus_element.find_element(By.CSS_SELECTOR, '.D136_h1').text
            bus_name = bus_element.find_element(By.CSS_SELECTOR, '.travels lh-24 f-bold d-color').text
            bus_type = bus_element.find_element(By.CSS_SELECTOR, '.bus-type f-12 m-top-16 l-color evBus').text
            departing_time = bus_element.find_element(By.CSS_SELECTOR, '.dp-time f-19 d-color f-bold').text
            duration = bus_element.find_element(By.CSS_SELECTOR, '.dur l-color lh-24').text
            reaching_time = bus_element.find_element(By.CSS_SELECTOR, '.bp-time f-19 d-color disp-Inline').text
            star_rating = float(bus_element.find_element(By.CSS_SELECTOR, '.icon icon-ic-star d-block').text)
            price = float(bus_element.find_element(By.CSS_SELECTOR, '.fare d-block').text.replace('Rs', '').strip())
            seats_available = int(bus_element.find_element(By.CSS_SELECTOR, '.seat-left m-top-30').text.split()[0])

            buses.append({
                'route_name': route_name,
                'bus_name': bus_name,
                'bus_type': bus_type,
                'departing_time': departing_time,
                'duration': duration,
                'reaching_time': reaching_time,
                'star_rating': star_rating,
                'price': price,
                'seats_available': seats_available
            })
        except Exception as e:
            print(f"Error scraping bus element: {e}")

    driver.quit()
    return buses

# Part 2: Storing Data in SQL Database
def store_data_in_db(buses):
    """Store scraped bus data in SQLite database."""
    conn = sqlite3.connect('buses.db')
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bus_routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT,
        bus_name TEXT,
        bus_type TEXT,
        departing_time TEXT,
        duration TEXT,
        reaching_time TEXT,
        star_rating REAL,
        price REAL,
        seats_available INTEGER
    )
    ''')

    # Insert data
    for bus in buses:
        cursor.execute('''
        INSERT INTO bus_routes (route_name, bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seats_available)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bus['route_name'],
            bus['bus_name'],
            bus['bus_type'],
            bus['departing_time'],
            bus['duration'],
            bus['reaching_time'],
            bus['star_rating'],
            bus['price'],
            bus['seats_available']
        ))

    conn.commit()
    conn.close()

# Part 3: Streamlit Application
def load_data_from_db():
    """Load data from the SQLite database."""
    conn = sqlite3.connect('buses.db')
    df = pd.read_sql_query("SELECT * FROM bus_routes", conn)
    conn.close()
    return df

def streamlit_app():
    """Run the Streamlit application."""
    st.title("Redbus Data Viewer")

    # Load data
    data = load_data_from_db()

    if data.empty:
        st.write("No data available. Please scrape data first.")
        return

    # Filters
    bus_type = st.selectbox("Select Bus Type", options=["All"] + data['bus_type'].unique().tolist())
    price_range = st.slider("Select Price Range", min_value=float(data['price'].min()), max_value=float(data['price'].max()), value=(float(data['price'].min()), float(data['price'].max())))
    star_rating = st.slider("Minimum Star Rating", min_value=0.0, max_value=5.0, value=3.0, step=0.1)

    filtered_data = data
    if bus_type != "All":
        filtered_data = filtered_data[filtered_data['bus_type'] == bus_type]

    filtered_data = filtered_data[(filtered_data['price'] >= price_range[0]) & (filtered_data['price'] <= price_range[1])]
    filtered_data = filtered_data[filtered_data['star_rating'] >= star_rating]

    st.dataframe(filtered_data)

if __name__ == "__main__":
    # Uncomment to scrape data and store in DB
    buses = scrape_redbus_data()
    store_data_in_db(buses)

    streamlit_app()
