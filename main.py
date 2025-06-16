from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

# Trusted Indian English sources
indian_sites = [
    "ndtv.com", "timesofindia.indiatimes.com", "indiatoday.in", "hindustantimes.com",
    "news18.com", "thehindu.com", "indianexpress.com", "livemint.com", "deccanherald.com"
]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.bing.com/search?q={query}+site:" + "+OR+site:".join(indian_sites)

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
            return jsonify({"data": ["❌ No Indian English news links found."]})

        results = []
        for url in links:
            try:
                article = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article.text, "html.parser")

                # Collect content from multiple tag types
                raw_text = []
                for tag in article_soup.find_all(['p', 'span', 'article']):
                    text = tag.get_text(strip=True)
                    if text and len(text.split()) > 10:
                        raw_text.append(text)

                # Filter: remove duplicate and footer-like content
                paragraphs = list(dict.fromkeys(raw_text))  # remove duplicates
                clean_paragraphs = [p for p in paragraphs if "©" not in p and "cookie" not in p.lower()]
                full_text = " ".join(clean_paragraphs)

                # Truncate long results for frontend (400-500 words max)
                if len(full_text) > 300:
                    domain = url.split("/")[2].replace("www.", "")
                    result = f"According to {domain}:\n" + " ".join(full_text.split()[:400])
                    results.append(result)
            except Exception as e:
                continue

        if not results:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable content."]})
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
