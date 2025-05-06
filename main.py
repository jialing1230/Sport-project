from app.app import create_app
from app.routers.map import map_bp
app = create_app()
app.register_blueprint(map_bp)
if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=5002)
