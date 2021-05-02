from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from pathlib import Path
import requests


class TaxScrapper:
    driver: webdriver.Chrome
    wait: WebDriverWait

    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome("./drivers/chromedriver.exe", options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def load_main(self):
        self.driver.get("https://apps.irs.gov/app/picklist/list/formsPublications.html")
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "picklistTable")))

    @staticmethod
    def fix_year(year_end):
        # Костыль для исправления года пересмотра
        # Где-то указан год, где-то месяц и последние 2 цифры года
        # Fix for Revision Dates
        # There are 2 variants: month and 2 digits of year; full year
        if int(year_end) <= 21:
            year = int(f"20{year_end}")
        else:
            year = int(f"19{year_end}")
        return year

    def get_tax_forms(self, args):
        output = []
        self.load_main()
        for name in args["forms"]:
            print(f"Getting information about {name}")
            years = []
            self.driver.find_element_by_id("searchFor").clear()
            self.driver.find_element_by_id("searchFor").send_keys(name)
            self.driver.find_element_by_name("submitSearch").click()
            self.wait.until(EC.url_changes)
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "picklistTable")))
            elements = self.driver.find_elements_by_link_text(name)
            if not elements:
                print(F"Form \"{name}\" not found!")
                continue
            for ele in elements:
                tr = ele.find_element_by_xpath('./../..')
                tds = tr.find_elements_by_tag_name("td")
                title = tds[1].text
                year_end = tds[2].text[-2:]
                year = self.fix_year(year_end)
                years.append(year)
            years.sort()
            min_year = years[0]
            max_year = years[-1]
            output.append(
                {
                    "form_number": name,
                    "form_title": title,
                    "min_year": min_year,
                    "max_year": max_year
                }
            )
            print("Got it!")
        json.dump(output, open("taxes.json", 'w', encoding="utf-8"), indent=4)

    def get_pdfs(self, args):
        self.load_main()
        name = args["name"]
        self.driver.find_element_by_id("searchFor").send_keys(name)
        self.driver.find_element_by_name("submitSearch").click()
        self.wait.until(EC.url_changes)
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "picklistTable")))
        frm, to = [int(year) for year in args["range"].split("-")]
        elements = self.driver.find_elements_by_link_text(name)
        if not elements:
            print(F"Form \"{name}\" not found!")
            return
        Path(f"./{name}").mkdir(exist_ok=True)
        for ele in elements:
            tr = ele.find_element_by_xpath('./../..')
            tds = tr.find_elements_by_tag_name("td")
            year_end = tds[2].text[-2:]
            year = self.fix_year(year_end)
            if frm <= year <= to:
                url = tds[0].find_element_by_tag_name("a").get_attribute("href")
                print(f"Trying download {name}-{year} PDF...")
                resp = requests.get(url)
                if resp.status_code != 200:
                    print(f"Error while downloading PDF. Status code: {resp.status_code}")
                else:
                    print("Downloading success!")
                    with open(f"./{name}/{name}-{year}.pdf", 'wb') as file:
                        file.write(resp.content)


if __name__ == '__main__':
    args = json.loads(open("input.json", 'r', encoding="utf-8").read())
    ts = TaxScrapper()
    ts.init_driver()
    try:
        if args["action"] == "Download PDF":
            print("Downloading PDF")
            ts.get_pdfs(args["args"])
        elif args["action"] == "Get taxes form info":
            print("Getting taxes forms info")
            ts.get_tax_forms(args["args"])
    except Exception as e:
        # Broad exception to make sure the driver turns off
        print(e)
    finally:
        ts.driver.close()
