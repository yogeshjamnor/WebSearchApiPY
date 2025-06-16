from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Updated site list to include multilingual Indian news portals
SITE_CATEGORIES = {
    "tech": ["techcrunch.com", "wired.com", "yourstory.com", "livemint.com"],
    "news": [
        "ndtv.com", "news18.com", "hindustantimes.com", "indianexpress.com",
        "timesofindia.indiatimes.com", "maharashtratimes.com", "loksatta.com", "navbharattimes.indiatimes.com"
    ],
    "business": ["economictimes.indiatimes.com", "thehindu.com", "business-standard.com"],
    "general": []
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
    for keyword in KEYWORDS_MAP:
        if keyword in query_lower:
            return KEYWORDS_MAP[keyword]
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
    try:
        for domain in selected_sites:
            search_url = f"https://www.bing.com/search?q={query}+site:{domain}"
            search_res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(search_res.text, "html.parser")
            result_links = []

            for a in soup.select("li.b_algo h2 a"):
                href = a.get("href")
                if href and href.startswith("http"):
                    result_links.append(href)
                if len(result_links) >= 3:
                    break

            for url in result_links:
                try:
                    article_res = requests.get(url, headers=headers, timeout=10)
                    article_soup = BeautifulSoup(article_res.text, "html.parser")
                    paragraphs = article_soup.find_all("p")
                    content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60])
                    summary = " ".join(content.split()[:400])
                    source = url.split("/")[2].replace("www.", "")
                    if summary:
                        results.append(f"According to {source}:\n{summary}")
                except:
                    continue

        if not results:
            return jsonify({"data": ["\u274c No live readable articles found for that query."]})

        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
