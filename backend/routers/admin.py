from fastapi import APIRouter
from datetime import datetime

# Imports com fallback para execução direta
try:
    from ..config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    from ..services.db import get_supabase_admin
except ImportError:
    # Fallback quando executado fora do pacote
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
    from services.db import get_supabase_admin

router = APIRouter()

@router.get("/admin/stats")
def get_admin_stats():
    """Retorna estatísticas do admin com contagens reais"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"total_users": 0, "total_projects": 0, "daily_visits": 0, "daily_logins": 0}

    try:
        supabase_admin = get_supabase_admin()
        count_users = 0
        count_projects = 0

        # Contagens Totais
        if supabase_admin:
            res_u = supabase_admin.table('profiles').select('id', count='exact').execute()
            count_users = res_u.count if res_u.count else 0
            res_p = supabase_admin.table('projects').select('id', count='exact').execute()
            count_projects = res_p.count if res_p.count else 0

        # Estatísticas do Dia (Visitas e Logins)
        visits = 0
        logins = 0

        if supabase_admin:
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                res_stats = supabase_admin.table('daily_stats').select('*').eq('date', today).single().execute()
                if res_stats.data:
                    visits = res_stats.data.get('visits', 0)
                    logins = res_stats.data.get('logins', 0)
            except:
                pass

        return {
            "total_users": count_users,
            "total_projects": count_projects,
            "daily_visits": visits,
            "daily_logins": logins,
            "new_subs": 0  # Placeholder até implementar Stripe webhooks
        }
    except Exception as e:
        print(f"Stats Error: {e}")
        return {"total_users": 0, "total_projects": 0, "daily_visits": 0, "daily_logins": 0}

@router.post("/track/visit")
def track_visit():
    """Incrementa contador de visitas"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"ok": True}  # Retorna OK mesmo sem Supabase para não travar o front

    try:
        supabase_admin = get_supabase_admin()
        if supabase_admin:
            supabase_admin.rpc('increment_visit').execute()
        return {"ok": True}
    except Exception as e:
        print(f"Erro ao incrementar visita: {e}")
        # Retornamos OK mesmo com erro para não travar o front
        return {"ok": True}

@router.post("/track/login")
def track_login():
    """Incrementa contador de logins"""
    # Verificação de segurança: só executa se as credenciais do Supabase estiverem configuradas
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"ok": False}

    try:
        supabase_admin = get_supabase_admin()
        if supabase_admin:
            supabase_admin.rpc('increment_login').execute()
            return {"ok": True}
    except Exception as e:
        print(f"Erro ao incrementar login: {e}")
    return {"ok": False}