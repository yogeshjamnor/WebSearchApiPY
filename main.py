from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Domains to ignore
EXCLUDED_DOMAINS = [
    "wikipedia.org", "wikitravel.org", "youtube.com", "facebook.com",
    "instagram.com", "britannica.com", "tripadvisor.com", "quora.com",
    "medium.com", "linkedin.com", "reddit.com", "pinterest.com", "amazon.com"
]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    try:
        # Force recent news (last 2 days)
        recent_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        encoded_query = quote(f"{query} after:{recent_date}")
        search_url = f"https://www.bing.com/news/search?q={encoded_query}"

        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.select("a.title"):
            href = a.get("href")
            if href and href.startswith("http"):
                domain = href.split("/")[2].replace("www.", "")
                if not any(ex in domain for ex in EXCLUDED_DOMAINS):
                    links.append(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No valid news links found. Try different keywords."]})

        summaries = []
        for link in links:
            try:
                page = requests.get(link, headers=HEADERS, timeout=10)
                article = BeautifulSoup(page.text, "html.parser")

                # Clean up unwanted tags
                for tag in article(['script', 'style', 'footer', 'nav', 'aside', 'form']):
                    tag.decompose()

                # Get readable paragraphs
                paragraphs = article.find_all('p')
                content = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if 60 < len(text) < 1000 and not any(x in text.lower() for x in ['cookie', 'subscribe', 'advert', 'feedback']):
                        content.append(text)

                # Build a summary of up to 20 useful paragraphs
                final_text = "\n\n".join(content[:20])
                if final_text:
                    domain = link.split("/")[2].replace("www.", "")
                    summaries.append(f"📌 According to {domain}:\n\n{final_text}\n\n🔗 {link}")
            except Exception as e:
                print(f"[Error scraping] {link} — {e}")
                continue

        if summaries:
            return jsonify({"data": summaries})
        else:
            return jsonify({"data": ["❌ Articles found, but no readable summaries extracted."]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
