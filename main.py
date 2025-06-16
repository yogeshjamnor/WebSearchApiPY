from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Query-based site filters
SITE_FILTERS = {
    "news": [
        "ndtv.com",
        "news18.com",
        "hindustantimes.com",
        "aljazeera.com",
        "cnn.com",
        "bbc.com",
        "reuters.com",
        "theguardian.com"
    ],
    "sports": [
        "espn.com",
        "cricbuzz.com",
        "goal.com",
        "sportstar.thehindu.com"
    ],
    "technology": [
        "techcrunch.com",
        "wired.com",
        "theverge.com",
        "gadgets360.com"
    ],
    "finance": [
        "moneycontrol.com",
        "livemint.com",
        "economictimes.indiatimes.com",
        "businessinsider.com"
    ],
    "default": [
        "ndtv.com",
        "news18.com",
        "hindustantimes.com",
        "aljazeera.com"
    ]
}

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}

    # Determine category by keyword in the query
    category = "default"
    for cat in SITE_FILTERS:
        if cat in query.lower():
            category = cat
            break

    sites = SITE_FILTERS[category]
    sites_filter = "+OR+".join(f"site:{site}" for site in sites)

    # Bing search
    search_url = f"https://www.bing.com/search?q={query}+{sites_filter}"

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")
        result_links = []

        # Collect links from search results
        for li in soup.select("li.b_algo h2 a"):
            href = li.get("href")
            if href and href.startswith("http"):
                result_links.append(href)
            if len(result_links) >= 3:
                break

        if not result_links:
            return jsonify({"data": ["❌ No articles found for that query."]})

        results = []
        for url in result_links:
            try:
                article_res = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 60])
                summary = " ".join(content.split()[:400])
                source = url.split("/")[2].replace("www.", "")
                if summary:
                    results.append(f"According to {source}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ No readable content found in the articles."]})
        
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
