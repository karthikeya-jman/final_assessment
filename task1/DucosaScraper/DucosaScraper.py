from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def get_project_urls(page):
    page.goto("https://ducosa.com/sitio/")
    # Wait for the menu or project links to load
    page.wait_for_selector('div.vc_grid-container')
    # Extract all project URLs from the menu or page content
    links = page.query_selector_all('div.vc_gitem-post-data-source-post_title a')
    print(f"Found {len(links)} links on the main page.")
    project_urls = []
    for link in links:
        href = link.get_attribute('href')
        # Filter URLs that look like project pages (adjust as needed)
        # if href and ('comercial' in href or 'hoteles' in href or 'industrial' in href or 'institucional' in href or 'residencial' in href):
        project_urls.append(href)
    return list(set(project_urls))  # Remove duplicates

def scrape_customers_and_links(page, project_url):
    page.goto(project_url)
    # Wait for the dynamic grid container to load
    page.wait_for_selector('.vc_grid-container a', timeout=15000)
    content = page.content()
    soup = BeautifulSoup(content, 'html.parser')

    customers = {}
    # Find all divs with class 'row'
    for div_row in soup.find_all('div', class_='row'):
        wpb_wrapper = div_row.find('div', class_='wpb_wrapper')
        if wpb_wrapper:
            customer_name = wpb_wrapper.get_text(strip=True)
            # Find all anchor tags inside this div_row
            anchors = div_row.find_all('a', href=True)
            hrefs = [a['href'] for a in anchors]
            if customer_name:
                customers[customer_name] = hrefs
    return customers

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Get all project URLs
        project_urls = get_project_urls(page)
        print("Project URLs found:")
        for url in project_urls:
            print(url)

        # Step 2: For each project URL, scrape customer names and their links
        for url in project_urls:
            print(f"\nScraping customers from project: {url}")
            customers = scrape_customers_and_links(page, url)
            for customer, links in customers.items():
                print(f"Customer: {customer}")
                for link in links:
                    print(f"  Link: {link}")

        browser.close()

if __name__ == "__main__":
    main()