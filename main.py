from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    duckduckgo_url = f"https://html.duckduckgo.com/html/?q={query}"

    try:
        res = requests.get(duckduckgo_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []

        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and "http" in href:
                try:
                    article = requests.get(href, headers=headers, timeout=10)
                    article_soup = BeautifulSoup(article.text, "html.parser")
                    paragraphs = article_soup.find_all("p")
                    text_blocks = [p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 60]
                    full_text = " ".join(text_blocks[:20])  # Limit to ~A4 size content
                    source = href.split("/")[2].replace("www.", "")
                    if full_text:
                        results.append(f"According to {source}:\n{full_text}")
                    if len(results) >= 3:
                        break
                except Exception as e:
                    continue

        if not results:
            return jsonify({"data": ["❌ No results found. Try different keywords."]})
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
