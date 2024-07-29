from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import home, invoices, leftovers, settings

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home.router)
app.include_router(invoices.router)
app.include_router(leftovers.router)
app.include_router(settings.router, prefix="/settings")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
