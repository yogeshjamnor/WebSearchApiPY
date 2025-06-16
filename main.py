from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://html.duckduckgo.com/html?q={query}"
    logging.debug(f"Searching URL: {search_url}")

    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a.get("href") for a in soup.select("a.result__a") if a.get("href", "").startswith("http")]
        logging.debug(f"Found links: {links}")

        if not links:
            return jsonify({"data": ["❌ No links found from DuckDuckGo for that query."]})

        results = []
        for href in links[:3]:
            try:
                logging.debug(f"Fetching article: {href}")
                art = requests.get(href, headers=headers, timeout=10)
                art.raise_for_status()
                art_soup = BeautifulSoup(art.text, "html.parser")
                paragraphs = art_soup.find_all("p")
                text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60]
                logging.debug(f"Paragraph count: {len(text_blocks)}")
                if not text_blocks:
                    continue
                full_text = " ".join(text_blocks[:20])
                source = href.split("/")[2].replace("www.", "")
                results.append(f"According to {source}:\n{full_text}")
            except Exception as e:
                logging.warning(f"Error scraping {href}: {e}")
                continue

        if not results:
            return jsonify({"data": ["❌ No articles scraped—pages had no valid content."]})
        return jsonify({"data": results})

    except Exception as e:
        logging.error(f"Search failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
