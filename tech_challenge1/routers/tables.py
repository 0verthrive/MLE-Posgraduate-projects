from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from routers.auth import fake_decode_token
from data_extraction.data_extraction import Extraction
from fastapi.templating import Jinja2Templates

# Define onde os templates HTML estão localizados
templates = Jinja2Templates(directory="views")

router = APIRouter()

# Função para buscar dados de acordo com a origem
def requests(option, ano, columns: list):
    ext = Extraction()
    try:
        print("try get of the site")
        return ext.request_site(option, ano)
    except:
        print("exception request, get of the csv")
        return ext.request_csv(option, ano, columns)

# Verifica o usuário autenticado baseado no cookie
# def get_current_user(request: Request):
#     token = request.cookies.get("access_token")
#     if not token:
#         return None
#     user = fake_decode_token(token)
#     if not user or getattr(user, "disabled", False):
#         return None
#     return user

# Rota protegida com checagem de autenticação
@router.get("/producao/", response_class=HTMLResponse)
def producao(request: Request, ano: str = "2023"):
    # user = get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/login", status_code=302)
    
    option = "Producao"
    columns = ['Produto', "Quantidade (L.)"]
    dados = requests(option, ano, columns)

    return templates.TemplateResponse("product.html", {
        "request": request,
        "tabela_html": dados,
        "ano": ano
    })


@router.get("/comercializacao/", response_class=HTMLResponse)
def comercializacao(request: Request, ano: str = "2023"):
    # user = get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/login")
    
    option = "Comercializacao"
    columns = ['Produto', 'Quantidade (Kg)']
    dados = requests(option, ano, columns)

    return templates.TemplateResponse("product.html", {
        "request": request,
        "tabela_html": dados,
        "ano": ano
    })

@router.get("/exportacao/{suboption}", response_class=HTMLResponse)
def exportacao(request: Request, suboption: str, ano: str = "2023"):
    # user = get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/login")
    
    columns = ["Países", "Quantidade (Kg)", "Valor (US$)"]
    dados = requests(suboption, ano, columns)

    return templates.TemplateResponse("product.html", {
        "request": request,
        "tabela_html": dados,
        "ano": ano
    })

@router.get("/importacao/{suboption}", response_class=HTMLResponse)
def importacao(request: Request, suboption: str, ano: str = "2023"):
    # user = get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/login")
    
    columns = ["Países", "Quantidade (Kg)", "Valor (US$)"]
    dados = requests(suboption, ano, columns)

    return templates.TemplateResponse("product.html", {
        "request": request,
        "tabela_html": dados,
        "ano": ano
    })

@router.get("/processamento/{suboption}", response_class=HTMLResponse)
def processamento(request: Request, suboption: str, ano: str = "2023"):
    # user = get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/login")
    
    columns = ["Cultivar", "Quantidade (Kg)"]
    dados = requests(suboption, ano, columns)

    return templates.TemplateResponse("product.html", {
        "request": request,
        "tabela_html": dados,
        "ano": ano
    })

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
