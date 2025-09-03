# site_admin/adminapps.py
from django.contrib.admin.apps import AdminConfig

class MyAdminConfig(AdminConfig):
    # ✅ a classe está em admin_site.py, não em admin.py
    default_site = 'site_admin.admin_site.MyAdminSite'
