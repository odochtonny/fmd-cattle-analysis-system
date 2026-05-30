import os
import traceback
import uvicorn

try:
    print("Starting Render backend...")
    print("PORT =", os.environ.get("PORT"))
    import app.main
    print("Imported app.main successfully")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        log_level="debug",
    )

except Exception:
    print("STARTUP ERROR:")
    traceback.print_exc()
    raise