from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import time, random
import pandas as pd
import threading
from queue import Queue 
import json

class JobSeeker:
    def __init__(self, keywords_list, location_list, max_search_limit):
        self.driver = webdriver.Chrome(self.get_chrome_options())
        self.keywords_list = keywords_list
        self.location_list = location_list
        self.max_search_limit = max_search_limit
        
        self.job_extraction_queue = Queue(maxsize = 0)
        self.job_processing_thread_list = []
        self.run_ok = True
        self.done = False

        self.job_queue_thread = threading.Thread(target=self.process_job_queue)        
        self.job_queue_thread.start()

        self.job_dict = {}
        
    def get_chrome_options(self, headless = True):
        # Set window to maximized
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        return options

    def get_curr_num_jobs(self):
        job_list = self.driver.find_element(By.CLASS_NAME, 'jobs-search__results-list')
        jobs = job_list.find_elements(By.TAG_NAME, 'li')
        
        return len(jobs)     
    
    def process_job_details(self, identifier_key, job_link):
        max_retries = 5
        while max_retries != 0:
            web_driver =  webdriver.Chrome(self.get_chrome_options())
            web_driver.get(job_link)
            time.sleep(3)

            job_desc0 = None
            seniority0 = None
            emp_type0 = None
            industry0 = None
            
            try:
                job_desc_xpath = "/html/body/main/section[1]/div/div/section[1]/div/div"
                job_desc0 = web_driver.find_element(By.XPATH, job_desc_xpath).get_attribute('innerText')
            except Exception as e:
                job_desc0 = "NA"
                            
            try:
                seniority_path_xpath = '/html/body/main/section[1]/div/div/section[1]/div/ul/li[1]/span'
                seniority0 = web_driver.find_element(By.XPATH, seniority_path_xpath).get_attribute('innerText')
            except Exception as e:
                seniority0 = "NA"
                
            try:
                employment_type_xpath = '/html/body/main/section[1]/div/div/section[1]/div/ul/li[2]/span'
                emp_type0 = web_driver.find_element(By.XPATH, employment_type_xpath).get_attribute('innerText')
            except:
                emp_type0 = "NA"
                
            try:
                industry_xpath = '/html/body/main/section[1]/div/div/section[1]/div/ul/li[4]/span'
                industry0 = web_driver.find_element(By.XPATH, industry_xpath).get_attribute('innerText')
            except:
                industry0 = "NA"
                
            if job_desc0 == "NA" and seniority0 == "NA" and industry0 == "NA":
                max_retries-=1
            else:        
                max_retries = 0
                self.job_dict[identifier_key].update(
                    {
                        "Job Description": job_desc0,
                        "Seniority": seniority0,
                        "Employment Type": emp_type0,
                        "Industry": industry0
                    }
                )

            web_driver.close()
        print(f"Processed Job Details for {identifier_key}")
            
    def process_job_queue(self):
        while self.run_ok:
            if not self.job_extraction_queue.empty():
                idenitifer_key, job_link = self.job_extraction_queue.get()
                thread = threading.Thread(target=self.process_job_details, args=(idenitifer_key, job_link))
                thread.start()
                self.job_processing_thread_list.append(thread)
            
            time.sleep(2)            

        for thread in self.job_processing_thread_list:
            thread.join()

    def generate_full_search_list(self):
        curr_num_jobs = self.get_curr_num_jobs()
        max_retry = 60 # Retry for 30 seconds
        print(f"Found {curr_num_jobs} jobs till now..")

        while max_retry != 0:
            print("Scrolling....")
            page = self.driver.find_element(By.TAG_NAME, "html")
            page.send_keys(Keys.END)
            try:
                see_more_jobs_btn = self.driver.find_element(By.CLASS_NAME, 'infinite-scroller__show-more-button')
                see_more_jobs_btn.click()
                time.sleep(0.5)
            except Exception as e:
                time.sleep(0.5)
                
            if self.get_curr_num_jobs() > curr_num_jobs:
                curr_num_jobs = self.get_curr_num_jobs()
                max_retry = 60
                print(f"Found {curr_num_jobs} jobs till now..")
            else:
                max_retry-=1

            if curr_num_jobs >= self.max_search_limit:
                max_retry = 0
            
    def extract_job_info(self):
        job_list = self.driver.find_element(By.CLASS_NAME, 'jobs-search__results-list')
        jobs = job_list.find_elements(By.TAG_NAME, 'li')  
        
        print(f"Scraping through {len(jobs)} number of jobs to extract information.")
        counter = 1
                        
        for job in jobs:                   
            job_title0 = None
            company_name0 = None
            location0 = None
            date0 = None
            job_link0 = None

            # Extract top level info
            try:
                job_title0 = job.find_element(By.CSS_SELECTOR, 'h3').get_attribute('innerText')
            except Exception as e:
                job_title0 = "NA"
        
            try:
                company_name0 = job.find_element(By.CSS_SELECTOR, 'h4').get_attribute('innerText')
            except Exception as e:
                company_name0 = "NA"
                
            try:
                location0 = job.find_element(By.CSS_SELECTOR, '[class="job-result-card__location"]').get_attribute('innerText')
            except Exception as e:
                location0 = "NA"

            try:
                date0 = job.find_element(By.CSS_SELECTOR, 'div>div>time').get_attribute('datetime')
            except Exception as e:
                date0 = "NA"

            try: 
                job_link0 = job.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except Exception as e:
                job_link0 = "NA"            
                        
            ## Get details
            if job_link0 != "NA" and job_title0 != "NA":
                identifier_key = job_title0 + "_!@#_" + job_link0
                ## Check for duplicates
                if identifier_key not in self.job_dict:                
                    self.job_dict[identifier_key] = {
                        "Job Title": job_title0,
                        "Company Name": company_name0,
                        "Location": location0,
                        "Date": date0,
                        "Job Link": job_link0,
                    }
                    
                    self.job_extraction_queue.put((identifier_key, job_link0))
                
            print(f"Extracted {counter}/{len(jobs)} jobs")
            counter+=1
            time.sleep(0.5)

    def get_results(self):
        job_data_list = list(self.job_dict.values())        
        df = pd.DataFrame(job_data_list)
        return df

    def save_to_csv(self, filename):
        # Convert the dictionary to a list of dictionaries
        print("Saving to csv...")
        job_data_list = list(self.job_dict.values())        
        df = pd.DataFrame(job_data_list)
        df.to_csv(f"{filename}.csv")
               
    def start(self):
        self.done = False
        for keyword in self.keywords_list:
            for location in self.location_list:
                # Open Linkedin with the search parameters
                url = f'https://www.linkedin.com/jobs/search?keywords={keyword.replace(" ", "%20")}&location={location.replace(" ", "%2C%20").replace(",", "%2C")}'
                self.driver.get(url)
                time.sleep(3)
                
                # Get a list of all jobs with elements
                self.generate_full_search_list()
                                
                # Get job info
                job_info = self.extract_job_info()
                
                while not self.job_extraction_queue.empty():
                    time.sleep(0.5)
                    
                self.run_ok = False
                self.job_queue_thread.join()
                                
        self.driver.close()
        self.done = True

    def is_job_done(self):
        return self.done

if __name__ == "__main__":
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    f = open(config_file) 
    config_data = json.load(f)
    job_seeker_obj = JobSeeker(config_data["keywords"], config_data["locations"], config_data["max_limit"])