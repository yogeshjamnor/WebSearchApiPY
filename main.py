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
    search_url = f"https://html.duckduckgo.com/html/?q={query}"

    try:
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        links = []
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                links.append(href)
            if len(links) >= 3:
                break

        results = []
        for link in links:
            try:
                article_res = requests.get(link, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                paragraphs = article_soup.find_all("p")
                content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 80])
                summary = " ".join(content.split()[:800])  # approx A4 size
                source = link.split("/")[2].replace("www.", "")
                if summary:
                    results.append(f"According to {source}:\n{summary}")
            except Exception as e:
                continue

        return jsonify({"data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)
