from django.contrib.admin import AdminSite
# site_admin/admin_site.py
MODEL_ORDER = [
    "core.DiretoriaEnsino","core.Diretor","core.Escola","core.PeriodoLetivo",
    "core.Bimestre","core.Turma","core.Disciplina","core.Professor",
    "core.Aluno","core.Frequencia","core.Avaliacao",
]
APP_ORDER = ["core", "auth", "admin"]

def _mkey(label: str):
    try: return MODEL_ORDER.index(label)
    except ValueError: return len(MODEL_ORDER) + 1

class MyAdminSite(AdminSite):
    site_header = "DIÁRIO DE CLASSE DIGITAL"

    # ✅ Django 4.2+: precisa aceitar app_label opcional
    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label=app_label)

        for app in apps:
            app_label_cur = app.get("app_label", "")
            models = app.get("models", [])
            def sort_model_key(m):
                object_name = m.get("object_name") or m.get("model_name") or m.get("name") or ""
                return _mkey(f"{app_label_cur}.{object_name}" if app_label_cur and object_name else "")
            models.sort(key=sort_model_key)

        if app_label is None:  # só reordenar no overview
            def sort_app_key(a):
                lbl = a.get("app_label", "")
                try: return APP_ORDER.index(lbl)
                except ValueError: return 999
            apps.sort(key=sort_app_key)

        return apps