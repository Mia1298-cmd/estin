from django.contrib import admin
from .models import Profile, Watchlist, WatchHistory

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'subscription_expiry', 'is_subscription_active')
    list_filter = ('subscription_type',)
    search_fields = ('user__username', 'user__email')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_date')
    list_filter = ('added_date',)
    search_fields = ('user__username', 'movie__title')

@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'watched_date', 'progress', 'completed')
    list_filter = ('watched_date', 'completed')
    search_fields = ('user__username', 'movie__title')
from django.contrib import admin
from .models import Profile, Watchlist, WatchHistory, SupportMessage

# Classe admin pour les messages de support
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'created_at', 'status', 'priority')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations de contact', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('message', 'created_at', 'updated_at')
        }),
        ('Traitement', {
            'fields': ('status', 'priority', 'admin_notes', 'user')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Rendre certains champs en lecture seule après création
        if obj:  # Si l'objet existe déjà (modification)
            return self.readonly_fields + ('first_name', 'last_name', 'email', 'phone', 'message')
        return self.readonly_fields

# Enregistrer seulement le nouveau modèle SupportMessage
admin.site.register(SupportMessage, SupportMessageAdmin)

# Ne pas réenregistrer les modèles déjà enregistrés
# Si vous voulez vérifier quels modèles sont déjà enregistrés, vous pouvez utiliser :
# print("Modèles déjà enregistrés:", admin.site._registry.keys())    