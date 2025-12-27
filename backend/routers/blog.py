from fastapi import APIRouter, HTTPException

# Imports com fallback para execução direta
try:
    from ..config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    from ..models import BlogPostModel
    from ..services.db import get_posts, get_post, create_post, delete_post, get_supabase_admin
except ImportError:
    # Fallback quando executado fora do pacote
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    from models import BlogPostModel
    from services.db import get_posts, get_post, create_post, delete_post, get_supabase_admin

router = APIRouter()

@router.get("/posts")
def list_posts():
    """Lista todos os posts publicados"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(500, "Serviço de banco de dados indisponível")

    return get_posts()

@router.get("/posts/{slug}")
def get_single_post(slug: str):
    """Retorna um post específico pelo slug"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(500, "Serviço de banco de dados indisponível")

    post = get_post(slug)
    if not post:
        raise HTTPException(404, "Post não encontrado")
    return post

@router.post("/posts")
def create_new_post(post: BlogPostModel):
    """Cria um novo post (requer autenticação admin)"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(500, "Serviço de banco de dados indisponível")

    try:
        return create_post(post.dict())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.delete("/posts/{post_id}")
def delete_existing_post(post_id: int):
    """Deleta um post (requer autenticação admin)"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(500, "Serviço de banco de dados indisponível")

    try:
        return delete_post(post_id)
    except Exception as e:
        raise HTTPException(400, str(e))