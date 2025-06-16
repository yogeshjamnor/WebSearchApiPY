from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

# Keywords for filtering Indian English results
indian_domains = [
    "indiatoday.in", "ndtv.com", "timesofindia.indiatimes.com", "hindustantimes.com",
    "news18.com", "livemint.com", "thehindu.com", "economictimes.indiatimes.com",
    "indianexpress.com", "dnaindia.com", "deccanherald.com"
]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={query}+site:{" OR site:".join(indian_domains)}"

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        links = []
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if href and href.startswith("http"):
                links.append(href)
            if len(links) >= 4:
                break

        if not links:
            return jsonify({"data": ["❌ No Indian English articles found for this query."]})

        summaries = []
        for url in links:
            try:
                article_res = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60])
                text = " ".join(content.split())
                if len(text.split()) >= 150:
                    domain = url.split("/")[2].replace("www.", "")
                    summaries.append(f"According to {domain}:\n{text[:2000]}")
            except Exception:
                continue

        if not summaries:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable content."]})

        return jsonify({"data": summaries})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
