# app/routers/map.py

from flask import Blueprint, render_template
import os

map_bp = Blueprint("map", __name__)

@map_bp.route("/map")
def google_map():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    return render_template("map.html", api_key=api_key)