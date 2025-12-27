from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Imports diretos para evitar problemas de módulos
import sys
import os
backend_path = os.path.dirname(__file__)
sys.path.insert(0, backend_path)

from config import ALLOWED_ORIGINS
from routers.api import router as api_router
from routers.blog import router as blog_router
from routers.admin import router as admin_router
from routers.payments import router as payments_router

# Criar aplicação FastAPI
app = FastAPI()

# Middleware CORS - CORRIGIDO: quando allow_credentials=True, NÃO usar allow_origins=["*"]
# Deve usar a lista explícita de origens permitidas por segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Lista explícita, não ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(api_router, prefix="/api")
app.include_router(blog_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(payments_router, prefix="/api")

# Middleware para debug de CORS (opcional)
@app.middleware("http")
async def debug_cors_middleware(request: Request, call_next):
    """Middleware para debug de requisições CORS"""
    origin = request.headers.get('origin')
    if origin:
        print(f"Request origin: {origin}")
    response = await call_next(request)
    return response

# Rota de saúde
@app.get("/")
def health_check():
    """Verificação de saúde da API"""
    return {"status": "ok", "service": "TramaGrid Backend"}

# Tratamento global de erros CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tratamento global de exceções"""
    print(f"Erro global: {exc}")
    # Permite que o FastAPI lide com CORS adequadamente
    raise exc
