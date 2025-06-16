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
    search_url = f"https://html.duckduckgo.com/html?q={query}+site:news18.com+OR+site:hindustantimes.com+OR+site:aljazeera.com+OR+site:ndtv.com"

    try:
        search_response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        # Get top 3 article links
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

                # Extract long meaningful paragraphs
                paragraphs = article_soup.find_all("p")
                long_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 80]
                full_text = "\n\n".join(long_paragraphs)

                # Shorten only if it's too long; keep as full paragraph text
                if full_text:
                    summary = full_text.strip().split('\n\n')
                    if len(summary) > 10:
                        summary = summary[:10]  # limit to 10 paragraphs (~20-30 lines)
                    joined = "\n\n".join(summary)
                    source = link.split("/")[2].replace("www.", "")
                    results.append(f"According to {source}:\n\n{joined}")
            except Exception as e:
                print(f"Failed to fetch article: {link}\nError: {e}")
                continue

        if not results:
            return jsonify({"error": "No detailed news summaries found."}), 404

        return jsonify({"data": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
