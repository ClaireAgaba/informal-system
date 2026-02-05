from django.contrib import admin
from .models import Sector, Occupation, OccupationLevel, OccupationModule, OccupationPaper, ModuleLWA


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_occupations_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_occupations_count']
    
    fieldsets = (
        ('Sector Information', {
            'fields': ('name', 'description')
        }),
        ('Statistics', {
            'fields': ('get_occupations_count',),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_occupations_count(self, obj):
        """Display count of occupations"""
        return obj.get_occupations_count()
    get_occupations_count.short_description = 'Occupations Count'


class OccupationLevelInline(admin.TabularInline):
    model = OccupationLevel
    extra = 1
    fields = ['level_name', 'structure_type', 'formal_fee', 'workers_pas_base_fee', 
              'workers_pas_per_module_fee', 'modular_fee_single_module', 'modular_fee_double_module', 'is_active']
    verbose_name = 'Level'
    verbose_name_plural = 'Occupation Levels'


@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
    list_display = ['occ_code', 'occ_name', 'occ_category', 'sector', 'has_modular', 'get_levels_count', 'is_active', 'created_at']
    list_filter = ['occ_category', 'has_modular', 'is_active', 'sector', 'created_at']
    search_fields = ['occ_code', 'occ_name', 'sector__name']
    readonly_fields = ['created_at', 'updated_at', 'get_levels_count']
    autocomplete_fields = ['sector']
    inlines = [OccupationLevelInline]
    # Enable autocomplete for this model in other admins
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('occ_code', 'occ_name', 'occ_category', 'sector')
        }),
        ('Awards & Hours', {
            'fields': ('award', 'award_modular', 'contact_hours'),
            'description': 'Award titles used on transcripts. Modular award only applies if "Has Modular" is enabled.'
        }),
        ('Levels & Structure Type', {
            'fields': ('has_modular', 'get_levels_count'),
            'description': 'Tick if this occupation allows Modular registration (Level 1 only). Add levels below.'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('levels')
    
    def get_levels_count(self, obj):
        """Display count of levels"""
        return obj.get_levels_count()
    get_levels_count.short_description = 'Levels Count'


@admin.register(OccupationLevel)
class OccupationLevelAdmin(admin.ModelAdmin):
    list_display = ['get_occupation_code', 'get_occupation_name', 'level_name', 'structure_type', 
                    'formal_fee', 'workers_pas_base_fee', 'is_active', 'created_at']
    list_filter = ['structure_type', 'is_active', 'occupation__occ_category', 'created_at']
    search_fields = ['level_name', 'occupation__occ_code', 'occupation__occ_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['occupation']
    
    fieldsets = (
        ('Level Information', {
            'fields': ('occupation', 'level_name', 'structure_type'),
            'description': 'Define the level name and whether it contains modules or papers'
        }),
        ('Billing Information', {
            'fields': (
                'formal_fee',
                'workers_pas_base_fee',
                'workers_pas_per_module_fee',
                'modular_fee_single_module',
                'modular_fee_double_module'
            ),
            'description': 'Set the fees for different registration types (all amounts in UGX)'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('occupation')
    
    def get_occupation_code(self, obj):
        """Display occupation code"""
        return obj.occupation.occ_code
    get_occupation_code.short_description = 'Occupation Code'
    get_occupation_code.admin_order_field = 'occupation__occ_code'
    
    def get_occupation_name(self, obj):
        """Display occupation name"""
        return obj.occupation.occ_name
    get_occupation_name.short_description = 'Occupation Name'
    get_occupation_name.admin_order_field = 'occupation__occ_name'


@admin.register(OccupationModule)
class OccupationModuleAdmin(admin.ModelAdmin):
    list_display = ['module_code', 'module_name', 'get_occupation_code', 'get_occupation_name', 
                    'get_level_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'occupation__occ_category', 'occupation', 'created_at']
    search_fields = ['module_code', 'module_name', 'occupation__occ_code', 'occupation__occ_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['occupation']
    
    fieldsets = (
        ('Module Information', {
            'fields': ('module_code', 'module_name'),
            'description': 'Enter the module code and name'
        }),
        ('Occupation & Level', {
            'fields': ('occupation', 'level'),
            'description': 'Select occupation first, then select the level for this module'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('occupation', 'level')
    
    def get_occupation_code(self, obj):
        """Display occupation code"""
        return obj.occupation.occ_code
    get_occupation_code.short_description = 'Occupation Code'
    get_occupation_code.admin_order_field = 'occupation__occ_code'
    
    def get_occupation_name(self, obj):
        """Display occupation name"""
        return obj.occupation.occ_name
    get_occupation_name.short_description = 'Occupation Name'
    get_occupation_name.admin_order_field = 'occupation__occ_name'
    
    def get_level_name(self, obj):
        """Display level name"""
        return obj.level.level_name
    get_level_name.short_description = 'Level'
    get_level_name.admin_order_field = 'level__level_name'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter level choices based on selected occupation"""
        if db_field.name == "level":
            # Get occupation from request if editing
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj = self.get_object(request, request.resolver_match.kwargs['object_id'])
                    if obj and obj.occupation:
                        kwargs["queryset"] = OccupationLevel.objects.filter(occupation=obj.occupation)
                except:
                    pass
            # For add form, show all levels but with occupation info
            if 'queryset' not in kwargs:
                kwargs["queryset"] = OccupationLevel.objects.select_related('occupation').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(OccupationPaper)
class OccupationPaperAdmin(admin.ModelAdmin):
    list_display = ['paper_code', 'paper_name', 'get_occupation_code', 'get_occupation_name', 
                    'get_level_name', 'get_module_code', 'paper_type', 'is_active', 'created_at']
    list_filter = ['paper_type', 'is_active', 'occupation__occ_category', 'occupation', 'module', 'created_at']
    search_fields = ['paper_code', 'paper_name', 'occupation__occ_code', 'occupation__occ_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['occupation']
    
    fieldsets = (
        ('Paper Information', {
            'fields': ('paper_code', 'paper_name', 'paper_type'),
            'description': 'Enter the paper code, name, and type (Theory or Practical)'
        }),
        ('Occupation & Level', {
            'fields': ('occupation', 'level', 'module'),
            'description': 'Select occupation first, then select the level for this paper. For Worker\'s PAS, also select the module this paper belongs to.'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('occupation', 'level', 'module')
    
    def get_occupation_code(self, obj):
        """Display occupation code"""
        return obj.occupation.occ_code
    get_occupation_code.short_description = 'Occupation Code'
    get_occupation_code.admin_order_field = 'occupation__occ_code'
    
    def get_occupation_name(self, obj):
        """Display occupation name"""
        return obj.occupation.occ_name
    get_occupation_name.short_description = 'Occupation Name'
    get_occupation_name.admin_order_field = 'occupation__occ_name'
    
    def get_level_name(self, obj):
        """Display level name"""
        return obj.level.level_name
    get_level_name.short_description = 'Level'
    get_level_name.admin_order_field = 'level__level_name'
    
    def get_module_code(self, obj):
        """Display module code"""
        return obj.module.module_code if obj.module else '-'
    get_module_code.short_description = 'Module'
    get_module_code.admin_order_field = 'module__module_code'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter level choices based on selected occupation"""
        if db_field.name == "level":
            # Get occupation from request if editing
            if request.resolver_match.kwargs.get('object_id'):
                try:
                    obj = self.get_object(request, request.resolver_match.kwargs['object_id'])
                    if obj and obj.occupation:
                        kwargs["queryset"] = OccupationLevel.objects.filter(occupation=obj.occupation)
                except:
                    pass
            # For add form, show all levels but with occupation info
            if 'queryset' not in kwargs:
                kwargs["queryset"] = OccupationLevel.objects.select_related('occupation').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
