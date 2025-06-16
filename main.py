from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_links(source, query, search_url, selector, attr="href", limit=2):
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = [a[attr] for a in soup.select(selector) if a.has_attr(attr) and a[attr].startswith("http")]
        return links[:limit]
    except:
        return []

def extract_content(url, source_name):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60]
        combined = "\n".join(text_blocks)
        summary = " ".join(combined.split()[:400])
        return f"According to {source_name}:\n{summary}" if summary else None
    except:
        return None

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    all_results = []

    # Add Indian news websites (Hindi/English/Marathi)
    sources = [
        {
            "name": "NDTV",
            "search_url": f"https://www.ndtv.com/search?searchtext={query}",
            "selector": "div.new_search_content div.searchTitle a"
        },
        {
            "name": "News18",
            "search_url": f"https://www.news18.com/search/?q={query}",
            "selector": "div.search-listing li a"
        },
        {
            "name": "AajTak",
            "search_url": f"https://www.aajtak.in/search?search={query}",
            "selector": "div.listing div.news_title a"
        },
        {
            "name": "IndiaToday",
            "search_url": f"https://www.indiatoday.in/search?search={query}",
            "selector": "div.search-result a"
        },
        {
            "name": "ZeeNews",
            "search_url": f"https://zeenews.india.com/search?q={query}",
            "selector": "div.search-cont a"
        }
    ]

    for source in sources:
        links = fetch_links(source["name"], query, source["search_url"], source["selector"])
        for link in links:
            content = extract_content(link, source["name"])
            if content:
                all_results.append(content)

    if not all_results:
        return jsonify({"data": ["❌ No Indian news found in any language for that query."]})
    
    return jsonify({"data": all_results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
