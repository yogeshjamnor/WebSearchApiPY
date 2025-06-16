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

    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://html.duckduckgo.com/html?q={query}+site:news18.com+OR+site:ndtv.com+OR+site:hindustantimes.com+OR+site:aljazeera.com"

    try:
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        # DuckDuckGo sometimes returns in .result__url or inside <a>
        results_links = soup.select("a.result__a")
        if not results_links:
            return jsonify({"error": "No search results found (selector failed)."}), 404

        links = []
        for a in results_links:
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
                long_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
                if not long_paragraphs:
                    continue
                content = "\n".join(long_paragraphs)
                summary = " ".join(content.split()[:400])
                source = link.split("/")[2].replace("www.", "")
                results.append(f"According to {source}:\n{summary}")
            except Exception as e:
                print(f"Error scraping {link}: {e}")
                continue

        if not results:
            return jsonify({"error": "No articles could be parsed."}), 500

        return jsonify({"data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
