import os

from waitress import serve

from index import server


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    serve(server, host="0.0.0.0", port=port, threads=8)
