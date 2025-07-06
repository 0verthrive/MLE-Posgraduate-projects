from fastapi import FastAPI
from routers import auth, login, tables

app = FastAPI()
# app.include_router(login.router)
# app.include_router(auth.router)
app.include_router(tables.router)

