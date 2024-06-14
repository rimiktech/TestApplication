import os
import time
import requests
from airtable import Airtable
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
load_dotenv()

logs_path = "./"

def log(message):
    try:
        message = "{0:%Y-%m-%d %H:%M:%S} {1}".format(datetime.now(), message)
        print(message)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        fileName = "{0}/{1}.{2:%m%d%y}.log"
        fileName = fileName.format(logs_path, "automation", datetime.now())
        with open(fileName, "a") as file:
            file.write(str(message) + "\n")
    except Exception as err:
        print(err)


class AirtableManager:
    def __init__(self):
        # Airtable keys
        self.airtable_api_key = os.getenv("API_KEY")
        self.airtable_base_id = os.getenv("BASE_ID")
        self.airtable_product = os.getenv("TABLE")
         
     

    def get_url_list(self):
        try:
            airtable = Airtable(self.airtable_base_id, self.airtable_product, api_key=self.airtable_api_key)
            all_url_list = []
            views=["viwEoQqCqAV7GtUlM","viwOEZRrMox33wBBS","viwsfe0mW93UAEELH"]
        
            for view_id in  views:            
                result = airtable.get_all(view=view_id)  # Use view_id directly
                url_list = [{'id': record['id'], 'url': record['fields'].get('Source URL')} for record in result if 'Source URL' in record['fields']]
                log("Total Url found for update in view '{0}':{1}".format(view_id, len(url_list)))
                all_url_list.extend(url_list)
            return all_url_list
        except Exception as e:
            log(f"Exception occurred in get_url_list(): {e}")


    def update_status(self, record_id, status,target_column=None):
        try:
            airtable = Airtable(self.airtable_base_id, self.airtable_product, api_key=self.airtable_api_key)
           
            if record_id and status:
                update_result = airtable.update(record_id, {target_column: status})
                log(f"Updated record {record_id} with status: {status}")
                return update_result
            else:
                log(f"Record id or status not found")
        except Exception as e:
            log(f"Error in update in airtable:{e}")


def view1(url,record_id):
    try:
        manager=AirtableManager()
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            stock_status = soup.find(id="ctl00_contentBody_lblStockStatus")
            if stock_status:
                status_text = stock_status.get_text().strip()
                if status_text:
                    log(f"Status of Stock:{status_text}")
                    manager.update_status(record_id, status_text,"CASIberia Stock Status")
                    log(f"Record update successfully for Url:{url}")
                else:
                    stock_status1 = soup.find(id="ctl00_contentBody_pnlDiscontinued")
                    status_text1 = stock_status1.get_text().strip()
                    log(f"Status of Stock:{status_text1}")
                    manager.update_status(record_id, status_text1,"CASIberia Stock Status")
                    log(f"Record update successfully for Url:{url}")
            else:
                log(f"Element with id 'ctl00_contentBody_lblStockStatus' not found.{url}")
        else:
            log(f"Failed to retrieve the page. Status code: {response.status_code}")
            log(f"Failed to retrieve the page url:{url}")

    except Exception as e:
        log(f"Error in views1 {e}")

def view2(url,record_id):
    try:
        manager=AirtableManager()
        response=requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract the text of the element with the specific id
            stock_status = soup.find(id="form-action-addToCart")
            if stock_status:
                status_text = stock_status.text
                if status_text == "Add to Cart":
                    log(f"Status of Stock:{status_text}")
                    manager.update_status(record_id, "In Stock!","Windlass Stock Status")
                    log(f"Record update successfully for Url:{url}")
                else:
                    
                    stock_status_element = soup.find(id="form-action-addToCart") 
                    stock_status_text=stock_status_element.get_text()
                    if stock_status_text=="Pre-Order Now":
                        manager.update_status(record_id, "This product is on BackOrder and will be shipped later","Windlass Stock Status")
                        log(f"Record update successfully for Url:{url}")
                    else:
                        manager.update_status(record_id, "Out of stock","Windlass Stock Status")
                        log(f"Record update successfully for Url:{url}")


    except Exception as e:
        log(f"Error in occured in view2:{e}")

def view3(url,record_id):
    try:
        manager=AirtableManager()
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (optional)
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
    
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        stock_status_element = soup.find('div', class_='bo-inventory-description')
        if stock_status_element:
            stock_status = stock_status_element.get_text()         
            manager.update_status(record_id, stock_status,"Windlass Stock Status")
        else:
            stock_status = soup.find(id="form-action-addToCart")
            if stock_status:
                status_text = stock_status.get("value")        
                if status_text == "Add to Cart":
                    log(f"Status of Stock:{status_text}")
                    manager.update_status(record_id, "In Stock Now!","Windlass Stock Status")
                    log(f"Record update successfully for Url:{url}")
                elif  status_text=="Pre-Purchase":
                    log(f"Status of Stock:{status_text}")
                    manager.update_status(record_id, "Not in Stock. Pre-Purchase Available.","Windlass Stock Status")
                    log(f"Record update successfully for Url:{url}")

                else:
                    manager.update_status(record_id, "Out of Stock","Windlass Stock Status")
    except Exception as e:
        log(f"Error in view3 as{e}")

def main():
    try:
      
        manager = AirtableManager()
        url_list = manager.get_url_list()
        if url_list:
            for item in url_list:
                record_id = item['id']
                url = item['url']
                if url.startswith("https://www.atlantacutlery.com/"):
                    log("URL starts with https://www.atlantacutlery.com/")
                    view3(url,record_id)
                elif url.startswith("https://www.museumreplicas.com/"):                
                    log("URL starts with https://www.museumreplicas.com/")
                    view2(url,record_id)
                elif url.startswith("https://casiberia.com/"):
                    log("URL starts with https://casiberia.com/")
                    view1(url,record_id)
                else:        
                    log("No URLs found in the Airtable data.")
    except Exception as e:
        log(f"Error in Main():{e}")        

if __name__ == "__main__":
    main()
