from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Trusted Indian news domains
INDIAN_NEWS_SITES = [
    "ndtv.com", "news18.com", "hindustantimes.com", "indiatoday.in",
    "timesofindia.indiatimes.com", "thehindu.com", "zeenews.india.com",
    "firstpost.com", "livemint.com", "deccanherald.com"
]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    site_filter = "+OR+".join(f"site:{site}" for site in INDIAN_NEWS_SITES)
    search_url = f"https://html.duckduckgo.com/html/?q={query}+{site_filter}"

    try:
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        links = []
        seen = set()

        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http") and any(site in href for site in INDIAN_NEWS_SITES):
                if href not in seen:
                    links.append(href)
                    seen.add(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No Indian news articles found for that query."]})

        results = []
        for link in links:
            try:
                res = requests.get(link, headers=headers, timeout=10)
                article_soup = BeautifulSoup(res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([
                    p.get_text(strip=True) for p in paragraphs
                    if len(p.get_text(strip=True)) > 60
                ])
                summary = " ".join(content.split()[:400])
                domain = link.split("/")[2].replace("www.", "")
                if summary and len(summary) > 200:
                    results.append(f"According to {domain}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ Articles found, but no readable content extracted."]})
        
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
