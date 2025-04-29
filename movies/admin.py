from django.contrib import admin
from .models import Category, Movie, Actor

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'rating', 'is_featured')
    list_filter = ('categories', 'is_featured', 'release_date')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    filter_horizontal = ('categories',)

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    filter_horizontal = ('movies',)