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