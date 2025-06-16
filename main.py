from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

SITE_CATEGORIES = {
    "tech": ["techcrunch.com", "wired.com", "yourstory.com", "livemint.com"],
    "news": ["ndtv.com", "news18.com", "hindustantimes.com", "indianexpress.com"],
    "business": ["economictimes.indiatimes.com", "thehindu.com", "business-standard.com"],
    "general": ["wikipedia.org", "britannica.com"]
}

KEYWORDS_MAP = {
    "ai": "tech",
    "artificial intelligence": "tech",
    "machine learning": "tech",
    "budget": "business",
    "finance": "business",
    "stock": "business",
    "rain": "news",
    "accident": "news",
    "crash": "news",
    "explosion": "news",
    "pune": "news",
    "mumbai": "news",
    "ahmedabad": "news"
}

def get_category(query):
    query_lower = query.lower()
    for keyword, cat in KEYWORDS_MAP.items():
        if keyword in query_lower:
            return cat
    return "news"

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    category = get_category(query)
    selected_sites = SITE_CATEGORIES.get(category, SITE_CATEGORIES["news"])
    headers = {"User-Agent": "Mozilla/5.0"}

    results = []
    for domain in selected_sites:
        search_url = f"https://www.bing.com/search?q={query}+site:{domain}"
        try:
            search_res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(search_res.text, "html.parser")
            links = [a.get("href") for a in soup.select("li.b_algo h2 a") if a.get("href", "").startswith("http")][:3]

            for url in links:
                try:
                    art_res = requests.get(url, headers=headers, timeout=10)
                    art_soup = BeautifulSoup(art_res.text, "html.parser")
                    paras = [p.get_text(strip=True) for p in art_soup.find_all("p") if len(p.get_text(strip=True)) > 60]
                    content = "\n".join(paras)
                    summary = " ".join(content.split()[:400])
                    source = url.split("/")[2].replace("www.", "")
                    if summary:
                        results.append(f"According to {source}:\n{summary}")
                except:
                    continue
        except:
            continue

    if not results:
        return jsonify({"data": ["❌ No live readable content found for that query."]})

    return jsonify({"data": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
