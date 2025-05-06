# app/routers/map.py
from flask import Blueprint, render_template, request
import os

map_bp = Blueprint("map", __name__)

@map_bp.route("/news")
def google_map():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return render_template("news.html", api_key=api_key)
@map_bp.route("/home")
def home_page():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    member_id = request.args.get("member_id")  # ⬅️ 接住 URL 上的 member_id
    return render_template("home.html", api_key=api_key, member_id=member_id)