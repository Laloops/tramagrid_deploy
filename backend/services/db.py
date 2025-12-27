from supabase import create_client, Client
from datetime import datetime
# Import direto para evitar problemas de módulos
import sys
import os
backend_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Conexão global do Supabase Admin
supabase_admin: Client = None

def get_supabase_admin() -> Client:
    """Retorna a instância global do Supabase Admin"""
    return supabase_admin

def init_supabase_connection():
    """Inicializa a conexão com Supabase"""
    global supabase_admin
    try:
        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print("Supabase Admin conectado!")
        else:
            print("Variáveis do Supabase faltando no .env")
            supabase_admin = None
    except Exception as e:
        print(f"Erro ao conectar Supabase: {e}")
        supabase_admin = None

def get_posts():
    """Retorna posts do blog mais recentes primeiro"""
    try:
        res = supabase_admin.table('posts').select('*').eq('published', True).order('created_at', desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Erro ao buscar posts: {e}")
        return []

def get_post(slug: str):
    """Retorna um post específico pelo slug"""
    try:
        res = supabase_admin.table('posts').select('*').eq('slug', slug).single().execute()
        return res.data
    except Exception as e:
        print(f"Erro ao buscar post {slug}: {e}")
        return None

def create_post(post_data: dict):
    """Cria um novo post"""
    try:
        res = supabase_admin.table('posts').insert(post_data).execute()
        return {"ok": True, "data": res.data}
    except Exception as e:
        print(f"Erro ao criar post: {e}")
        raise Exception(str(e))

def delete_post(post_id: int):
    """Deleta um post"""
    try:
        supabase_admin.table('posts').delete().eq('id', post_id).execute()
        return {"ok": True}
    except Exception as e:
        print(f"Erro ao deletar post {post_id}: {e}")
        raise Exception(str(e))

def get_user_profile(user_id: str):
    """Busca o perfil do usuário"""
    try:
        res = supabase_admin.table('profiles').select('*').eq('id', user_id).single().execute()
        return res.data
    except Exception as e:
        print(f"Erro ao buscar perfil {user_id}: {e}")
        raise Exception(f"DB Error: {e}")

def update_user_credits(user_id: str, credits: int):
    """Atualiza os créditos do usuário"""
    try:
        supabase_admin.table('profiles').update({'credits': credits}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao atualizar créditos do usuário {user_id}: {e}")
        raise Exception(f"Update Error: {e}")

def get_admin_stats():
    """Retorna estatísticas do admin com contagens reais"""
    try:
        # Conta usuários
        res_users = supabase_admin.table('profiles').select('id', count='exact').execute()
        count_users = res_users.count if res_users.count else 0

        # Conta projetos
        res_projects = supabase_admin.table('projects').select('id', count='exact').execute()
        count_projects = res_projects.count if res_projects.count else 0

        # Estatísticas do dia (Visitas e Logins)
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
        print(f"Erro ao buscar stats: {e}")
        return {"total_users": 0, "total_projects": 0, "daily_visits": 0, "daily_logins": 0}

def increment_visit():
    """Incrementa contador de visitas"""
    try:
        if supabase_admin:
            supabase_admin.rpc('increment_visit').execute()
    except Exception as e:
        print(f"Erro ao incrementar visita: {e}")

def increment_login():
    """Incrementa contador de logins"""
    try:
        if supabase_admin:
            supabase_admin.rpc('increment_login').execute()
            return {"ok": True}
    except Exception as e:
        print(f"Erro ao incrementar login: {e}")
        return {"ok": False}

# Inicializar conexão na importação do módulo
init_supabase_connection()
