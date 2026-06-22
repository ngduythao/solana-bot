
from fastapi import FastAPI, Response
app=FastAPI(title="Solbot Dashboard (Combined)")

@app.get("/")
def index():
    return Response(content="<h1>Solbot Dashboard</h1><p>Use the main dashboard container.</p>", media_type="text/html")
