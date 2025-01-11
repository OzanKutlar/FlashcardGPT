from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Headless mode
options.add_argument("--no-sandbox")  # Required for many VPS setups
options.add_argument("--disable-dev-shm-usage")  # Avoid /dev/shm issues
options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)

driver = webdriver.Chrome(options=options)

driver.get("https://www.example.com")
print(f"Title: {driver.title}")

driver.quit()