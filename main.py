from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
EXCLUDED_DOMAINS = ["wikipedia.org", "britannica.com", "youtube.com", "facebook.com", "instagram.com"]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    try:
        search_url = f"https://www.bing.com/search?q={query}+site:.in"
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href")
            if href and href.startswith("http"):
                domain = href.split("/")[2].replace("www.", "")
                if not any(domain.endswith(ex) for ex in EXCLUDED_DOMAINS):
                    links.append(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No valid Indian English news links found."]})

        summaries = []
        for link in links:
            try:
                page = requests.get(link, headers=HEADERS, timeout=10)
                article = BeautifulSoup(page.text, "html.parser")

                # Remove non-readable sections
                for tag in article(['script', 'style', 'footer', 'nav', 'aside', 'form']):
                    tag.decompose()

                # Grab all <p> tags with decent content
                paragraphs = article.find_all('p')
                content = [p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 60]
                text = "\n".join(content[:20])  # limit to ~20 paragraphs

                if text:
                    domain = link.split("/")[2].replace("www.", "")
                    summaries.append(f"According to {domain}:\n{text}")
            except:
                continue

        if summaries:
            return jsonify({"data": summaries})
        else:
            return jsonify({"data": ["❌ Articles found, but couldn't extract readable content."]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
