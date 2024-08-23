import os
import re
import logging
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from RPA.Browser.Selenium import Selenium
from RPA.Robocloud.Items import Items
import pandas as pd


class NewsScraper:

    def __init__(self):
        self.browser = Selenium()
        self.work_items = Items()
        self.search_phrase = ""
        self.news_category = ""
        self.months = 0
        self.results = []

    def load_work_item(self):
        work_item = self.work_items.get_input_work_item()
        self.search_phrase = work_item.get("search_phrase", "")
        self.news_category = work_item.get("news_category", "")
        self.months = int(work_item.get("months", 0))

    def open_website(self, url):
        self.browser.open_available_browser(url)
    
    def search_news(self):
        search_field = self.browser.find_element('//input[@type="text"]')
        search_field.send_keys(self.search_phrase)
        search_field.submit()

    def filter_news_by_category(self):
        try:
            category_element = WebDriverWait(self.browser.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//a[text()='{self.news_category}']"))
            )
            category_element.click()
        except TimeoutException:
            logging.warning("Category not found, proceeding without filtering.")

    def scrape_news(self):
        articles = self.browser.find_elements('//article')
        for article in articles:
            title = article.find_element(By.XPATH, './/h2').text
            date_text = article.find_element(By.XPATH, './/time').get_attribute("datetime")
            description = article.find_element(By.XPATH, './/p').text if article.find_elements(By.XPATH, './/p') else ""
            image = article.find_element(By.XPATH, './/img').get_attribute("src")
            date = datetime.strptime(date_text, "%Y-%m-%d")
            
            # Filter news by date range
            if self.is_within_date_range(date):
                search_count = self.count_search_phrase(title, description)
                contains_money = self.contains_money(title, description)
                self.results.append({
                    "title": title,
                    "date": date.strftime("%Y-%m-%d"),
                    "description": description,
                    "image_filename": os.path.basename(image),
                    "search_count": search_count,
                    "contains_money": contains_money
                })
                self.download_image(image)

    def is_within_date_range(self, date):
        start_date = datetime.today().replace(day=1) - timedelta(days=self.months * 30)
        return start_date <= date

    def count_search_phrase(self, title, description):
        return title.lower().count(self.search_phrase.lower()) + description.lower().count(self.search_phrase.lower())

    def contains_money(self, title, description):
        money_pattern = r'\$\d+(\.\d{1,2})?|(\d+|\d{1,3}(,\d{3})*)(\.\d{2})? (dollars|USD)'
        return bool(re.search(money_pattern, title)) or bool(re.search(money_pattern, description))

    def download_image(self, url):
        image_name = os.path.basename(url)
        self.browser.download(url, image_name)

    def save_to_excel(self, filename):
        df = pd.DataFrame(self.results)
        df.to_excel(filename, index=False)

    def close_browser(self):
        self.browser.close_browser()

    def run(self):
        try:
            self.load_work_item()
            self.open_website("https://example-news-website.com")
            self.search_news()
            self.filter_news_by_category()
            self.scrape_news()
            self.save_to_excel("news_results.xlsx")
        finally:
            self.close_browser()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    scraper = NewsScraper()
    scraper.run()