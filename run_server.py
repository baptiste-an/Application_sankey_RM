from waitress import serve
from index import (
    app,
)  # Make sure 'index' is your main file and 'app' is the Dash instance

if __name__ == "__main__":
    serve(app.server, host="0.0.0.0", port=8050)
