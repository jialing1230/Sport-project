from flask import Flask, render_template
from app.routers.auth import auth_bp
from app.routers.activity import activity_bp
from app.routers.memeber import member_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(member_bp)

    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route('/login', endpoint='login_html')
    def login_page():
        return render_template('login.html')

    @app.route('/members')
    def members_page():
        return render_template('member_management.html')
    
    @app.route('/profiles')
    def profiles():
        return render_template('profiles.html')
    
    
    return app
