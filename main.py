from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "API is Live"

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    search_url = f"https://lite.duckduckgo.com/lite?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        search_res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_res.text, "html.parser")

        results = []
        for link in soup.select("a"):
            title = link.text.strip()
            href = link.get("href")
            if href and "http" in href:
                clean_link = href.split("&rut=")[0].replace("/l/?uddg=", "")
                article_url = requests.utils.unquote(clean_link)

                # Visit the article and extract summary
                try:
                    article_res = requests.get(article_url, headers=headers, timeout=5)
                    article_soup = BeautifulSoup(article_res.text, "html.parser")

                    # Grab first paragraph or meta description
                    paragraph = article_soup.find("p")
                    description = paragraph.text.strip() if paragraph else ""

                    if not description:
                        meta = article_soup.find("meta", attrs={"name": "description"})
                        if meta and meta.get("content"):
                            description = meta["content"].strip()

                    results.append({
                        "title": title,
                        "link": article_url,
                        "summary": description if description else "No summary available.",
                        "source": urlparse(article_url).hostname.replace("www.", "")
                    })
                except Exception as article_err:
                    results.append({
                        "title": title,
                        "link": article_url,
                        "summary": "Could not fetch article.",
                        "source": urlparse(article_url).hostname.replace("www.", "")
                    })

            if len(results) >= 5:
                break

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
