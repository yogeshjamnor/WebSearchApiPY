from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# List of Indian news sites to search directly
NEWS_SITES = {
    "ndtv": "https://www.ndtv.com/search?searchtext=",
    "news18": "https://www.news18.com/search/?searchText=",
    "hindustantimes": "https://www.hindustantimes.com/search?q=",
    "indiatoday": "https://www.indiatoday.in/search?q=",
    "timesofindia": "https://timesofindia.indiatimes.com/topic/",
    "thehindu": "https://www.thehindu.com/search/?q=",
    "zeenews": "https://zeenews.india.com/tags/",
}

headers = {
    "User-Agent": "Mozilla/5.0"
}

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    results = []

    for name, base_url in NEWS_SITES.items():
        try:
            print(f"Searching {name}...")
            if name == "timesofindia" or name == "zeenews":
                search_url = base_url + query.replace(" ", "-")
            else:
                search_url = base_url + query.replace(" ", "+")

            res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            # Find article links
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "http" not in href:
                    href = base_url.split("/search")[0] + href
                if href.startswith("http") and name in href:
                    links.append(href)
                if len(links) >= 2:
                    break

            # Fetch summaries
            for link in links:
                try:
                    article = requests.get(link, headers=headers, timeout=10)
                    article_soup = BeautifulSoup(article.text, "html.parser")
                    paras = article_soup.find_all("p")
                    content = "\n".join(
                        [p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 50]
                    )
                    summary = " ".join(content.split()[:400])
                    if summary:
                        results.append(f"According to {name}.com:\n{summary}")
                except:
                    continue
        except Exception as e:
            continue

    if not results:
        return jsonify({"data": ["❌ No Indian news articles found for that keyword."]})

    return jsonify({"data": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
