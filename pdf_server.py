"""Tiny static file server for Blueprint PDFs"""
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI()
PDF_DIR = "/opt/aetherlang-bot/blueprints"

@app.get("/blueprints/{filename}")
async def serve_pdf(filename: str):
    if not filename.endswith(".pdf"):
        return JSONResponse({"error": "Only PDF files"}, 400)
    path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "Not found"}, 404)
    return FileResponse(path, media_type="application/pdf", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9997)
