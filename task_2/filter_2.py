import asyncio
import re
from collections import defaultdict
from crawl4ai import AsyncWebCrawler
import google.generativeai as genai
import tldextract

# Function to initialize Google GenAI
def initialize_genai():
    """Initialize Google GenAI"""
    apikey = 'AIzaSyCMfQV4VkjxA3hMItXgVIZwPpnIL7mJrDw'  
    genai.configure(api_key=apikey)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

# Function to crawl the website and save the markdown and HTML
async def crawl_website(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        with open("C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/output.md", "w", encoding='utf-8') as f:
            f.write(result.markdown)
        with open("C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/output.html", "w", encoding='utf-8') as f:
            f.write(result.cleaned_html)
        print("Markdown content saved to output.md")
        print("Clean HTML content saved to output.html")

# Function to extract unique links from the markdown file
def extract_links(input_file_path, output_file_path,url):
    ext = tldextract.extract(url)
    link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
    url_dict = defaultdict(list)

    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    matches = link_pattern.findall(content)

    for text, url in matches:
        if '#' in url:
            continue
        if re.search(r'\.(pdf|jpg|jpeg|png|gif|svg|mp4|xlsx|docx|zip)$', url, re.IGNORECASE):
            continue
        if ext.domain in url:
            url_dict[url].append(text)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for url, texts in url_dict.items():
            unique_texts = list(dict.fromkeys(texts))  # Remove duplicates while preserving order
            combined_text = ', '.join(unique_texts)
            file.write(f"{combined_text}: {url}\n")

    print(f"Extracted unique links with combined text saved to: {output_file_path}")

# Function to generate answers using Google GenAI
def predict_urls(url, question, file_path):
    model = initialize_genai()
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()

    final_prompt = f"""
    TASK: URL RELEVANCE ANALYSIS

    BASE WEBSITE: {url}
    INFORMATION NEED: {question}

    INSTRUCTIONS:
    - Analyze the provided URLs and keywords below
    - Identify the most relevant URLs that likely contain the requested information
    - Consider keyword matches, semantic relevance, and URL path structure
    - Return ONLY the top URLs with their relevance scores
    - At least 3 URLs should be returned

    AVAILABLE DATA:
    {data}

    OUTPUT REQUIREMENTS:
    - Format: JSON only
    - Include only URLs from the provided data
    - Score each URL on relevance (1-10 scale)
    - Higher scores indicate higher relevance
    - Example format:
    [
        {{"url": "example.com/page1", "score": 9}},
        {{"url": "example.com/page2", "score": 7}}
    ]
    """
    try:
        model_response = model.generate_content(final_prompt)
        response = model_response.text
        # Regular expression to find URLs and scores
        pattern = r'\{\s*"url":\s*"([^"]+)",\s*"score":\s*(\d+)\s*\}'

        # Find all matches in the string
        matches = re.findall(pattern, response)

        # Convert matches to a list of dictionaries
        data = [{'url': url, 'score': int(score)} for url, score in matches]
        print(data)
        return data

    except Exception as e:
        return f"Error generating answer: {str(e)}"

async def main():
    # Read from the response file for second filtering
    with open("C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/response.txt", "r", encoding='utf-8') as f:
        final_urls = []
        for line in f:
            url, score = line.strip().split(',')
            print(f"URL: {url}, Score: {score}")
            try:
                await crawl_website(url)  # Step 4: Crawl the URLs with high scores
                extract_links("C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/output.md", 
                              "C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/extracted_deep_links.txt", url)
                filtered_response = predict_urls(url, "only types of business", 
                                                  "C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/extracted_deep_links.txt")
                
                # Ensure filtered_response is a list of dictionaries
                if isinstance(filtered_response, list):
                    final_urls.extend(filtered_response)  # Append the new URLs to final_urls
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error crawling {url}: {e}")

    # Write final URLs to a file after processing all URLs
    with open("C:/Users/TumpudiKarthikeya/Desktop/pro/task_2/final_urls.txt", "w", encoding='utf-8') as f:
        for item in final_urls:
            f.write(f"{item['url']},{item['score']}\n")

    print("=>>>>Final URLs:", final_urls)

# Run the async main function
asyncio.run(main())