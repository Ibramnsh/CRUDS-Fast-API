from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uuid
import os

# Pastikan direktori templates dan static ada
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Data model
class Person(BaseModel):
    id: str
    nama: str
    email: str
    pekerjaan: str

# Database dalam memory
database: List[Person] = []

# Lifespan: menggantikan on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tambahkan sample data saat startup
    database.append(Person(id=str(uuid.uuid4()), nama="John Doe", email="john@example.com", pekerjaan="Developer"))
    database.append(Person(id=str(uuid.uuid4()), nama="Jane Smith", email="jane@example.com", pekerjaan="Designer"))
    database.append(Person(id=str(uuid.uuid4()), nama="Bob Johnson", email="bob@example.com", pekerjaan="Manager"))
    
    yield  # Aplikasi berjalan
    
    # Bisa tambahkan kode saat shutdown di sini jika perlu
    print("Aplikasi dimatikan.")

# Inisialisasi FastAPI dengan lifespan
app = FastAPI(lifespan=lifespan)

# Set up templates dan static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fungsi helper
def get_person_by_id(person_id: str):
    for person in database:
        if person.id == person_id:
            return person
    return None

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_all(request: Request, search: Optional[str] = None, message: Optional[str] = None):
    if search:
        filtered_data = [p for p in database if search.lower() in p.nama.lower() or search.lower() in p.email.lower()]
        return templates.TemplateResponse("index.html", {"request": request, "people": filtered_data, "search": search, "message": message})
    return templates.TemplateResponse("index.html", {"request": request, "people": database, "message": message})

@app.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create")
async def create_person(request: Request, nama: str = Form(...), email: str = Form(...), pekerjaan: str = Form(...)):
    person_id = str(uuid.uuid4())
    new_person = Person(id=person_id, nama=nama, email=email, pekerjaan=pekerjaan)
    database.append(new_person)
    return RedirectResponse(url="/?message=Data berhasil ditambahkan", status_code=303)

@app.get("/edit/{person_id}", response_class=HTMLResponse)
async def edit_form(request: Request, person_id: str):
    person = get_person_by_id(person_id)
    if not person:
        return RedirectResponse(url="/?message=Data tidak ditemukan", status_code=303)
    return templates.TemplateResponse("edit.html", {"request": request, "person": person})

@app.post("/edit/{person_id}")
async def edit_person(request: Request, person_id: str, nama: str = Form(...), email: str = Form(...), pekerjaan: str = Form(...)):
    person = get_person_by_id(person_id)
    if not person:
        return RedirectResponse(url="/?message=Data tidak ditemukan", status_code=303)
    
    # Update data
    for i, p in enumerate(database):
        if p.id == person_id:
            database[i] = Person(id=person_id, nama=nama, email=email, pekerjaan=pekerjaan)
            break
    
    return RedirectResponse(url=f"/?message=Data {nama} berhasil diperbarui", status_code=303)

@app.get("/delete/{person_id}")
async def delete_person(person_id: str):
    person = get_person_by_id(person_id)
    if not person:
        return RedirectResponse(url="/?message=Data tidak ditemukan", status_code=303)
    
    # Delete data
    global database
    database = [p for p in database if p.id != person_id]
    
    return RedirectResponse(url=f"/?message=Data berhasil dihapus", status_code=303)

# Jalankan aplikasi
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
