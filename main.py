from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

HEADERS = {"User-Agent": "Mozilla/5.0"}
EXCLUDED_DOMAINS = ["wikipedia.org", "britannica.com"]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    try:
        search_url = f"https://www.bing.com/search?q={query}"
        search_res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        # Try to extract Bing Answer Box (summary-style)
        for selector in [".b_focusTextLarge", ".b_focusTextMedium", ".b_vPanel .b_snippet"]:
            element = soup.select_one(selector)
            if element:
                summary = element.get_text(strip=True)
                if summary:
                    return jsonify({"data": [f"Summary:\n{summary}"]})

        # Fallback: parse normal search snippets
        snippets = soup.select("li.b_algo")
        results = []
        seen_sites = set()
        seen_texts = set()

        for snippet in snippets:
            title_tag = snippet.select_one("h2 a")
            desc_tag = snippet.select_one(".b_caption p")
            if not title_tag or not desc_tag:
                continue

            link = title_tag.get("href", "")
            domain = link.split("/")[2].replace("www.", "") if "//" in link else ""

            # Exclude Wikipedia and Britannica results from the search
            if any(domain.endswith(ex) for ex in EXCLUDED_DOMAINS):
                continue

            # Avoid duplicates
            if domain in seen_sites:
                continue

            title = title_tag.get_text(strip=True)
            desc = desc_tag.get_text(strip=True)
            combined_text = f"{title}\n{desc}"

            # Avoid repeated descriptions
            if combined_text in seen_texts:
                continue

            seen_sites.add(domain)
            seen_texts.add(combined_text)

            if title and desc:
                results.append(f"According to {domain}:\n{title}\n{desc}")

            # Limit results to top 4 for better response
            if len(results) >= 4:
                break

        if results:
            return jsonify({"data": results})
        else:
            return jsonify({"data": ["❌ No relevant summary or results found."]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
