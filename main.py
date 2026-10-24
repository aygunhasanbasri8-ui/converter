import os

import uvicorn

if __name__ == "__main__":
    # Varsayılan bilerek yalnızca yerel; konteyner içinde 0.0.0.0 gerekiyor, port
    # yayınlanırken yine 127.0.0.1'e bağlanmalı (README > Docker).
    host = os.environ.get("CONVERTER_HOST", "127.0.0.1")
    port = int(os.environ.get("CONVERTER_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, log_level="warning")
