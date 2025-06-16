from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

INDIAN_NEWS_DOMAINS = {
    "ndtv.com",
    "timesofindia.indiatimes.com",
    "indiatoday.in",
    "hindustantimes.com",
    "news18.com",
    "thehindu.com",
    "indianexpress.com",
    "livemint.com",
    "deccanherald.com"
}

BLOCKED_DOMAINS = {"wikipedia.org", "wikidata.org", "britannica.com", "wikivoyage.org"}

def is_valid_indian_news_site(url):
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        return (
            any(site in domain for site in INDIAN_NEWS_DOMAINS)
            and not any(block in domain for block in BLOCKED_DOMAINS)
        )
    except:
        return False

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={query}"

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        links = []
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if href and href.startswith("http") and is_valid_indian_news_site(href):
                links.append(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No valid Indian news links found."]})

        results = []
        for url in links:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([
                    p.get_text(strip=True) for p in paragraphs
                    if len(p.get_text(strip=True).split()) > 10
                    and "cookie" not in p.get_text().lower()
                    and "consent" not in p.get_text().lower()
                    and "subscribe" not in p.get_text().lower()
                ])
                summary = " ".join(content.split()[:400])
                domain = urlparse(url).netloc.replace("www.", "")
                if summary:
                    results.append(f"According to {domain}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable content."]})

        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
