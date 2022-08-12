from uvicorn import run

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/qrcode/{id}", response_class=HTMLResponse)
async def show_qrcode(request: Request, id: int):
    path = f"qrcodes/{id}.png"
    return templates.TemplateResponse("qrcode.html", {"request": request, "qrcode_id": id, "path": path})

if __name__ == '__main__':
    run('main:app', reload=True, log_level="info")