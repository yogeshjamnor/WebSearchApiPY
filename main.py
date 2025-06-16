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

    search_url = f"https://lite.duckduckgo.com/lite?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        for link in soup.select("a"):
            href = link.get("href")
            if href and "uddg=" in href:
                full_url = urllib.parse.unquote(href.split("uddg=")[-1].split("&")[0])
                article_text = extract_article_text(full_url)
                if article_text:
                    results.append({
                        "source": full_url,
                        "content": article_text
                    })
                if len(results) >= 3:  # Limit to 3 full articles per query
                    break

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_article_text(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Get all visible paragraph tags
        paragraphs = soup.find_all("p")
        content = "\n".join(p.text.strip() for p in paragraphs if len(p.text.strip()) > 60)

        # Filter out small junk content
        if len(content) > 800:  # roughly A4 size
            return content[:5000]  # limit to avoid too long response
        return None
    except:
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
