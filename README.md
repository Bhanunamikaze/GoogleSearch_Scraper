# Google Search & Content Scraper

A powerful, production-ready web scraper that searches Google and extracts full content from search results. Built with Playwright for robust browser automation and designed with anti-detection measures for reliable scraping.

## 🚀 Features

- **Google Search Automation**: Automatically searches Google with any query
- **Full Content Extraction**: Scrapes complete webpage content from search results
- **Anti-Detection**: Built-in stealth measures to avoid bot detection
- **Concurrent Processing**: Configurable concurrent page processing for efficiency
- **Multiple Output Formats**: Saves both detailed and summary JSON results
- **Robust Error Handling**: Comprehensive error handling and logging
- **Debug Mode**: Screenshots and HTML dumps for troubleshooting
- **Human-like Behavior**: Random delays and realistic browsing patterns
- **Flexible Selectors**: Multiple fallback selectors for different Google layouts

## 📋 Requirements

- Python 3.7+
- Playwright
- BeautifulSoup4
- aiofiles

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/Bhanunamikaze/GoogleSearch_Scraper.git
cd GoogleSearch_Scraper
```

2. **Install Python dependencies**
```bash
pip install playwright beautifulsoup4 aiofiles
```

3. **Install Playwright browsers**
```bash
playwright install chromium
```

## 🎯 Usage

### Basic Usage

```bash
python Google_Search.py "your search query"
```

### Advanced Usage with Options

```bash
python Google_Search.py "machine learning tutorials" \
  --max-results 20 \
  --headless \
  --concurrent 5 \
  --output-dir ./results \
  --debug
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `query` | Search query (required) | - |
| `--max-results` | Maximum number of results to process | 10 |
| `--headless` | Run browser in headless mode | False |
| `--debug` | Enable debug mode with screenshots | False |
| `--concurrent` | Maximum concurrent pages | 3 |
| `--output-dir` | Output directory for results | `scraped_data` |
| `--delay-min` | Minimum delay between actions (seconds) | 2.0 |
| `--delay-max` | Maximum delay between actions (seconds) | 5.0 |
| `--timeout` | Page timeout in milliseconds | 30000 |

## 📊 Output Format

The scraper generates two types of JSON files:

### Detailed Results (`*_detailed.json`)
Contains complete information for each scraped page:

```json
{
  "position": 1,
  "title": "Page Title",
  "url": "https://example.com",
  "snippet": "Search result snippet",
  "domain": "example.com",
  "search_query": "your query",
  "content": "Full HTML content",
  "text_content": "Clean text content",
  "meta_description": "Page meta description",
  "headings": [
    {"level": "h1", "text": "Main Heading"},
    {"level": "h2", "text": "Sub Heading"}
  ],
  "word_count": 1250,
  "reading_time": 6,
  "status_code": 200,
  "scraped_at": "2024-01-01T12:00:00"
}
```

### Summary Results (`*_summary.json`)
Contains condensed information for quick overview:

```json
{
  "position": 1,
  "title": "Page Title",
  "url": "https://example.com",
  "domain": "example.com",
  "snippet": "Search result snippet",
  "word_count": 1250,
  "reading_time": 6,
  "headings_count": 8,
  "has_error": false,
  "status_code": 200
}
```

## 🔧 Configuration

### Browser Settings
The scraper uses Chromium with optimized settings for stealth and performance:
- Disabled automation indicators
- Realistic viewport size (1920x1080)
- Rotating user agents
- US locale and timezone

### Anti-Detection Measures
- Random delays between actions
- Human-like browsing patterns
- Stealth browser configuration
- User agent rotation
- JavaScript execution context hiding

## 📁 File Structure

```
scraped_data/
├── logs/
│   └── scraper_20240101_120000.log
├── query_name_20240101_120000_detailed.json
├── query_name_20240101_120000_summary.json
└── debug_*.png (if debug mode enabled)
```

## 🐛 Debug Mode

Enable debug mode to troubleshoot issues:

```bash
python Google_Search.py "test query" --debug
```

Debug mode provides:
- Screenshots at each major step
- HTML dumps of page content
- Detailed logging output
- Error state captures

## ⚠️ Important Notes

### Legal and Ethical Considerations
- **Respect robots.txt**: Check website policies before scraping
- **Rate limiting**: Use appropriate delays to avoid overwhelming servers
- **Terms of Service**: Ensure compliance with Google's ToS and target websites
- **Personal use**: This tool is intended for research and personal use

### Best Practices
- Use reasonable delays between requests
- Don't run multiple instances simultaneously
- Monitor your IP for any rate limiting
- Respect website resources and bandwidth

## 🔍 Troubleshooting

### Common Issues

**No search results found**
- Enable debug mode to see screenshots
- Check if Google is blocking the request
- Verify your internet connection
- Try a different search query

**Browser crashes or timeouts**
- Reduce concurrent pages (`--concurrent 1`)
- Increase timeout value (`--timeout 60000`)
- Run in non-headless mode for debugging

**Content extraction failures**
- Check the debug HTML files
- Website may have anti-scraping measures
- Try reducing the number of concurrent requests

### Log Files
Check the log files in `scraped_data/logs/` for detailed error information and debugging hints.



## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Disclaimer

This tool is for educational and research purposes only. Users are responsible for ensuring their use complies with applicable laws, terms of service, and ethical guidelines. The authors are not responsible for any misuse of this software.

**Note**: Always ensure you have permission to scrape websites and comply with their robots.txt files and terms of service. Use this tool responsibly and ethically.
