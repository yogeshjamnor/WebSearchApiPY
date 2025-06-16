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

    try:
        search_url = f"https://www.bing.com/search?q={query}"
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Check for direct answers
        selectors = [
            ".b_focusTextLarge",    # Big bold answer
            ".b_focusTextMedium",   # Medium bold answer
            ".b_vPanel .b_snippet", # Knowledge card
            ".b_subModule",         # Sub modules
        ]
        for sel in selectors:
            element = soup.select_one(sel)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return jsonify({"data": [f"Summary:\n{text}"]})

        # Fallback: search results
        snippets = soup.select("li.b_algo")
        results = []
        for item in snippets:
            title_tag = item.select_one("h2 a")
            desc_tag = item.select_one(".b_caption p")
            if not title_tag or not desc_tag:
                continue
            link = title_tag.get("href", "")
            if any(x in link for x in ["wikipedia.org", "britannica.com"]):
                continue
            site = link.split("/")[2].replace("www.", "")
            title = title_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True)
            if desc:
                results.append(f"According to {site}:\n{title}\n{desc}")
            if len(results) >= 3:
                break

        if results:
            return jsonify({"data": results})
        else:
            return jsonify({"data": ["❌ No relevant summary or results found."]})

    except Exception as e:
        return jsonify({"error": f"❌ Error: {str(e)}"]}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
