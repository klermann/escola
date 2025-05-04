# site_admin/admin.py
from django.contrib import admin
from site_admin.models import HeroContent, FeatureBlock  

@admin.register(FeatureBlock)
class FeatureBlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'description')

@admin.register(HeroContent)
class HeroContentAdmin(admin.ModelAdmin):
    list_display = ('title',)
    def has_add_permission(self, request):
            return HeroContent.objects.count() < 3
        