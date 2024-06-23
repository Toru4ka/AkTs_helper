from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import home, invoices, leftovers

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home.router)
app.include_router(invoices.router)
app.include_router(leftovers.router)