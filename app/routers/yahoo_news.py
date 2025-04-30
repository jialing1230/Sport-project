from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup

yahoo_news_bp = Blueprint('yahoo_news_bp', __name__)

@yahoo_news_bp.route("/api/yahoo-sports-news")
def yahoo_sports_news():
    url = "https://tw.news.yahoo.com/sports/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("li.js-stream-content")[:5]

        result = []
        for item in items:
            title_tag = item.select_one("h3")
            summary_tag = item.select_one("p")
            link_tag = item.select_one("a")

            if title_tag and summary_tag and link_tag:
                result.append({
                    "title": title_tag.text.strip(),
                    "summary": summary_tag.text.strip(),
                    "url": "https://tw.news.yahoo.com" + link_tag['href']
                })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
