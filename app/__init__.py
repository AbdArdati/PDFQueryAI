from flask import Flask
__version__ = '1.0.0-beta'

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)

    # Additional configuration if needed

    return app
