from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Only trusted Indian domains
INDIAN_SITES = [
    "ndtv.com", "timesofindia.indiatimes.com", "indiatoday.in", "hindustantimes.com",
    "news18.com", "thehindu.com", "indianexpress.com", "livemint.com", "deccanherald.com"
]

# Domains to block (Wikipedia, Britannica)
BLOCKED_DOMAINS = ["wikipedia.org", "britannica.com", "wikidata.org", "wikivoyage.org"]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={query}+site:" + "+OR+site:".join(INDIAN_SITES)

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        links = []
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if href and href.startswith("http"):
                domain = href.split("/")[2].replace("www.", "")
                if domain in INDIAN_SITES and not any(b in domain for b in BLOCKED_DOMAINS):
                    links.append(href)
            if len(links) >= 4:
                break

        if not links:
            return jsonify({"data": ["❌ No valid Indian English news links found."]})

        results = []
        for url in links:
            try:
                article = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(article.text, "html.parser")
                content_blocks = soup.find_all(["p", "span", "article"])
                paragraphs = []

                for block in content_blocks:
                    text = block.get_text(strip=True)
                    if len(text.split()) > 10 and '©' not in text and 'cookie' not in text.lower():
                        paragraphs.append(text)

                clean_text = " ".join(dict.fromkeys(paragraphs))  # Remove duplicates
                if len(clean_text.split()) > 100:
                    domain = url.split("/")[2].replace("www.", "")
                    results.append(f"According to {domain}:\n" + " ".join(clean_text.split()[:400]))
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ Articles found, but readable content missing."]})
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
