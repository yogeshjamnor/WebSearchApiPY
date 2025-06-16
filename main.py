from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    headers = {"User-Agent": "Mozilla/5.0"}

    # ✅ Indian news sites
    allowed_sites = [
        "ndtv.com", "news18.com", "hindustantimes.com", "indiatoday.in",
        "timesofindia.indiatimes.com", "thehindu.com", "zeenews.india.com",
        "firstpost.com", "livemint.com", "deccanherald.com"
    ]

    site_filter = "+OR+".join(f"site:{site}" for site in allowed_sites)
    search_url = f"https://www.bing.com/search?q={query}+{site_filter}"

    try:
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        result_links = []
        seen = set()

        # 🔍 Collect up to 10 links from allowed domains
        for tag in soup.select("li.b_algo h2 a"):
            href = tag.get("href")
            if href and href.startswith("http"):
                domain = href.split("/")[2].replace("www.", "")
                if any(site in domain for site in allowed_sites) and href not in seen:
                    result_links.append(href)
                    seen.add(href)
            if len(result_links) >= 10:
                break

        if not result_links:
            return jsonify({"data": ["❌ No Indian news articles found for that query."]})

        results = []
        for url in result_links:
            try:
                article_res = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([
                    p.get_text(strip=True)
                    for p in paragraphs if len(p.get_text()) > 60
                ])
                summary = " ".join(content.split()[:400])
                source = url.split("/")[2].replace("www.", "")
                if summary and len(summary) > 200:
                    results.append(f"According to {source}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ No readable Indian news content found."]})

        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
