from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "API is Live"

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    url = f"https://lite.duckduckgo.com/lite?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        for link in soup.select("a"):
            title = link.text.strip()
            href = link.get("href")

            # Only look for DuckDuckGo redirect links
            if href and "uddg=" in href:
                parsed = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed.query)
                real_link = query_params.get("uddg", [None])[0]

                if real_link:
                    decoded_link = urllib.parse.unquote(real_link)
                    results.append({"title": title, "link": decoded_link})

            if len(results) >= 5:
                break

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
