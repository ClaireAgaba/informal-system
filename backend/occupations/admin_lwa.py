from django.contrib import admin
from .models import ModuleLWA


@admin.register(ModuleLWA)
class ModuleLWAAdmin(admin.ModelAdmin):
    list_display = ['lwa_name', 'get_module_code', 'get_module_name', 'created_at']
    list_filter = ['module__occupation', 'created_at']
    search_fields = ['lwa_name', 'module__module_code', 'module__module_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['module']
    
    fieldsets = (
        ('LWA Information', {
            'fields': ('module', 'lwa_name'),
            'description': 'Enter the Learning Working Assignment name'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('module', 'module__occupation')
    
    def get_module_code(self, obj):
        """Display module code"""
        return obj.module.module_code
    get_module_code.short_description = 'Module Code'
    get_module_code.admin_order_field = 'module__module_code'
    
    def get_module_name(self, obj):
        """Display module name"""
        return obj.module.module_name
    get_module_name.short_description = 'Module Name'
    get_module_name.admin_order_field = 'module__module_name'
