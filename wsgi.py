from app import create_app

# Create the app instance for gunicorn
app = create_app()

if __name__ == "__main__":
    # This is only for local development
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)