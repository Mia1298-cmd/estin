from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Category, Movie, Season, Episode, Actor

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'movie_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def movie_count(self, obj):
        count = obj.movies.count()
        return format_html(
            '<span style="background-color: #007cba; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            count
        )
    movie_count.short_description = 'Nombre de contenus'

class SeasonInline(admin.TabularInline):
    model = Season
    extra = 1
    fields = ['season_number', 'title', 'description', 'release_date', 'poster']
    readonly_fields = ['episode_count_display']
    
    def episode_count_display(self, obj):
        if obj.pk:
            count = obj.episodes.count()
            url = reverse('admin:movies_episode_changelist') + f'?season__id__exact={obj.pk}'
            return format_html(
                '<a href="{}" style="color: #007cba;">{} épisodes</a>',
                url, count
            )
        return "Sauvegardez d'abord pour ajouter des épisodes"
    episode_count_display.short_description = 'Épisodes'

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1
    fields = ['episode_number', 'title', 'duration', 'video_file', 'thumbnail']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = [
        'title_with_icon', 
        'content_type', 
        'release_date', 
        'rating', 
        'is_featured',
        'status',
        'seasons_episodes_count'
    ]
    list_filter = [
        'content_type', 
        'is_featured', 
        'status', 
        'categories', 
        'release_date'
    ]
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    # Correction : ne garder dans filter_horizontal que des champs ManyToMany
    filter_horizontal = ['categories']  # <-- 'actors' n'est pas ManyToMany dans Movie, donc on l'enlève

    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'slug', 'content_type', 'description')
        }),
        ('Médias', {
            'fields': ('poster', 'banner', 'trailer_url'),
            'classes': ('collapse',)
        }),
        ('Contenu vidéo (Films uniquement)', {
            'fields': ('video_file', 'duration'),
            'classes': ('collapse',),
            'description': 'Ces champs ne sont utilisés que pour les films. Pour les séries, utilisez les saisons et épisodes.'
        }),
        ('Métadonnées', {
            'fields': ('release_date', 'rating', 'is_featured', 'status')
        }),
        ('Séries uniquement', {
            'fields': ('total_seasons',),
            'classes': ('collapse',),
            'description': 'Ce champ n\'est utilisé que pour les séries.'
        }),
        # Correction ici : on retire complètement le fieldset 'Relations' s'il ne contient que 'actors'
        # ou bien on le laisse uniquement avec 'categories' si ce champ existe bien dans Movie
        ('Relations', {
            'fields': ('categories',),
            'classes': ('collapse',)
        }),
    )
    
    def get_inlines(self, request, obj):
        if obj and obj.content_type == 'series':
            return [SeasonInline]
        return []
    
    def title_with_icon(self, obj):
        icon = "📺" if obj.content_type == 'series' else "🎬"
        return f"{icon} {obj.title}"
    title_with_icon.short_description = 'Titre'
    
    def seasons_episodes_count(self, obj):
        if obj.content_type == 'series':
            seasons_count = obj.seasons.count()
            episodes_count = obj.total_episodes
            return format_html(
                '<span style="color: #007cba;">{} saisons, {} épisodes</span>',
                seasons_count, episodes_count
            )
        else:
            if obj.duration:
                return format_html(
                    '<span style="color: #28a745;">Durée: {}</span>',
                    obj.duration
                )
            return "Pas de durée définie"
    seasons_episodes_count.short_description = 'Contenu'

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = [
        'series_title', 
        'season_number', 
        'title', 
        'episode_count_display', 
        'release_date'
    ]
    list_filter = ['series', 'release_date']
    search_fields = ['series__title', 'title']
    inlines = [EpisodeInline]
    
    def series_title(self, obj):
        return f"📺 {obj.series.title}"
    series_title.short_description = 'Série'
    
    def episode_count_display(self, obj):
        count = obj.episodes.count()
        if count > 0:
            url = reverse('admin:movies_episode_changelist') + f'?season__id__exact={obj.pk}'
            return format_html(
                '<a href="{}" style="color: #007cba; font-weight: bold;">{} épisodes</a>',
                url, count
            )
        return format_html('<span style="color: #dc3545;">Aucun épisode</span>')
    episode_count_display.short_description = 'Épisodes'

@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = [
        'episode_display', 
        'title', 
        'duration', 
        'rating', 
        'air_date',
        'has_video'
    ]
    list_filter = ['season__series', 'season', 'air_date']
    search_fields = ['title', 'description', 'season__series__title']
    
    def episode_display(self, obj):
        return f"📺 {obj.season.series.title} S{obj.season.season_number}E{obj.episode_number:02d}"
    episode_display.short_description = 'Épisode'
    
    def has_video(self, obj):
        if obj.video_file:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Vidéo</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Pas de vidéo</span>'
        )
    has_video.short_description = 'Fichier vidéo'

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ['name', 'nationality', 'birth_date', 'movies_count']
    list_filter = ['nationality']
    search_fields = ['name', 'bio']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['movies']
    
    def movies_count(self, obj):
        count = obj.movies.count()
        return format_html(
            '<span style="background-color: #007cba; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            count
        )
    movies_count.short_description = 'Nombre de films/séries'

# Configuration de l'admin
admin.site.site_header = "🎬 STINS Administration"
admin.site.site_title = "STINS Admin"
admin.site.index_title = "Gestion des contenus"
# Ajoutez ceci à votre admin.py existant

from .models import Comment, Like

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'created_at', 'content_preview']
    list_filter = ['rating', 'created_at', 'movie__content_type']
    search_fields = ['user__username', 'movie__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Aperçu du commentaire'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'created_at']
    list_filter = ['created_at', 'movie__content_type']
    search_fields = ['user__username', 'movie__title']