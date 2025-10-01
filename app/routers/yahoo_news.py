import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify

yahoo_news_bp = Blueprint("yahoo_news", __name__)

@yahoo_news_bp.route("/api/yahoo-sports-news")
def get_yahoo_sports_news():
    url = "https://tw.sports.yahoo.com/"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    seen = set()  # ✅ 用來記錄已經出現過的新聞連結

    for item in soup.select("li.js-stream-content, div.Pos\(r\)")[:30]:
        title_elem = item.select_one("h3")
        link_elem = item.select_one("a")
        summary_elem = item.select_one("p")
        img_elem = item.select_one("img")

        if not title_elem or not link_elem:
            continue

        title = title_elem.get_text(strip=True)
        url = link_elem["href"]
        summary = summary_elem.get_text(strip=True) if summary_elem else ""

        # Yahoo 有些連結是相對路徑，補全
        if url.startswith("/"):
            url = "https://tw.sports.yahoo.com" + url

        # ✅ 如果這則新聞已經出現過，就跳過
        if url in seen:
            continue
        seen.add(url)

        # ✅ 圖片邏輯
        image = None
        if img_elem:
            if img_elem.has_attr("data-src"):
                image = img_elem["data-src"]
            elif img_elem.has_attr("srcset"):
                image = img_elem["srcset"].split(",")[-1].split()[0]
            elif img_elem.has_attr("src"):
                image = img_elem["src"]

        if not image:
            image = "https://via.placeholder.com/300x200?text=No+Image"

        articles.append({
            "title": title,
            "url": url,
            "summary": summary,
            "image": image
        })

    return jsonify(articles)
