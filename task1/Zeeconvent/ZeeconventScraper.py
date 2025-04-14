import requests
from bs4 import BeautifulSoup
import re
import time
import json

class ZeeconventScraper:
    def __init__(self, url='https://www.zeeconvent.be', cache=True):
        """
        Initializes the scraper with the given URL and fetches the BeautifulSoup object for parsing.

        Args:
            url (str): The website URL to scrape.
            cache (bool): Whether to use cached HTML or fetch anew.
        """
        self.url = url
        self.headers = {"Accept-Language": "en"}
        self.soup = self._get_soup(cache=cache)

    def _get_soup(self, cache=True):
        """
        Makes a GET request to the website and returns the parsed HTML content using BeautifulSoup.

        Args:
            cache (bool): Whether to load from cache or fetch from the web.

        Returns:
            BeautifulSoup: Parsed HTML content.
        """
        if cache:
            try:
                with open('cached_page.html', 'r', encoding='utf-8') as file:
                    return BeautifulSoup(file.read(), 'html.parser')
            except FileNotFoundError:
                pass  # fall through to fetching and caching below

        response = requests.get(self.url, headers=self.headers)
        with open('cached_page.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
        return BeautifulSoup(response.text, 'html.parser')


    def extract_media_sections(self):
        """
        Extracts media sections including titles, subtitles, text content, image URLs, and detail links.
        """
        media_sections = []
        for section in self.soup.find_all('div', class_='s-new-media-section'):
            title = section.find('div', class_='s-title')
            subtitle = section.find('div', class_='s-subtitle')
            title_text = title.get_text(strip=True) if title else ''
            subtitle_text = subtitle.get_text(strip=True) if subtitle else ''

            items = []
            for item in section.find_all('div', class_='s-repeatable-item'):
                item_title = item.find('div', class_='s-item-title')
                item_subtitle = item.find('div', class_='s-item-subtitle')
                item_text = item.find('div', class_='s-item-text')
                item_img = item.find('img')
                item_details = item.find('a', class_='s-common-button')

                items.append({
                    'title': item_title.get_text(strip=True) if item_title else '',
                    'subtitle': item_subtitle.get_text(strip=True) if item_subtitle else '',
                    'text': item_text.get_text(strip=True) if item_text else '',
                    'image_url': f"https:{item_img['src']}" if item_img else '',
                    'details_url': item_details['href'] if item_details else ''
                })

            media_sections.append({
                'section_title': title_text,
                'section_subtitle': subtitle_text,
                'items': items
            })
        return media_sections

    def extract_gallery_section(self):
        """
        Extracts the gallery section including image URLs, titles, and subtitles.
        """
        galleries = []
        for section in self.soup.find_all('div', 's-gallery-section'):
            title = section.find('h2', class_='s-title')
            subtitle = section.find('h4', class_='s-subtitle')
            images = [f"https:{img['src']}" for img in section.find_all('img')]

            galleries.append({
                'title': title.get_text(strip=True) if title else '',
                'subtitle': subtitle.get_text(strip=True) if subtitle else '',
                'images': images
            })
        return galleries

    def extract_slide_section(self):
        """
        Extracts a slide section's title and subtitle.
        """
        section = self.soup.find('li', class_='s-section-2')
        title = section.find('div', class_='s-title').get_text(strip=True)
        subtitle = section.find('div', class_='s-section-item-wrapper').get_text(strip=True)
        return {'title': title, 'subtitle': subtitle}

    def extract_day_trips(self):
        """
        Extracts nearby day trips including place name, distance, and estimated travel time.
        """
        section = self.soup.find('li', class_='s-section-8')
        title = section.find('div', class_='s-item-title').get_text(strip=True)
        subtitle = section.find('b').get_text(strip=True)
        trips = []
        for li in section.find_all('li'):
            match = re.match(r'(.+?)\s+([\d,]+km)\s+(\d+min)', li.get_text(strip=True))
            if match:
                place, distance, time = match.groups()
                trips.append({
                    'place': place,
                    'distance(km)': distance.replace(',', '')[:-2],
                    'time(min)': time[:-3]
                })
        return {'title': title, 'subtitle': subtitle, 'trips': trips}

    def extract_rental_prices(self):
        """
        Extracts seasonal rental prices with durations and corresponding costs.
        """
        rental_section = self.soup.find('li', class_='s-section-10')
        title = rental_section.find('div', class_='s-title').get_text(strip=True)

        season_data = {}
        blocks = rental_section.find_all('div', class_='s-block-title')[:3]
        rows = rental_section.find_all('div', class_='s-block-rowBlock')[1:]

        for block, row in zip(blocks, rows):
            season_text = block.find('h3').get_text(strip=True)
            season_match = re.match(r'^(\w+)', season_text)
            date_parts = re.findall(r'\(([^)]+)\)', season_text)
            season = season_match.group(1) if season_match else None
            date_description = " ".join(date_parts)

            row_text = "  ".join([p.get_text(strip=True) for p in row.find_all('p')])
            pattern = r"((?:\d+\s+)?(?:[A-Za-z]+\s*)+(?:\(\d+\s*nachten\))?)\s*\u20ac(\d+)"
            matches = re.findall(pattern, row_text)

            prices = {duration.strip(): f"\u20ac{price}" for duration, price in matches}

            if season:
                season_data[season] = {
                    'date_info': date_description,
                    'prices': prices
                }

        return season_data

    def extract_contact_info(self):
        """
        Extracts contact details like address, phone number, and email.
        """
        section = self.soup.find('li', class_='s-section-12')
        inner = section.find('div', class_='s-block-item-inner')
        p_tags = [p.get_text(strip=True) for p in inner.find_all('p')]
        contact = {
            p_tags[0][:-1]: p_tags[1],
            p_tags[3][:-1]: p_tags[4],
            p_tags[6][:-1]: " ".join(p_tags[7:10])
        }
        return contact

    def extract_practical_info(self):
        """
        Extracts practical information as a dictionary of headings and their content.
        """
        section = self.soup.find('li', class_='s-section-11')
        info = {}
        for div in section.find_all('div', class_='rich-text'):
            ps = div.find_all('p')
            if ps:
                title = ps[0].get_text(strip=True)
                content = " ".join([p.get_text(strip=True) for p in ps[1:]])
                info[title] = content
        return info


def main():

    start_time = time.time()

    scraper = ZeeconventScraper(cache=True)

    results = {
        "Media Sections": scraper.extract_media_sections(),
        "Gallery Section": scraper.extract_gallery_section(),
        "Slide Section": scraper.extract_slide_section(),
        "Day Trips": scraper.extract_day_trips(),
        "Rental Prices": scraper.extract_rental_prices(),
        "Practical Info": scraper.extract_practical_info(),
        "Contact Info": scraper.extract_contact_info(),
    }

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Save to .txt file
    with open("zeeconvent_scraped_data.txt", "w", encoding='utf-8') as file:
        file.write("Zeeconvent  Data\n")
        file.write("=" * 50 + "\n\n")
        for section, content in results.items():
            file.write(f"## {section} ##\n")
            file.write(json.dumps(content, indent=2, ensure_ascii=False))
            file.write("\n\n")
        file.write(f"Total Time Taken: {elapsed_time:.2f} seconds\n")

    print(f"✅ Scraping complete! Data saved to 'scraped_data.txt' in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()

