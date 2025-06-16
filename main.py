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
    search_url = f"https://www.bing.com/search?q={query}"

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")
        result_links = []

        for li in soup.select("li.b_algo h2 a"):
            href = li.get("href")
            if href and href.startswith("http"):
                result_links.append(href)
            if len(result_links) >= 3:
                break

        if not result_links:
            return jsonify({"data": ["❌ No articles found for that query."]})

        results = []
        for url in result_links:
            try:
                article_res = requests.get(url, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 60])
                summary = " ".join(content.split()[:400])
                source = url.split("/")[2].replace("www.", "")
                if summary:
                    results.append(f"According to {source}:\n{summary}")
            except:
                continue

        if not results:
            return jsonify({"data": ["❌ No readable content found in the articles."]})
        return jsonify({"data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

