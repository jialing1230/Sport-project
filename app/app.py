import os
from flask import Flask, render_template, request, redirect, url_for
from app.routers.auth import auth_bp
from app.routers.activity import activity_bp
from app.routers.memeber import member_bp
from app.routers.preference import preference_bp
from app.routers.yahoo_news import yahoo_news_bp
from app.services.scheduler import start_scheduler
#from app.routers.class_ import class_bp


def create_app():
    app = Flask(__name__)

    # 1. 定義並建立上傳目錄
    upload_folder = os.path.join(app.root_path, "static", "avatars")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    # 2. 註冊 API Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(preference_bp)
    app.register_blueprint(yahoo_news_bp)
    #app.register_blueprint(class_bp) 


    # 前端頁面路由
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", endpoint="login_html")
    def login_page():
        return render_template("login.html")

    @app.route("/members")
    def members_page():
        return render_template("member_management.html")

    @app.route("/activities_overview")
    def activities_overview_page():
        return render_template("activities_overview.html")

    @app.route("/profiles")
    def profiles_page():
        # 從查詢參數取得 member_id
        member_id = request.args.get("member_id")
        if not member_id:
            # 如果缺少 member_id，導回登入頁面
            return redirect(url_for("login_html"))
        # 將 member_id 注入模板
        return render_template("profiles.html", member_id=member_id)

    @app.route("/preference")
    def user_preference_page():
        # 從查詢參數取得 member_id
        member_id = request.args.get("member_id")
        if not member_id:
            # 如果缺少 member_id，導回登入頁面
            return redirect(url_for("login_html"))
        # 將 member_id 注入模板
        return render_template("preference.html", member_id=member_id)

    @app.route("/create_activity")
    def create_activity_page():
        member_id = request.args.get("member_id")
        if not member_id:
            # 如果缺少 member_id，導回登入頁面
            return redirect(url_for("login_html"))
        # 將 member_id 注入模板
        return render_template("create_activity.html", member_id=member_id)

    @app.route("/activity")
    def activity_page():
        member_id = request.args.get("member_id")
        if not member_id:
            # 如果缺少 member_id，導回登入頁面
            return redirect(url_for("login_html"))
        # 將 member_id 注入模板
        return render_template("activity.html", member_id=member_id)

    @app.route("/profile_view")
    def profile_view():
        member_id = request.args.get("member_id")
        return render_template("profile_view.html", member_id=member_id)

    @app.route("/activity.details", endpoint="activity.details_html")
    def view_activity_page():
        return render_template("activity.details.html")
    
    @app.route("/create_class")
    def create_class_page():
        member_id = request.args.get("member_id")
        if not member_id:
            return redirect(url_for("login_html"))
        return render_template("create_class.html", member_id=member_id)

    @app.route("/member_view")
    def member_view():
        member_id = request.args.get("member_id")
        return render_template("member.html", member_id=member_id)

    start_scheduler()  # 啟動排程
    return app


