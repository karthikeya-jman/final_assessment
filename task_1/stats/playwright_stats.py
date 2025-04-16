from playwright.sync_api import sync_playwright
import time
 
# URL to request
urls = [
#     'https://www.zeeconvent.be',
# 'https://www.priceforbes.com',
'https://ducosa.com'
# 'https://www.nexyan.be',
# 'https://www.juistekredietkeuzes.be'
]

 
# Function to measure request time for a single request
def one_request_time(page, url):
    start_time = time.time()  # Start the timer
    response1 = page.goto(url)  # Navigate to the URL
    end_time = time.time()  # End the timer
    duration1 = end_time - start_time  # Calculate the duration
    start_time = time.time()  # Start the timer
    response2 = page.goto(url)  # Navigate to the URL
    end_time = time.time()  # End the timer
    duration2 = end_time - start_time  # Calculate the duration
    return response2, duration2
 
# Function to measure request time for multiple requests
def multiple_request_time(page, count, url):
    start_time = time.time()  # Start the timer for multiple hits
    for _ in range(count):
        response = page.goto(url)  # Navigate to the URL
    end_time = time.time()  # End the timer
    duration_multiple = end_time - start_time  # Calculate the total duration
    return response, duration_multiple
 
# Main function to run the Playwright script
def run_playwright():
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=True)  # Set headless=True to run in headless mode
        context = browser.new_context()
        page = context.new_page()
 
        for url in urls:
            print(f"url: {url}")
 
            # Measure time for a single request
            response_single_hit, duration_single_hit = one_request_time(page, url)
            print(f"Single request to {url} took {duration_single_hit:.2f} seconds. Status Code: {response_single_hit.status}")
 
            # Measure time for 100 requests
            response_of_100_hits, duration_of_100_hits = multiple_request_time(page, 100, url)
            print(f"100 requests to {url} took {duration_of_100_hits:.2f} seconds. Last Status Code: {response_of_100_hits.status}")
 
        # Close the browser
        browser.close()
 
# Run the Playwright function
run_playwright()