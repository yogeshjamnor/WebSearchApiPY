from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

HEADERS = {"User-Agent": "Mozilla/5.0"}

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    # Attempt to use Google Knowledge Panel or Bing answer box
    try:
        # Prefer Bing for easier parsing of direct answers
        search_url = f"https://www.bing.com/search?q={query}"
        search_res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        # Check for Bing answer box or knowledge panel
        direct_answer = soup.select_one(".b_focusTextLarge")
        if not direct_answer:
            direct_answer = soup.select_one(".b_vPanel .b_snippet")
        if not direct_answer:
            direct_answer = soup.select_one(".b_focusTextMedium")

        if direct_answer:
            summary = direct_answer.get_text(strip=True)
            return jsonify({"data": [f"Summary:
{summary}"]})

        # Fallback to general snippets if direct answer not found
        snippets = soup.select("li.b_algo")
        results = []
        for snippet in snippets[:3]:
            title_tag = snippet.select_one("h2 a")
            desc_tag = snippet.select_one(".b_caption p")
            if title_tag and desc_tag:
                title = title_tag.get_text(strip=True)
                desc = desc_tag.get_text(strip=True)
                link = title_tag.get("href")
                results.append(f"According to {link.split('/')[2].replace('www.', '')}:
{title}\n{desc}")

        if results:
            return jsonify({"data": results})
        else:
            return jsonify({"data": ["❌ No summary or snippet found for that query."]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
