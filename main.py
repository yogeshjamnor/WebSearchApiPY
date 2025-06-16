from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Each source has a scraper function
def scrape_news18(query):
    url = f"https://www.news18.com/search/?q={query}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("div.search-listing li a")
        links = [a["href"] for a in articles if a["href"].startswith("http")][:2]

        results = []
        for link in links:
            article = requests.get(link, headers=HEADERS, timeout=10)
            article_soup = BeautifulSoup(article.text, "html.parser")
            paragraphs = article_soup.find_all("p")
            content = "\n".join([
                p.get_text(strip=True)
                for p in paragraphs if len(p.get_text(strip=True)) > 80 and p.get_text().isascii()
            ])
            summary = " ".join(content.split()[:400])
            if summary:
                results.append(f"According to news18.com:\n{summary}")
        return results
    except:
        return []

def scrape_ndtv(query):
    url = f"https://www.ndtv.com/search?searchtext={query}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("div.new_search_content div.searchTitle a")
        links = [a["href"] for a in articles if a["href"].startswith("http")][:2]

        results = []
        for link in links:
            article = requests.get(link, headers=HEADERS, timeout=10)
            article_soup = BeautifulSoup(article.text, "html.parser")
            paragraphs = article_soup.find_all("p")
            content = "\n".join([
                p.get_text(strip=True)
                for p in paragraphs if len(p.get_text(strip=True)) > 80 and p.get_text().isascii()
            ])
            summary = " ".join(content.split()[:400])
            if summary:
                results.append(f"According to ndtv.com:\n{summary}")
        return results
    except:
        return []

def scrape_indiatoday(query):
    url = f"https://www.indiatoday.in/search?search={query}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("div.search-result a")
        links = [a["href"] for a in articles if a["href"].startswith("http")][:2]

        results = []
        for link in links:
            article = requests.get(link, headers=HEADERS, timeout=10)
            article_soup = BeautifulSoup(article.text, "html.parser")
            paragraphs = article_soup.find_all("p")
            content = "\n".join([
                p.get_text(strip=True)
                for p in paragraphs if len(p.get_text(strip=True)) > 80 and p.get_text().isascii()
            ])
            summary = " ".join(content.split()[:400])
            if summary:
                results.append(f"According to indiatoday.in:\n{summary}")
        return results
    except:
        return []

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    combined_results = (
        scrape_news18(query) +
        scrape_ndtv(query) +
        scrape_indiatoday(query)
    )

    if not combined_results:
        return jsonify({"data": ["❌ No live Indian articles found for that query."]})

    return jsonify({"data": combined_results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
