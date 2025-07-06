from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

router = APIRouter()

templates = Jinja2Templates(directory="views")

# @router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "erro": None})

# @router.post("/login")
async def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    # Envia para /token
    async with httpx.AsyncClient() as client:
        response = await client.post("https://fiap-mle-challenge1-git-main-0verthrives-projects.vercel.app/token", data={"username": username, "password": password})
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        redirect = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        redirect.set_cookie("access_token", token)
        return redirect
    else:
        return templates.TemplateResponse("login.html", {"request": request, "erro": "Usuário ou senha inválidos"})

# @router.get("/")
async def home(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get("https://fiap-mle-challenge1-git-main-0verthrives-projects.vercel.app/users/me", headers=headers)

    if response.status_code != 200:
        return RedirectResponse(url="/login")

    user = response.json()
    return templates.TemplateResponse("home.html", {"request": request, "user": user})
