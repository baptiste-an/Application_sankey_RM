from waitress import serve
from index import (
    app,
)  # Make sure 'index' is your main file and 'app' is the Dash instance
import os

if __name__ == "__main__":
    port = int(
        os.environ.get("PORT", 8050)
    )  # Utilise le port fourni par Render ou 8050 par défaut
    app.run(host="0.0.0.0", port=port)
