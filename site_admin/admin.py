# site_admin/admin.py
from django.contrib import admin
from site_admin.models import HeroContent, FeatureBlock  

@admin.register(FeatureBlock)
class FeatureBlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'description')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Adicione, edite ou exclua uma notícia no site'
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(HeroContent)
class HeroContentAdmin(admin.ModelAdmin):
    list_display = ('title',)

    def has_add_permission(self, request):
            return HeroContent.objects.count() < 3

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Crie um ou até três slides para a Home page do site'
        return super().changelist_view(request, extra_context=extra_context)
        