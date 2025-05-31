from rest_framework import serializers
from .models import Category, Movie, Season, Episode, Actor

class CategorySerializer(serializers.ModelSerializer):
    movie_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'movie_count']
    
    def get_movie_count(self, obj):
        return obj.movies.count()

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['id', 'name', 'slug', 'photo', 'bio', 'birth_date', 'nationality']

class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = [
            'id', 'episode_number', 'title', 'description', 
            'duration', 'thumbnail', 'air_date', 'rating'
        ]

class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    episode_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Season
        fields = [
            'id', 'season_number', 'title', 'description', 
            'release_date', 'poster', 'episodes', 'episode_count'
        ]
    
    def get_episode_count(self, obj):
        return obj.episodes.count()

class MovieListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'content_type', 'description', 
            'release_date', 'duration', 'poster', 'banner', 
            'rating', 'is_featured', 'status', 'categories', 'actors'
        ]

class MovieSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    total_episodes = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'content_type', 'description', 
            'release_date', 'duration', 'poster', 'banner', 
            'video_file', 'trailer_url', 'rating', 'is_featured', 
            'status', 'total_seasons', 'categories', 'actors', 
            'seasons', 'total_episodes', 'created_at', 'updated_at'
        ]