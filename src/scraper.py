import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
import os
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any
import feedparser
from urllib.parse import quote_plus

# Optional imports for JavaScript rendering
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available - JavaScript scraping disabled. Install with: pip install playwright")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self, sources_file: str = "sources.json"):
        with open(sources_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.sources = [s for s in self.config['sources'] if s.get('enabled', True)]

        self.auto_fix_feeds = os.getenv('MMM_AUTO_FIX_FEEDS', '1').strip().lower() not in {'0', 'false', 'no'}
        self.feed_cache_path = os.getenv('MMM_FEED_URL_CACHE', 'feed_url_cache.json')
        self.feed_url_cache: Dict[str, Dict[str, Any]] = self._load_feed_url_cache(self.feed_cache_path)
        self.require_article_content = os.getenv('MMM_REQUIRE_ARTICLE_CONTENT', '0').strip().lower() in {'1', 'true', 'yes'}
        self.thin_ratio_threshold = float(os.getenv('MMM_THIN_RATIO_THRESHOLD', '0.35') or 0.35)
        self.thin_ratio_auto_strict = os.getenv('MMM_THIN_AUTO_STRICT', '0').strip().lower() in {'1', 'true', 'yes'}
        self.thin_ratio_min_items = int(os.getenv('MMM_THIN_RATIO_MIN_ITEMS', '6') or 6)

        # Apply cached URLs first (best-effort)
        for source in self.sources:
            cached = self.feed_url_cache.get(source.get('name', ''))
            if cached and isinstance(cached, dict) and cached.get('url'):
                source.setdefault('original_url', source.get('url'))
                source['url'] = cached['url']

    @staticmethod
    def _looks_like_html(text: str) -> bool:
        if not text:
            return False
        head = text.lstrip()[:500].lower()
        return '<html' in head or '<!doctype html' in head

    @staticmethod
    def _derive_homepage_url(url: str) -> str:
        """Derive a reasonable homepage URL from any source URL."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return url
            return f"{parsed.scheme}://{parsed.netloc}/"
        except Exception:
            return url

    @staticmethod
    def _extract_candidate_feed_urls(base_url: str, html: str) -> List[str]:
        """Extract likely RSS/Atom URLs from an HTML document."""
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        found: set[str] = set()

        # <link rel="alternate" type="application/rss+xml" href="...">
        for link in soup.find_all('link'):
            href = link.get('href')
            if not href:
                continue
            rel = link.get('rel') or []
            rel = [str(x).lower() for x in rel]
            typ = (link.get('type') or '').lower()
            if 'alternate' in rel and any(x in typ for x in ['rss', 'atom', 'xml']):
                found.add(urljoin(base_url, href))

        # Anchors
        for a in soup.find_all('a'):
            href = a.get('href')
            if not href:
                continue
            href_l = href.lower()
            if any(k in href_l for k in ['rss', 'feed', 'atom', '.xml', '.rss']):
                found.add(urljoin(base_url, href))

        # Regex sweep (some sites embed feed URLs in scripts)
        for m in re.finditer(r"https?://[^\s\"'>]+", html):
            u = m.group(0)
            ul = u.lower()
            if any(k in ul for k in ['rss', 'feed', 'atom', '.xml', '.rss']):
                found.add(u.split('#')[0])

        # De-dup + stable order
        return sorted(found)

    @staticmethod
    def _load_feed_url_cache(path: str) -> Dict[str, Dict[str, Any]]:
        try:
            if not path or not os.path.exists(path):
                return {}
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_feed_url_cache(self) -> None:
        try:
            with open(self.feed_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.feed_url_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ Could not write feed URL cache {self.feed_cache_path}: {e}")

    async def _validate_rss_url(self, session: aiohttp.ClientSession, url: str, source_type: str | None) -> Dict[str, Any] | None:
        meta = await self.fetch_url_with_meta(session, url, source_type)
        text = meta.get('text', '')
        status = meta.get('status')
        if not text or (status and status >= 400) or self._looks_like_html(text):
            return None
        feed = feedparser.parse(text)
        if not feed.entries:
            return None
        return {
            'url': url,
            'feed_title': feed.feed.get('title'),
            'entries': len(feed.entries),
            'http_status': status,
            'content_type': meta.get('content_type', ''),
            'final_url': meta.get('final_url', url),
        }

    async def _autofix_rss_source_url(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> str | None:
        if not self.auto_fix_feeds:
            return None

        homepage = source.get('homepage') or self._derive_homepage_url(source.get('original_url') or source.get('url', ''))
        meta = await self.fetch_url_with_meta(session, homepage, source.get('type'))
        html = meta.get('text', '')
        if not html:
            return None

        candidates = self._extract_candidate_feed_urls(meta.get('final_url', homepage), html)
        # Prefer URLs that look most like feeds
        preferred = []
        others = []
        for c in candidates:
            cl = c.lower()
            if any(k in cl for k in ['/feed', '/rss', '.rss', 'rss', 'atom']):
                preferred.append(c)
            else:
                others.append(c)
        ordered = preferred + others

        for candidate in ordered[:15]:
            validated = await self._validate_rss_url(session, candidate, source.get('type'))
            if validated:
                return validated['url']
        return None

    async def fetch_url_with_meta(
        self,
        session: aiohttp.ClientSession,
        url: str,
        source_type: str = None
    ) -> Dict[str, Any]:
        """Fetch URL and return content plus HTTP metadata for better diagnostics."""
        # Use different user agents for different source types
        if source_type == 'weather' and 'wttr.in' in url:
            headers = {
                'User-Agent': 'curl/7.68.0'
            }
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.9, text/html;q=0.8, */*;q=0.7',
                'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7'
            }

        logger.info(f"🌐 Fetching {url} with User-Agent: {headers['User-Agent'][:50]}...")

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                content_type = response.headers.get('Content-Type', '')
                final_url = str(response.url)
                status = response.status

                try:
                    content = await response.text()
                except UnicodeDecodeError:
                    content = (await response.read()).decode('utf-8', errors='ignore')

                logger.info(f"✅ Fetched {len(content)} characters from {url} (HTTP {status}, {content_type})")
                logger.info(f"📝 Content preview: {content[:200]}...")

                return {
                    'text': content,
                    'status': status,
                    'content_type': content_type,
                    'final_url': final_url,
                    'error': None,
                }
        except Exception as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            return {
                'text': "",
                'status': None,
                'content_type': "",
                'final_url': url,
                'error': str(e),
            }
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str, source_type: str = None) -> str:
        meta = await self.fetch_url_with_meta(session, url, source_type)
        return meta.get('text', '')
    
    async def scrape_source(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"🔍 Scraping {source['name']} ({source['url']})...")
        
        # Check if this is an RSS feed
        url_lower = source['url'].lower()
        if (
            source.get('format') == 'rss'
            or url_lower.endswith('.rss')
            or '/rss' in url_lower
            or '/feed' in url_lower
            or 'lab_viewport=rss' in url_lower
            or 'viewport=rss' in url_lower
            or 'format=rss' in url_lower
        ):
            return await self.scrape_rss_source(session, source)
        else:
            return await self.scrape_html_source(session, source)
    
    async def fetch_article_content(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch full article content from URL"""
        try:
            content = await self.fetch_url(session, url, 'html')
            if not content:
                return ""
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script, style, nav, and comment form elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                element.decompose()
            
            # Also remove common comment/reply sections
            for element in soup.find_all(class_=['comment-form', 'comments', 'respond', 'comment-respond', 'reply']):
                element.decompose()
            
            # Common article content selectors (in priority order)
            article_selectors = [
                'article .entry-content',  # WordPress common
                'article .post-content',   # Blog common
                '.article-body',           # News sites
                '.story-body',             # BBC-style
                '.content-body',           # Generic
                'article',                 # Full article tag
                '.entry-content',          # WordPress
                '.post-content',           # Blogs
                '.article-content',        # News
                '.content',                # Generic
                'main article',            # Semantic HTML
                '.wp-block-post-content',  # WordPress blocks
                '.entry',                  # Generic blog
                '.post',                   # Generic blog
                'main'                     # Main content
            ]
            
            best_text = ""
            best_length = 0
            
            for selector in article_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements[:2]:  # Check first 2 matches
                        # Get text from this element
                        text = element.get_text(separator=' ', strip=True)
                        
                        # Clean up the text
                        text = ' '.join(text.split())  # Normalize whitespace
                        
                        # Skip if too short or looks like navigation/comments
                        if len(text) < 100:
                            continue
                        if any(skip_word in text[:100].lower() for skip_word in [
                            'menu', 'search', 'subscribe', 'lämna ett svar', 
                            'din e-postadress', 'obligatoriska fält', 'comment', 'reply'
                        ]):
                            continue
                        
                        # Keep the longest quality text found
                        if len(text) > best_length:
                            best_text = text
                            best_length = len(text)
                except:
                    continue
            
            if best_text:
                return best_text[:5000]  # Increased limit to 5000 chars for better content
            
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            if paragraphs:
                # Filter out short paragraphs and comment form text
                good_paragraphs = []
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    if len(p_text) > 30:
                        # Skip if it looks like comment form
                        if any(skip in p_text.lower() for skip in [
                            'din e-postadress', 'obligatoriska fält', 
                            'lämna ett svar', 'avbryt svar'
                        ]):
                            continue
                        good_paragraphs.append(p_text)
                
                if good_paragraphs:
                    text = ' '.join(good_paragraphs)
                    return text[:5000] if text else ""  # Increased limit for better content
            
            return ""
        except Exception as e:
            logger.debug(f"Could not fetch article content from {url}: {e}")
            return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove HTML tags if present and normalize whitespace
        if "<" in text and ">" in text:
            try:
                soup = BeautifulSoup(text, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
            except Exception:
                pass
        return " ".join(str(text).split())
    
    async def fetch_javascript_content(self, url: str, wait_for_selector: str = None) -> str:
        """Fetch content from pages that require JavaScript rendering"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available - cannot fetch JavaScript content")
            return ""
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Navigate to page
                logger.debug(f"🌐 Loading JavaScript page: {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=10000)
                        logger.debug(f"✅ Found selector: {wait_for_selector}")
                    except:
                        logger.debug(f"⚠️ Selector not found: {wait_for_selector}")
                else:
                    # Wait a bit for dynamic content to load
                    await page.wait_for_timeout(3000)
                
                # Click "See more" buttons to expand truncated Facebook posts
                logger.debug("🔍 Looking for 'See more' buttons to expand content...")
                # More comprehensive selectors for Facebook expand buttons
                see_more_selectors = [
                    # Facebook-specific selectors
                    '[role="button"][aria-label*="See more"]',
                    '[role="button"]:has-text("See More")',
                    '[role="button"]:has-text("See more")', 
                    '[role="button"]:has-text("Visa mer")',
                    '[role="button"]:has-text("Show more")',
                    # Generic expand selectors
                    '.see-more', '.show-more', '.expand-text', '.expand-link',
                    '[data-testid*="expand"]', '[aria-label*="expand"]',
                    # Text-based selectors
                    'a:has-text("See More")', 'a:has-text("see more")',
                    'span:has-text("See More")', 'span:has-text("see more")',
                    # More specific Facebook patterns
                    'a[href="#"][role="button"]', '[tabindex="0"][role="button"]'
                ]
                
                expanded_count = 0
                
                # First, try to find all "See More" text on the page for debugging
                try:
                    see_more_texts = await page.query_selector_all('text="See More"')
                    logger.debug(f"Found {len(see_more_texts)} 'See More' text elements on page")
                except:
                    pass
                
                # Try multiple approaches to expand content
                for selector in see_more_selectors:
                    try:
                        buttons = await page.query_selector_all(selector)
                        logger.debug(f"Found {len(buttons)} buttons with selector: {selector}")
                        
                        for i, button in enumerate(buttons[:5]):  # Limit to 5 expansions
                            try:
                                # Check if button exists and is visible
                                if await button.is_visible():
                                    # Get button text for debugging
                                    button_text = await button.inner_text()
                                    logger.debug(f"Attempting to click button {i+1}: '{button_text[:30]}...'")
                                    
                                    # Try clicking with different methods
                                    try:
                                        await button.click(force=True, timeout=5000)
                                        expanded_count += 1
                                        logger.debug(f"✅ Successfully clicked button {i+1} ({expanded_count} total)")
                                        await page.wait_for_timeout(2000)  # Wait for content to expand
                                    except:
                                        # Fallback: try JavaScript click
                                        await page.evaluate('(button) => button.click()', button)
                                        expanded_count += 1
                                        logger.debug(f"✅ JS-clicked button {i+1} ({expanded_count} total)")
                                        await page.wait_for_timeout(2000)
                            except Exception as e:
                                logger.debug(f"Failed to click button {i+1}: {str(e)[:50]}")
                                continue
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {str(e)[:50]}")
                        continue
                
                if expanded_count > 0:
                    logger.debug(f"🎯 Expanded {expanded_count} truncated posts")
                    # Wait a bit more for all expanded content to load
                    await page.wait_for_timeout(2000)
                
                # Scroll down to trigger lazy loading of more posts
                logger.debug("📜 Scrolling to load more content...")
                for scroll in range(3):  # Scroll 3 times
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)  # Wait for content to load
                
                # Final scroll back to top to ensure all content is processed
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(1000)
                
                # Get page content
                content = await page.content()
                await browser.close()
                
                return content
                
        except Exception as e:
            logger.debug(f"JavaScript scraping failed for {url}: {e}")
            return ""
    
    async def extract_facebook_posts(self, html_content: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """Extract Facebook posts from JavaScript-rendered HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            posts = []
            
            # Look for various Facebook post containers
            post_selectors = [
                '.fb-post', '.facebook-post', '[data-href*="facebook.com"]',
                '.post-content', '.social-post', '.embed-facebook',
                '.fb-xfbml-parse-ignore', '[id*="facebook"]', 
                '.entry-content p', 'article p', '.content p'  # Fallback to paragraphs
            ]
            
            for selector in post_selectors:
                elements = soup.select(selector)
                logger.debug(f"🔍 Selector '{selector}' found {len(elements)} elements")
                
                for element in elements:
                    if len(posts) >= max_items:  # Stop when we have enough posts
                        break
                        
                    # Extract text content
                    text_content = element.get_text(separator=' ', strip=True)
                    
                    # Clean up the text content - remove Facebook UI artifacts
                    cleaned_text = text_content
                    for artifact in ['...See MoreSee Less', '...See More', 'See MoreSee Less', 
                                   'See Less', '... See More', '...see more', 'see less']:
                        cleaned_text = cleaned_text.replace(artifact, '')
                    
                    # Clean up whitespace
                    cleaned_text = ' '.join(cleaned_text.split())
                    
                    # Validate cleaned content
                    if len(cleaned_text) > 50:
                        # Try to extract timestamp, likes, etc.
                        timestamp_elem = element.select_one('[datetime], .timestamp, .time')
                        timestamp = timestamp_elem.get('datetime') or timestamp_elem.get_text() if timestamp_elem else ''
                        
                        # Extract Facebook URL if available
                        fb_link = element.get('data-href') or ''
                        if not fb_link:
                            link_elem = element.select_one('a[href*="facebook.com"]')
                            fb_link = link_elem.get('href', '') if link_elem else ''
                        
                        posts.append({
                            'title': cleaned_text[:100] + '...' if len(cleaned_text) > 100 else cleaned_text,
                            'content': cleaned_text[:2000] + '...' if len(cleaned_text) > 2000 else cleaned_text,
                            'link': fb_link,
                            'timestamp': datetime.now().isoformat(),
                            'source_timestamp': timestamp
                        })
                
                # Continue trying selectors until we have enough posts
                if len(posts) >= max_items:
                    break
            
            # Fallback: look for any text that looks like Facebook posts
            if not posts:
                # Look for paragraphs with substantial content
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    
                    # Clean Facebook artifacts from fallback text too
                    for artifact in ['...See MoreSee Less', '...See More', 'See MoreSee Less', 
                                   'See Less', '... See More', '...see more', 'see less']:
                        text = text.replace(artifact, '')
                    text = ' '.join(text.split())
                    
                    if len(text) > 100 and not any(skip in text.lower() for skip in ['menu', 'navigation', 'cookie']):
                        posts.append({
                            'title': text[:100] + '...' if len(text) > 100 else text,
                            'content': text[:2000] + '...' if len(text) > 2000 else text,
                            'link': '',
                            'timestamp': datetime.now().isoformat(),
                            'source_timestamp': ''
                        })
                        
                        if len(posts) >= 5:  # Limit fallback posts
                            break
            
            logger.debug(f"Extracted {len(posts)} Facebook posts")
            return posts
            
        except Exception as e:
            logger.debug(f"Error extracting Facebook posts: {e}")
            return []
    
    async def scrape_rss_source(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"📡 RSS feed detected for {source['name']}")
        
        try:
            attempted_url = source['url']
            meta = await self.fetch_url_with_meta(session, attempted_url, source.get('type'))
            feed_data = meta.get('text', '')
            http_status = meta.get('status')
            content_type = meta.get('content_type', '')
            final_url = meta.get('final_url', attempted_url)

            # Self-heal if feed is broken (HTTP error or HTML block page)
            if (
                (http_status and http_status >= 400)
                or (feed_data and self._looks_like_html(feed_data))
                or (not feed_data)
            ):
                new_url = await self._autofix_rss_source_url(session, source)
                if new_url and new_url != attempted_url:
                    logger.warning(f"🛠️ Auto-fixed RSS URL for {source['name']}: {attempted_url} -> {new_url}")
                    source.setdefault('original_url', attempted_url)
                    source['url'] = new_url
                    # retry with new url
                    attempted_url = new_url
                    meta = await self.fetch_url_with_meta(session, attempted_url, source.get('type'))
                    feed_data = meta.get('text', '')
                    http_status = meta.get('status')
                    content_type = meta.get('content_type', '')
                    final_url = meta.get('final_url', attempted_url)

                    # persist cache (best-effort)
                    self.feed_url_cache[source['name']] = {
                        'url': new_url,
                        'updated_at': datetime.now().isoformat(),
                        'from_url': source.get('original_url')
                    }
                    self._save_feed_url_cache()

            if not feed_data:
                logger.warning(f"❌ Failed to fetch RSS feed from {source['name']}")
                return self.create_empty_result(
                    source,
                    f"Failed to fetch RSS feed: {meta.get('error') or 'empty response'}",
                    http_status=http_status,
                    content_type=content_type,
                    final_url=final_url,
                )

            if http_status and http_status >= 400:
                return self.create_empty_result(
                    source,
                    f"HTTP error while fetching feed: {http_status}",
                    http_status=http_status,
                    content_type=content_type,
                    final_url=final_url,
                )

            if self._looks_like_html(feed_data):
                return self.create_empty_result(
                    source,
                    "Expected RSS/XML but got HTML",
                    http_status=http_status,
                    content_type=content_type,
                    final_url=final_url,
                )
            
            logger.info(f"✅ Successfully fetched RSS feed ({len(feed_data)} characters)")
            
            # Parse RSS feed
            feed = feedparser.parse(feed_data)
            
            if feed.bozo:
                logger.warning(f"⚠️ RSS feed may have parsing issues: {feed.bozo_exception}")
            
            logger.info(f"📡 RSS feed parsed: {len(feed.entries)} entries found")
            
            items = []
            thin_items = 0
            skipped_thin = 0
            
            # Dynamic max items: if few sources, get more items per source
            total_sources = len([s for s in self.sources if s.get('enabled', True)])
            if total_sources <= 2:
                max_items = source.get('maxItems', 15)  # Get many items when very few sources
            elif total_sources <= 4:
                max_items = source.get('maxItems', 10)  # Get moderate items
            elif total_sources <= 6:
                max_items = source.get('maxItems', 7)   # Standard amount
            else:
                max_items = source.get('maxItems', 5)   # Limit when many sources
            
            logger.info(f"📊 Using max {max_items} items (total sources: {total_sources})")
            
            for entry in feed.entries:
                title = self._clean_text(entry.get('title', '').strip())
                summary = self._clean_text(entry.get('summary', '').strip())
                if not summary:
                    summary = self._clean_text(entry.get('description', '').strip())
                if not summary:
                    content_list = entry.get('content', []) or []
                    if isinstance(content_list, list) and content_list:
                        summary = self._clean_text((content_list[0] or {}).get('value', '').strip())
                
                # Use title, or summary if no title
                text = title if title else summary
                
                if text and len(text) > 10:
                    entry_link = entry.get('link', '')
                    if entry_link:
                        entry_link = urljoin(final_url or attempted_url, entry_link)
                    item = {
                        'title': text,
                        'link': entry_link,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Add published date if available
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                            item['published'] = pub_date.isoformat()
                        except:
                            pass
                    
                    # Check if summary is too short or generic
                    # We should fetch full content for most RSS feeds as they often only provide teasers
                    needs_full_content = False
                    if not summary or len(summary) < 200:
                        needs_full_content = True
                    elif any(generic in summary.lower() for generic in [
                        'inlägget', 'dök först upp på', 'läs mer', 'read more', 
                        'continue reading', 'click here', '...', 'the post',
                        'appeared first on', 'fortsätt läsa', 'dök först upp'
                    ]):
                        needs_full_content = True
                    # Also fetch if summary is mostly links/HTML (or has any HTML tags)
                    elif summary.count('<') > 0 or summary.count('http') > 2:
                        needs_full_content = True
                    # Also if very short and generic sounding
                    elif len(summary) < 150 and ('dök' in summary or 'inlägg' in summary):
                        needs_full_content = True
                    
                    # Fetch full article content if needed
                    if needs_full_content and entry_link:
                        logger.debug(f"  📄 Fetching full content for: {title[:50]}...")
                        article_content = await self.fetch_article_content(session, entry_link)
                        if article_content:
                            item['summary'] = article_content[:2000] + '...' if len(article_content) > 2000 else article_content
                            logger.debug(f"  ✓ Got {len(article_content)} chars of article content")
                        elif summary:
                            item['summary'] = summary[:1000] + '...' if len(summary) > 1000 else summary
                        else:
                            logger.warning(f"⚠️ No article content for: {title[:80]} ({entry_link})")
                    else:
                        # Use existing summary if it's good enough
                        if summary and summary != title and len(summary) > 10:
                            item['summary'] = summary[:2000] + '...' if len(summary) > 2000 else summary

                    if not item.get('summary'):
                        if self.require_article_content:
                            logger.warning(f"⚠️ Skipping thin item (no content): {title[:80]}")
                            skipped_thin += 1
                            continue
                        logger.warning(f"⚠️ Thin item (no content): {title[:80]}")
                        thin_items += 1
                    
                    items.append(item)
                    logger.debug(f"  ✓ Added RSS item: {text[:80]}...")

                    if len(items) >= max_items:
                        break
            
            logger.info(f"✅ Successfully extracted {len(items)} RSS items from {source['name']}")
            
            return {
                'source': source['name'],
                'type': source['type'],
                'priority': source.get('priority', 3),
                'items': items,
                'scraped_count': len(items),
                'thin_items': thin_items,
                'skipped_thin_items': skipped_thin,
                'format': 'rss',
                'feed_title': feed.feed.get('title', source['name']),
                'http_status': http_status,
                'content_type': content_type,
                'final_url': final_url,
                'original_url': source.get('original_url')
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing RSS feed from {source['name']}: {e}")
            return self.create_empty_result(source, f'RSS parsing error: {str(e)}')
    
    async def scrape_html_source(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> Dict[str, Any]:
        meta = await self.fetch_url_with_meta(session, source['url'], source.get('type'))
        html = meta.get('text', '')
        http_status = meta.get('status')
        content_type = meta.get('content_type', '')
        final_url = meta.get('final_url', source['url'])

        if not html:
            logger.warning(f"❌ Failed to fetch HTML content from {source['name']}")
            return self.create_empty_result(
                source,
                f"Failed to fetch HTML: {meta.get('error') or 'empty response'}",
                http_status=http_status,
                content_type=content_type,
                final_url=final_url,
            )

        if http_status and http_status >= 400:
            return self.create_empty_result(
                source,
                f"HTTP error while fetching HTML: {http_status}",
                http_status=http_status,
                content_type=content_type,
                final_url=final_url,
            )
        
        logger.info(f"✅ Successfully fetched HTML ({len(html)} characters from {source['name']})")
        
        # Check if this page needs JavaScript rendering (Facebook embeds, etc.)
        needs_javascript = any(indicator in html.lower() for indicator in [
            'fb-post', 'facebook.com/plugins', 'facebook-blog', 'social-embed', 
            'instagram-media', 'twitter-tweet', 'data-src=', 'lazy-load'
        ])
        
        if needs_javascript and PLAYWRIGHT_AVAILABLE:
            logger.info(f"🚀 Detected dynamic content - using JavaScript rendering for {source['name']}")
            js_html = await self.fetch_javascript_content(source['url'], source.get('selector'))
            if js_html:
                html = js_html
                logger.info(f"✅ JavaScript rendering complete ({len(html)} characters)")
        
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        thin_items = 0
        skipped_thin = 0
        
        if source['type'] == 'weather':
            # Special handling for weather
            logger.info(f"🌤️ Extracting weather information...")
            weather_info = self.extract_weather(soup)
            items = [weather_info] if weather_info else []
            if items:
                logger.info(f"✅ Found weather info: {items[0].get('description', 'N/A')}")
            else:
                logger.warning(f"❌ No weather information found")
        elif 'facebook-blog' in source['url'] or needs_javascript:
            # Special handling for Facebook/social media content
            logger.info(f"📘 Extracting Facebook/social media posts...")
            max_items = source.get('maxItems', 5)
            facebook_posts = await self.extract_facebook_posts(html, max_items)
            items = facebook_posts  # No need to limit again since extract_facebook_posts already respects max_items
            if items:
                logger.info(f"✅ Extracted {len(items)} social media posts")
            else:
                logger.warning(f"❌ No social media posts found")
        else:
            # Extract news/tech items from HTML
            selector = source.get('selector', 'h2')
            max_items = source.get('maxItems', 5)
            logger.info(f"🔎 Looking for HTML elements with selector: '{selector}' (max {max_items} items)")
            
            elements = soup.select(selector)
            logger.info(f"📰 Found {len(elements)} total HTML elements matching selector")
            
            processed = 0
            for elem in elements[:max_items]:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    # Try to get link if element is or contains a link
                    link = ''
                    if elem.name == 'a':
                        link = elem.get('href', '')
                    else:
                        link_elem = elem.find('a')
                        if link_elem:
                            link = link_elem.get('href', '')

                    if link:
                        link = urljoin(final_url or source['url'], link)

                    summary = ''
                    if link:
                        article_content = await self.fetch_article_content(session, link)
                        if article_content:
                            summary = article_content[:2000] + '...' if len(article_content) > 2000 else article_content
                        else:
                            logger.warning(f"⚠️ No article content for: {text[:80]} ({link})")

                    if not summary and self.require_article_content:
                        logger.warning(f"⚠️ Skipping thin item (no content): {text[:80]}")
                        skipped_thin += 1
                        continue
                    if not summary:
                        logger.warning(f"⚠️ Thin item (no content): {text[:80]}")
                        thin_items += 1
                    
                    items.append({
                        'title': text,
                        'link': link,
                        'summary': summary,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.debug(f"  ✓ Added HTML item: {text[:80]}...")
                    processed += 1
                else:
                    logger.debug(f"  ✗ Skipped (too short): {text[:40]}...")
            
            logger.info(f"✅ Successfully extracted {processed} HTML items from {source['name']}")
        
        return {
            'source': source['name'],
            'type': source['type'],
            'priority': source.get('priority', 3),
            'items': items,
            'scraped_count': len(items),
            'thin_items': thin_items,
            'skipped_thin_items': skipped_thin,
            'format': 'html',
            'http_status': http_status,
            'content_type': content_type,
            'final_url': final_url
        }
    
    def create_empty_result(
        self,
        source: Dict[str, Any],
        error: str,
        http_status: int | None = None,
        content_type: str | None = None,
        final_url: str | None = None,
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'source': source['name'],
            'type': source['type'],
            'items': [],
            'error': error
        }
        if http_status is not None:
            result['http_status'] = http_status
        if content_type:
            result['content_type'] = content_type
        if final_url:
            result['final_url'] = final_url
        return result
    
    def extract_weather(self, soup: BeautifulSoup) -> Dict[str, str]:
        try:
            # Get the raw text content from the page
            text_content = soup.get_text(strip=True)
            logger.info(f"🌤️ Raw weather text ({len(text_content)} chars): {text_content[:300]}...")
            
            # For plain text responses (like wttr.in format=3), the content might be minimal
            if text_content and len(text_content) < 500:  # Likely plain text weather
                # Clean up the text
                weather_text = text_content.strip()
                
                # If it looks like wttr.in format (city: emoji temp)
                if ':' in weather_text and any(char in weather_text for char in ['°C', '°F', '🌤', '☀', '🌧', '🌫', '❄', '⛅', '🌩', '⛈', '🌦']):
                    logger.info(f"✅ Detected wttr.in plain text format")
                    
                    return {
                        'description': weather_text,
                        'temperature': self.extract_temperature_from_text(weather_text),
                        'location': self.extract_location_from_text(weather_text),
                        'timestamp': datetime.now().isoformat(),
                        'raw_content': text_content,
                        'format': 'wttr_plain'
                    }
                
                # Any other short text with temperature
                elif any(temp_indicator in weather_text for temp_indicator in ['°C', '°F']):
                    logger.info(f"✅ Detected plain text weather format")
                    return {
                        'description': weather_text,
                        'temperature': self.extract_temperature_from_text(weather_text),
                        'timestamp': datetime.now().isoformat(),
                        'raw_content': text_content,
                        'format': 'plain_text'
                    }
            
            # Check if this is wttr.in HTML format  
            if 'wttr.in' in str(soup) or any(char in text_content for char in ['°C', '°F', '🌤', '☀', '🌧', '🌫', '❄', '⛅']):
                # This is likely wttr.in or similar weather service with HTML
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                if lines:
                    # Look for weather information in the lines
                    for line in lines:
                        if any(char in line for char in ['°C', '°F', '🌤', '☀', '🌧', '🌫', '❄', '⛅']):
                            return {
                                'description': line,
                                'temperature': self.extract_temperature_from_text(line),
                                'location': self.extract_location_from_text(line),
                                'timestamp': datetime.now().isoformat(),
                                'raw_content': text_content[:500],
                                'format': 'wttr_html'
                            }
            
            # Fallback: Try SMHI or other HTML-based weather sites
            temp = soup.select_one('.temperature')
            desc = soup.select_one('.weather-description')
            
            if temp and desc:
                return {
                    'temperature': temp.get_text(strip=True),
                    'description': desc.get_text(strip=True),
                    'timestamp': datetime.now().isoformat(),
                    'format': 'html_structured'
                }
            
            # If no structured data found, use the text content
            if text_content:
                return {
                    'description': text_content[:200] + '...' if len(text_content) > 200 else text_content,
                    'timestamp': datetime.now().isoformat(),
                    'raw_content': text_content[:500],
                    'format': 'fallback'
                }
                
        except Exception as e:
            logger.error(f"❌ Weather extraction error: {e}")
        
        return {
            'description': 'Väderinformation ej tillgänglig',
            'timestamp': datetime.now().isoformat(),
            'error': 'extraction_failed'
        }
    
    def extract_temperature_from_text(self, text: str) -> str:
        """Extract temperature from text like 'kalmar: 🌫 +20°C'"""
        import re
        temp_match = re.search(r'[+-]?\d+°[CF]', text)
        return temp_match.group(0) if temp_match else ''
    
    def extract_location_from_text(self, text: str) -> str:
        """Extract location from text like 'kalmar: 🌫 +20°C'"""
        if ':' in text:
            location = text.split(':')[0].strip()
            return location.title() if location else ''
        return ''

    @staticmethod
    def _is_thin_item(item: Dict[str, Any]) -> bool:
        summary = (item.get('summary') or '').strip()
        title = (item.get('title') or '').strip()
        if not title or len(title) < 12:
            return True
        if not summary:
            return True
        return len(summary) < 320

    @staticmethod
    def _build_search_query_from_title(title: str) -> str:
        """Build a conservative keyword query from a Swedish/English headline."""
        t = (title or '').strip()
        if not t:
            return ''

        # Remove punctuation and collapse whitespace
        t = re.sub(r"[^\w\s\-åäöÅÄÖ]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()

        stop = {
            'och', 'att', 'som', 'för', 'med', 'utan', 'i', 'på', 'av', 'till', 'från', 'om', 'när',
            'den', 'det', 'de', 'en', 'ett', 'the', 'a', 'an', 'to', 'of', 'in', 'on', 'for', 'with',
            'är', 'var', 'blir', 'blev', 'kan', 'ska', 'har', 'hade', 'får', 'fick', 'nya', 'ny',
        }

        parts = [p for p in t.split(' ') if p and p.lower() not in stop]
        # Keep it short to avoid overly broad searches
        parts = parts[:10]
        return ' '.join(parts)

    @staticmethod
    def _google_news_rss_url(query: str, *, hl: str = 'sv', gl: str = 'SE', ceid: str = 'SE:sv') -> str:
        q = quote_plus(query)
        return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

    async def _fetch_google_news_rss_entries(
        self,
        session: aiohttp.ClientSession,
        query: str,
        *,
        max_entries: int = 6,
        require_domain: str | None = None,
    ) -> List[Dict[str, Any]]:
        if not query:
            return []
        url = self._google_news_rss_url(query)
        meta = await self.fetch_url_with_meta(session, url, 'rss')
        xml = meta.get('text', '')
        if not xml or self._looks_like_html(xml):
            return []

        feed = feedparser.parse(xml)
        out: List[Dict[str, Any]] = []
        for e in (feed.entries or [])[: max_entries * 2]:
            link = (e.get('link') or '').strip()
            title = (e.get('title') or '').strip()
            if not link or not title:
                continue

            if require_domain:
                try:
                    if require_domain.lower() not in (urlparse(link).netloc or '').lower():
                        # Sometimes Google News links are on news.google.com; allow and rely on redirects.
                        if 'news.google.com' not in (urlparse(link).netloc or '').lower():
                            continue
                except Exception:
                    continue

            out.append({'title': title, 'link': link})
            if len(out) >= max_entries:
                break
        return out

    async def _enrich_item_with_related(
        self,
        session: aiohttp.ClientSession,
        item: Dict[str, Any],
        *,
        max_related: int,
        provider: str,
        omni_only: bool,
    ) -> None:
        title = (item.get('title') or '').strip()
        if not title:
            return

        query = self._build_search_query_from_title(title)
        if not query:
            return

        require_domain = 'omni.se' if omni_only else None
        entries: List[Dict[str, Any]] = []

        if provider in {'google_news', 'google'}:
            # If omni_only is set, bias heavily towards omni results.
            q = f"site:omni.se {query}" if omni_only else query
            entries = await self._fetch_google_news_rss_entries(session, q, max_entries=max_related, require_domain=require_domain)
        else:
            return

        if not entries:
            return

        existing_url = (item.get('link') or '').strip()
        related: List[Dict[str, Any]] = item.get('related', []) if isinstance(item.get('related'), list) else []

        for e in entries:
            link = (e.get('link') or '').strip()
            if not link or link == existing_url:
                continue
            try:
                content = await self.fetch_article_content(session, link)
            except Exception:
                content = ''
            content = (content or '').strip()
            if len(content) < 450:
                continue
            related.append({
                'title': (e.get('title') or '').strip(),
                'link': link,
                'summary': content[:2000] + '...' if len(content) > 2000 else content,
                'provider': provider,
            })
            if len(related) >= max_related:
                break

        if related:
            item['related'] = related

    async def _enrich_thin_items(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Best-effort enrichment: if an item is too 'thin', try to fetch 1-2 related sources."""
        enabled = os.getenv('MMM_ENRICH_THIN_ITEMS', '1').strip().lower() not in {'0', 'false', 'no'}
        if not enabled:
            return results

        provider = os.getenv('MMM_ENRICH_PROVIDER', 'google_news').strip().lower() or 'google_news'
        max_items_total = int(os.getenv('MMM_ENRICH_MAX_ITEMS', '6') or 6)
        max_related = int(os.getenv('MMM_ENRICH_MAX_RELATED_PER_ITEM', '2') or 2)
        omni_only = os.getenv('MMM_ENRICH_OMNI_ONLY', '0').strip().lower() in {'1', 'true', 'yes'}

        if max_items_total <= 0 or max_related <= 0:
            return results

        logger.info(
            "🧩 Enrichment enabled: provider=%s, max_items=%s, max_related=%s, omni_only=%s",
            provider,
            max_items_total,
            max_related,
            omni_only,
        )

        enriched = 0
        async with aiohttp.ClientSession() as session:
            for group in results or []:
                if enriched >= max_items_total:
                    break
                if not isinstance(group, dict):
                    continue
                if group.get('type') in {'weather'}:
                    continue
                items = group.get('items') or []
                if not isinstance(items, list):
                    continue

                for item in items:
                    if enriched >= max_items_total:
                        break
                    if not isinstance(item, dict):
                        continue
                    if not self._is_thin_item(item):
                        continue
                    try:
                        await self._enrich_item_with_related(
                            session,
                            item,
                            max_related=max_related,
                            provider=provider,
                            omni_only=omni_only,
                        )
                        if item.get('related'):
                            enriched += 1
                            logger.info("🧩 Enriched thin item: %s... (+%s related)", (item.get('title') or '')[:60], len(item.get('related') or []))
                    except Exception as e:
                        logger.debug(f"Enrichment failed for item: {e}")

        return results
    
    async def scrape_all(self) -> List[Dict[str, Any]]:
        async def _scrape_once() -> List[Dict[str, Any]]:
            logger.info(f"🚀 Starting scraping from {len(self.sources)} sources...")
            async with aiohttp.ClientSession() as session:
                tasks = [self.scrape_source(session, source) for source in self.sources]
                scraped = await asyncio.gather(*tasks)

            # Optional best-effort enrichment for items that are too short to summarize well
            try:
                scraped = await self._enrich_thin_items(scraped)
            except Exception as e:
                logger.warning(f"🧩 Enrichment step failed, continuing without it: {e}")

            # Sort by priority
            scraped.sort(key=lambda x: x.get('priority', 99))
            return scraped

        def _compute_thin_stats(scraped: List[Dict[str, Any]]) -> Dict[str, int | float]:
            total_items = sum(len(result.get('items', [])) for result in scraped)
            successful_sources = len([r for r in scraped if r.get('items')])
            total_thin = sum(int(result.get('thin_items', 0) or 0) for result in scraped)
            total_skipped_thin = sum(int(result.get('skipped_thin_items', 0) or 0) for result in scraped)
            total_seen = total_items + total_skipped_thin
            thin_seen = total_thin + total_skipped_thin
            thin_ratio = (thin_seen / total_seen) if total_seen else 0.0
            return {
                'total_items': total_items,
                'successful_sources': successful_sources,
                'total_thin': total_thin,
                'total_skipped_thin': total_skipped_thin,
                'total_seen': total_seen,
                'thin_seen': thin_seen,
                'thin_ratio': thin_ratio,
            }

        def _log_scrape_summary(scraped: List[Dict[str, Any]]) -> None:
            stats = _compute_thin_stats(scraped)
            logger.info(f"📊 Scraping Summary:")
            logger.info(f"  • Total sources: {len(self.sources)}")
            logger.info(f"  • Successful sources: {stats['successful_sources']}")
            logger.info(f"  • Total items extracted: {stats['total_items']}")
            if stats['total_thin'] or stats['total_skipped_thin']:
                logger.warning(
                    f"  ⚠️ Thin items (no content): {stats['total_thin']} (skipped: {stats['total_skipped_thin']})"
                )

            for result in scraped:
                item_count = len(result.get('items', []))
                status = "✅" if item_count > 0 else "❌"
                logger.info(f"  {status} {result['source']}: {item_count} items")
                thin_count = int(result.get('thin_items', 0) or 0)
                skipped_count = int(result.get('skipped_thin_items', 0) or 0)
                if thin_count or skipped_count:
                    logger.warning(f"    ⚠️ Thin items: {thin_count} (skipped: {skipped_count})")

        results = await _scrape_once()

        # Auto-tighten if too many thin items and strict mode is allowed
        if self.thin_ratio_auto_strict and not self.require_article_content:
            stats = _compute_thin_stats(results)
            if stats['total_seen'] >= self.thin_ratio_min_items and stats['thin_ratio'] >= self.thin_ratio_threshold:
                logger.warning(
                    "⚠️ High thin-item ratio (%.0f%%). Retrying with strict content requirement.",
                    stats['thin_ratio'] * 100,
                )
                self.require_article_content = True
                results = await _scrape_once()

        _log_scrape_summary(results)
        return results

async def main():
    scraper = NewsScraper()
    results = await scraper.scrape_all()
    
    with open('scraped_content.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("Scraping completed")
    return results

if __name__ == "__main__":
    asyncio.run(main())