from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)

    # Additional configuration if needed

    return app
