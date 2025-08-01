import asyncio
import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, urljoin
import argparse
import sys

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import aiofiles

class GoogleSearchScraper:
    def __init__(self, 
                 headless: bool = True,
                 max_concurrent_pages: int = 3,
                 delay_range: tuple = (2, 5),
                 timeout: int = 30000,
                 output_dir: str = "scraped_data",
                 debug: bool = False):
        
        self.headless = headless
        self.max_concurrent_pages = max_concurrent_pages
        self.delay_range = delay_range
        self.timeout = timeout
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.debug = debug
        
        # Setup logging
        self.setup_logging()
        
        # Browser and context
        self.browser = None
        self.context = None
        
        # Semaphore for concurrent control
        self.semaphore = asyncio.Semaphore(max_concurrent_pages)
        
        # User agents rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.output_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"scraper_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.DEBUG if self.debug else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def setup_browser(self):
        """Initialize browser with anti-detection measures"""
        self.logger.info("Setting up browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-javascript-harmony-shipping',
                '--disable-wake-on-wifi',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--window-size=1920,1080'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(self.user_agents),
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add stealth script
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        self.logger.info("Browser setup completed")
    
    async def debug_page_content(self, page: Page, step: str):
        """Debug helper to capture page content"""
        if self.debug:
            timestamp = datetime.now().strftime("%H%M%S")
            screenshot_path = self.output_dir / f"debug_{step}_{timestamp}.png"
            html_path = self.output_dir / f"debug_{step}_{timestamp}.html"
            
            await page.screenshot(path=screenshot_path)
            content = await page.content()
            
            async with aiofiles.open(html_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.logger.debug(f"Debug files saved: {screenshot_path}, {html_path}")
    
    async def human_like_delay(self):
        """Add human-like delays"""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
    
    async def search_google(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Google and extract search results with improved selectors"""
        page = await self.context.new_page()
        results = []
        
        try:
            self.logger.info(f"Searching Google for: '{query}'")
            
            # Navigate to Google search directly
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            await page.goto(search_url, wait_until='networkidle', timeout=self.timeout)
            
            if self.debug:
                await self.debug_page_content(page, "after_navigation")
            
            await self.human_like_delay()
            
            # Handle cookie consent with multiple selectors
            try:
                consent_selectors = [
                    "button:has-text('Accept all')",
                    "button:has-text('I agree')", 
                    "button:has-text('Accept')",
                    "[aria-label*='Accept']",
                    "#L2AGLb",  # Google's accept button ID
                    ".QS5gu"   # Another possible accept button class
                ]
                
                for selector in consent_selectors:
                    consent_button = page.locator(selector)
                    if await consent_button.count() > 0:
                        await consent_button.first.click()
                        await self.human_like_delay()
                        self.logger.info("Clicked consent button")
                        break
                        
            except Exception as e:
                self.logger.debug(f"No consent dialog found or error clicking: {e}")
            
            if self.debug:
                await self.debug_page_content(page, "after_consent")
            
            # Wait for search results with multiple possible selectors
            result_selectors = [
                '#search',           # Main search container
                '#rso',              # Results container
                '.g',                # Individual result
                '[data-header-feature]',  # Alternative container
                '.MjjYud',           # New Google result class
                '.hlcw0c'            # Another possible class
            ]
            
            search_container = None
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    search_container = selector
                    self.logger.info(f"Found search results with selector: {selector}")
                    break
                except:
                    continue
            
            if not search_container:
                self.logger.error("Could not find search results container")
                if self.debug:
                    await self.debug_page_content(page, "no_results_found")
                return results
            
            await self.human_like_delay()
            
            # Extract search results with multiple selector strategies
            search_result_selectors = [
                '.g',                    # Traditional Google result
                '.MjjYud',               # Newer Google result class
                '[data-sokoban-container] .g',  # Alternative path
                '.hlcw0c',               # Another class
                '[jscontroller] .g'      # JS controller based
            ]
            
            search_results = []
            for selector in search_result_selectors:
                search_results = await page.locator(selector).all()
                if search_results:
                    self.logger.info(f"Found {len(search_results)} results with selector: {selector}")
                    break
            
            if not search_results:
                self.logger.warning("No search results found with any selector")
                if self.debug:
                    await self.debug_page_content(page, "no_individual_results")
                return results
            
            # Process each result
            for i, result in enumerate(search_results[:max_results]):
                try:
                    # Extract title with multiple selectors
                    title = ""
                    title_selectors = ['h3', 'h2', '.LC20lb', '.DKV0Md']
                    for title_sel in title_selectors:
                        title_element = result.locator(title_sel)
                        if await title_element.count() > 0:
                            title = await title_element.first.text_content()
                            if title and title.strip():
                                break
                    
                    # Extract URL with multiple selectors
                    url = ""
                    link_selectors = ['a[href]', '[href]']
                    for link_sel in link_selectors:
                        link_element = result.locator(link_sel)
                        if await link_element.count() > 0:
                            url = await link_element.first.get_attribute('href')
                            if url and url.startswith('http'):
                                break
                    
                    # Extract snippet with multiple selectors
                    snippet = ""
                    snippet_selectors = ['.VwiC3b', '.s3v9rd', '.st', '[data-sncf="1"]', '.IsZvec', '.aCOpRe']
                    for snippet_sel in snippet_selectors:
                        snippet_element = result.locator(snippet_sel)
                        if await snippet_element.count() > 0:
                            snippet = await snippet_element.first.text_content()
                            if snippet and snippet.strip():
                                break
                    
                    # Validate and clean data
                    if not title or not url or not url.startswith('http'):
                        self.logger.debug(f"Skipping result {i+1}: incomplete data")
                        continue
                    
                    # Skip Google's own results and ads
                    if any(domain in url for domain in ['google.com', 'youtube.com/results', 'googleadservices']):
                        continue
                    
                    results.append({
                        'position': len(results) + 1,
                        'title': title.strip(),
                        'url': url,
                        'snippet': snippet.strip() if snippet else "No description available",
                        'domain': urlparse(url).netloc,
                        'search_query': query
                    })
                    
                    self.logger.info(f"Found result {len(results)}: {title.strip()[:50]}...")
                
                except Exception as e:
                    self.logger.warning(f"Error extracting result {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(results)} search results")
            
        except Exception as e:
            self.logger.error(f"Error during Google search: {e}")
            if self.debug:
                await self.debug_page_content(page, "error_state")
        finally:
            await page.close()
        
        return results
    
    async def extract_page_content(self, url: str, title: str) -> Dict[str, Any]:
        """Extract content from a single webpage"""
        async with self.semaphore:
            page = await self.context.new_page()
            content_data = {
                'url': url,
                'title': title,
                'content': '',
                'text_content': '',
                'meta_description': '',
                'headings': [],
                'links': [],
                'images': [],
                'status_code': None,
                'error': None,
                'scraped_at': datetime.now().isoformat(),
                'word_count': 0,
                'reading_time': 0
            }
            
            try:
                self.logger.info(f"Extracting content from: {url}")
                
                # Navigate to page with better error handling
                try:
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    content_data['status_code'] = response.status if response else None
                    
                    if response and response.status >= 400:
                        content_data['error'] = f"HTTP {response.status}"
                        return content_data
                        
                except Exception as nav_error:
                    content_data['error'] = f"Navigation failed: {nav_error}"
                    return content_data
                
                await self.human_like_delay()
                
                # Wait for content to load
                try:
                    await page.wait_for_load_state('networkidle', timeout=15000)
                except:
                    pass  # Continue even if networkidle times out
                
                # Extract text content
                text_content = await page.evaluate("""
                    () => {
                        // Remove unwanted elements
                        const unwanted = document.querySelectorAll('script, style, nav, header, footer, aside, .ads, .advertisement');
                        unwanted.forEach(el => el.remove());
                        
                        // Try to find main content
                        const selectors = ['main', 'article', '.content', '.post', '.article-body', '.entry-content', '.post-content'];
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.length > 200) {
                                return element.innerText;
                            }
                        }
                        
                        // Fallback to body
                        return document.body.innerText || '';
                    }
                """)
                
                content_data['text_content'] = text_content.strip() if text_content else ''
                
                # Calculate metrics
                if content_data['text_content']:
                    words = len(content_data['text_content'].split())
                    content_data['word_count'] = words
                    content_data['reading_time'] = max(1, words // 200)
                
                # Extract meta description
                try:
                    meta_desc = await page.locator('meta[name="description"]').get_attribute('content')
                    content_data['meta_description'] = meta_desc or ''
                except:
                    pass
                
                # Extract headings
                try:
                    headings = await page.locator('h1, h2, h3, h4, h5, h6').all()
                    for heading in headings[:20]:  # Limit headings
                        try:
                            tag_name = await heading.evaluate('el => el.tagName.toLowerCase()')
                            text = await heading.text_content()
                            if text and text.strip():
                                content_data['headings'].append({
                                    'level': tag_name,
                                    'text': text.strip()[:200]  # Limit text length
                                })
                        except:
                            continue
                except:
                    pass
                
                self.logger.info(f"Successfully extracted content from {url} ({content_data['word_count']} words)")
                
            except Exception as e:
                error_msg = f"Error extracting content from {url}: {e}"
                self.logger.warning(error_msg)
                content_data['error'] = error_msg
                
            finally:
                await page.close()
            
            return content_data
    
    async def scrape_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract content from all search results concurrently"""
        if not search_results:
            self.logger.warning("No search results to scrape")
            return []
            
        self.logger.info(f"Starting content extraction for {len(search_results)} URLs...")
        
        tasks = []
        for result in search_results:
            task = self.extract_page_content(result['url'], result['title'])
            tasks.append(task)
        
        # Execute with controlled concurrency
        content_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        combined_results = []
        for i, (search_result, content_result) in enumerate(zip(search_results, content_results)):
            if isinstance(content_result, Exception):
                self.logger.error(f"Failed to extract content for {search_result['url']}: {content_result}")
                content_result = {
                    'url': search_result['url'],
                    'title': search_result['title'],
                    'error': str(content_result),
                    'scraped_at': datetime.now().isoformat()
                }
            
            # Combine search result with content
            combined_result = {**search_result, **content_result}
            combined_results.append(combined_result)
        
        return combined_results
    
    async def save_results(self, results: List[Dict[str, Any]], query: str):
        """Save results to multiple formats"""
        if not results:
            self.logger.warning("No results to save")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')
        
        # Save detailed JSON
        json_file = self.output_dir / f"{safe_query}_{timestamp}_detailed.json"
        async with aiofiles.open(json_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Save summary JSON
        summary_results = []
        for result in results:
            summary_results.append({
                'position': result.get('position'),
                'title': result.get('title'),
                'url': result.get('url'),
                'domain': result.get('domain'),
                'snippet': result.get('snippet'),
                'word_count': result.get('word_count', 0),
                'reading_time': result.get('reading_time', 0),
                'headings_count': len(result.get('headings', [])),
                'has_error': bool(result.get('error')),
                'status_code': result.get('status_code')
            })
        
        summary_file = self.output_dir / f"{safe_query}_{timestamp}_summary.json"
        async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary_results, indent=2, ensure_ascii=False))
        
        self.logger.info(f"Results saved to {json_file}")
        self.logger.info(f"Summary saved to {summary_file}")
    
    async def run_search_and_scrape(self, query: str, max_results: int = 10):
        """Main method to run the complete search and scrape process"""
        try:
            await self.setup_browser()
            
            # Step 1: Search Google
            search_results = await self.search_google(query, max_results)
            
            if not search_results:
                self.logger.warning("No search results found - check debug files if debug mode enabled")
                return
            
            # Step 2: Extract content from all results
            detailed_results = await self.scrape_search_results(search_results)
            
            # Step 3: Save results
            await self.save_results(detailed_results, query)
            
            # Print summary
            successful = sum(1 for r in detailed_results if not r.get('error'))
            total_words = sum(r.get('word_count', 0) for r in detailed_results)
            
            self.logger.info(f"\n=== SCRAPING COMPLETED ===")
            self.logger.info(f"Query: {query}")
            self.logger.info(f"Total results: {len(detailed_results)}")
            self.logger.info(f"Successful extractions: {successful}")
            self.logger.info(f"Total words extracted: {total_words:,}")
            self.logger.info(f"Output directory: {self.output_dir}")
            
        except Exception as e:
            self.logger.error(f"Critical error in main process: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.logger.info("Browser cleanup completed")

async def main():
    parser = argparse.ArgumentParser(description='Production Google Search & Content Scraper')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of results to process')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with screenshots')
    parser.add_argument('--concurrent', type=int, default=3, help='Max concurrent pages')
    parser.add_argument('--output-dir', default='scraped_data', help='Output directory')
    parser.add_argument('--delay-min', type=float, default=2.0, help='Minimum delay between actions')
    parser.add_argument('--delay-max', type=float, default=5.0, help='Maximum delay between actions')
    parser.add_argument('--timeout', type=int, default=30000, help='Page timeout in milliseconds')
    
    args = parser.parse_args()
    
    scraper = GoogleSearchScraper(
        headless=args.headless,
        max_concurrent_pages=args.concurrent,
        delay_range=(args.delay_min, args.delay_max),
        output_dir=args.output_dir,
        timeout=args.timeout,
        debug=args.debug
    )
    
    await scraper.run_search_and_scrape(args.query, args.max_results)

if __name__ == "__main__":
    asyncio.run(main())
