from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# ✅ Strictly allow only Indian English news domains
INDIAN_ENGLISH_DOMAINS = {
    "ndtv.com",
    "timesofindia.indiatimes.com",
    "indiatoday.in",
    "hindustantimes.com",
    "news18.com",
    "thehindu.com",
    "indianexpress.com",
    "livemint.com",
    "deccanherald.com",
    "theprint.in"
}

BLOCKED_DOMAINS = {"wikipedia.org", "wikidata.org", "britannica.com"}

def is_valid_domain(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return (
        any(site in domain for site in INDIAN_ENGLISH_DOMAINS)
        and not any(block in domain for block in BLOCKED_DOMAINS)
    )

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={query}+site:ndtv.com+OR+site:timesofindia.indiatimes.com+OR+site:indiatoday.in+OR+site:hindustantimes.com+OR+site:news18.com+OR+site:thehindu.com+OR+site:indianexpress.com+OR+site:livemint.com+OR+site:deccanherald.com+OR+site:theprint.in"

    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # ✅ Get only valid Indian English links
        links = []
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if href and href.startswith("http") and is_valid_domain(href):
                links.append(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No valid Indian English news links found."]})

        # ✅ Fetch article summaries
        results = []
        for url in links:
            try:
                article = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article.text, "html.parser")
                paras = article_soup.find_all("p")
                content = "\n".join([
                    p.get_text(strip=True) for p in paras
                    if len(p.get_text(strip=True).split()) > 10
                    and p.get_text(strip=True).isascii()
                    and "cookie" not in p.get_text().lower()
                ])
                summary = " ".join(content.split()[:400])
                domain = urlparse(url).netloc.replace("www.", "")
                if summary:
                    results.append(f"According to {domain}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable English content."]})

        return jsonify({"data": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
