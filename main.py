from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def home():
    return "API is Live"

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    url = f"https://lite.duckduckgo.com/lite?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        for link in soup.select("a"):
            title = link.text.strip()
            href = link.get("href")
            if href and "http" in href:
                results.append({"title": title, "link": href})
            if len(results) >= 5:
                break

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
