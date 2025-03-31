import requests
from bs4 import BeautifulSoup
import trafilatura
import time
import os
import urllib.parse

# Cache to avoid repeated requests
web_cache = {}

def get_company_info_from_web(company_name, domain=None):
    """
    Get information about a company from web sources.
    Uses multiple strategies:
    1. If domain is provided, scrape company website
    2. Search for company information using search engines
    """
    if not company_name:
        return ""
    
    # Generate cache key
    cache_key = f"{company_name}_{domain}"
    if cache_key in web_cache:
        return web_cache[cache_key]
    
    combined_info = ""
    
    # Strategy 1: If domain is provided, try to scrape company website
    if domain and not company_name.lower() == domain.lower():
        try:
            website_info = scrape_company_website(domain)
            if website_info:
                combined_info += website_info + "\n\n"
        except Exception as e:
            print(f"Error scraping company website: {e}")
    
    # Strategy 2: Search for company information
    try:
        search_results = search_for_company(company_name)
        if search_results:
            combined_info += search_results
    except Exception as e:
        print(f"Error searching for company: {e}")
    
    # Cache the result
    web_cache[cache_key] = combined_info
    return combined_info

def scrape_company_website(domain):
    """Scrape the company website for relevant information"""
    if not domain:
        return ""
    
    # Ensure domain has http/https
    if not domain.startswith('http'):
        url = f"https://{domain}"
    else:
        url = domain
    
    try:
        # Use trafilatura to extract clean text from website
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            
            # If trafilatura failed to extract text, try BeautifulSoup
            if not text:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text from about, contact, team pages
                text = ""
                
                # Get main content
                for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
                    text += tag.get_text() + "\n"
            
            return text
        
        return ""
    
    except Exception as e:
        print(f"Error scraping website {domain}: {str(e)}")
        return ""

def search_for_company(company_name):
    """Search for company information using search engines or APIs"""
    # Check if SERPAPI_KEY is available
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    if serpapi_key:
        return search_using_serpapi(company_name, serpapi_key)
    else:
        return search_using_duckduckgo(company_name)

def search_using_serpapi(company_name, api_key):
    """Search for company using SerpAPI"""
    try:
        # Encode the company name for URL
        encoded_query = urllib.parse.quote(company_name)
        
        # Build the API URL
        url = f"https://serpapi.com/search.json?q={encoded_query}&api_key={api_key}"
        
        # Make the request
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Extract organic results
        if 'organic_results' in data:
            combined_text = ""
            
            # Get information from top 3 results
            for i, result in enumerate(data['organic_results'][:3]):
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                combined_text += f"{title}\n{snippet}\n{link}\n\n"
            
            # If knowledge graph is available
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                for key, value in kg.items():
                    if isinstance(value, str):
                        combined_text += f"{key}: {value}\n"
            
            return combined_text
        
        return ""
    
    except Exception as e:
        print(f"Error using SerpAPI: {str(e)}")
        return ""

def search_using_duckduckgo(company_name):
    """Search for company using DuckDuckGo (as a fallback)"""
    try:
        # Create a clean search query
        query = f"{company_name} company information"
        encoded_query = urllib.parse.quote(query)
        
        # Use DuckDuckGo HTML
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        # Add headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results
        results = soup.find_all('div', {'class': 'result__body'})
        
        combined_text = ""
        
        # Get information from top 3 results
        for i, result in enumerate(results[:3]):
            # Get the title
            title_elem = result.find('a', {'class': 'result__a'})
            title = title_elem.get_text() if title_elem else "No title"
            
            # Get the snippet
            snippet_elem = result.find('a', {'class': 'result__snippet'})
            snippet = snippet_elem.get_text() if snippet_elem else "No snippet"
            
            combined_text += f"{title}\n{snippet}\n\n"
        
        return combined_text
    
    except Exception as e:
        print(f"Error using DuckDuckGo: {str(e)}")
        return ""
