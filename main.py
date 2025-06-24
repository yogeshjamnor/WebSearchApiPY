from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
EXCLUDED_DOMAINS = ["wikipedia.org", "youtube.com", "facebook.com", "instagram.com", "britannica.com"]

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    try:
        encoded_query = quote(query + " news")
        search_url = f"https://www.bing.com/news/search?q={encoded_query}"
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.select("a.title"):
            href = a.get("href")
            if href and href.startswith("http"):
                domain = href.split("/")[2].replace("www.", "")
                if not any(ex in domain for ex in EXCLUDED_DOMAINS):
                    links.append(href)
            if len(links) >= 5:
                break

        if not links:
            return jsonify({"data": ["❌ No valid news links found. Try different keywords."]})

        summaries = []
        for link in links:
            try:
                page = requests.get(link, headers=HEADERS, timeout=10)
                article = BeautifulSoup(page.text, "html.parser")

                for tag in article(['script', 'style', 'footer', 'nav', 'aside', 'form']):
                    tag.decompose()

                paragraphs = article.find_all('p')
                content = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if 60 < len(text) < 1000 and not any(x in text.lower() for x in ['cookie', 'subscribe']):
                        content.append(text)

                final_text = "\n\n".join(content[:20])
                if final_text:
                    domain = link.split("/")[2].replace("www.", "")
                    summaries.append(f"📌 According to {domain}:\n\n{final_text}\n\n🔗 {link}")
            except Exception as e:
                continue

        if summaries:
            return jsonify({"data": summaries})
        else:
            return jsonify({"data": ["❌ Articles found, but no readable summaries extracted."]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
