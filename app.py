from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)  # Turn on debugging mode for development
    print("Flask app is running on http://127.0.0.1:5000")
