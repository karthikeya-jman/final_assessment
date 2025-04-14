import requests
from bs4 import BeautifulSoup
from pprint import pprint
import os

class NexyanScraper:
    def __init__(self, base_url="https://www.nexyan.be"):
        self.base_url = base_url
        self.headers = {"Accept-Language": "en"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_soup(self, url, cache_file=None):
        """
        Fetches and returns BeautifulSoup object for a given URL.
        If a cache_file is provided and exists, loads from the file instead of making a request.
        """
        if cache_file and os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return BeautifulSoup(f.read(), 'html.parser')
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        if cache_file:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
        return soup

    def get_services(self):
        """
        Scrapes all service links and their content from the homepage.
        Returns a dictionary with service names as keys and page text as values.
        """
        homepage_soup = self.fetch_soup(self.base_url, cache_file="nexyan_home.html")
        service_urls = {}

        for li in homepage_soup.find_all('li', class_='menu-item-object-service'):
            a_tag = li.find('a')
            if a_tag:
                name = a_tag.text.strip()
                url = a_tag['href']
                service_urls[name] = url

        service_details = {}
        for name, url in service_urls.items():
            try:
                soup = self.fetch_soup(url)
                content = soup.find('article', class_='uk-article')
                text = content.get_text(strip=True) if content else "No content found"
                service_details[name] = text
            except Exception as e:
                print(f"Failed to fetch service {name}: {e}")
        return service_details

    def get_team_details(self):
        """
        Scrapes 'About Us' page and collects team member names, titles, and profile descriptions.
        Returns a dictionary of team member details.
        """
        about_url = f"{self.base_url}/about-us/"
        soup = self.fetch_soup(about_url, cache_file="nexyan_about.html")
        team_details = {}

        for member in soup.find_all('div', class_='team-member'):
            try:
                name = member.find('h3').text.strip()
                title = member.find('p').text.strip()
                profile_link = member.find('a')['href']
                profile_soup = self.fetch_soup(profile_link)
                article = profile_soup.find('article', class_='uk-article')
                desc = article.get_text(strip=True) if article else "No description"
                team_details[name] = {
                    'title': title,
                    'description': desc
                }
            except Exception as e:
                print(f"Error processing team member: {e}")
        return team_details

def main():
    scraper = NexyanScraper()
    
    print("Fetching service information...")
    services = scraper.get_services()
    with open("services.txt", "w", encoding='utf-8') as f:
        for name, content in services.items():
            f.write(f"=== {name} ===\n{content}\n\n")
    
    print("Fetching team information...")
    team = scraper.get_team_details()
    with open("team_details.txt", "w", encoding='utf-8') as f:
        for name, details in team.items():
            f.write(f"=== {name} ({details['title']}) ===\n{details['description']}\n\n")
    
    print("✅ Data has been saved to 'services.txt' and 'team_details.txt'.")

if __name__ == "__main__":
    main()
