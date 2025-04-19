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
    
    @app.route("/register-test")
    def register_test():
        return render_template("register_test.html")

    @app.route("/register")
    def register():
        return render_template("register.html")
    
    @app.route('/members')
    def members_page():
        return render_template('member_management.html')

    return app
