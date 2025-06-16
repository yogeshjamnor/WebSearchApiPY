from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

@app.route("/scrape", methods=["GET"])
def scrape_news():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    rss_url = f"https://news.google.com/rss/search?q={query}+when:7d&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(rss_url, headers=headers, timeout=10)
        root = ET.fromstring(res.content)

        items = root.findall(".//item")
        if not items:
            return jsonify({"data": ["❌ No English news found."]})

        summaries = []
        for item in items[:4]:  # limit to 3-4 top articles
            link = item.find("link").text
            title = item.find("title").text
            try:
                article = requests.get(link, headers=headers, timeout=10)
                soup = BeautifulSoup(article.text, "html.parser")
                paras = soup.find_all("p")
                content = "\n".join(
                    [p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 50]
                )
                summary = " ".join(content.split()[:400])
                if summary:
                    summaries.append(f"According to {link.split('/')[2]}:\n{summary}")
            except:
                continue

        if not summaries:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable content."]})

        return jsonify({"data": summaries})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
