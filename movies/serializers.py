from rest_framework import serializers
from .models import Category, Movie, Actor

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['id', 'name', 'slug', 'photo', 'bio']

class MovieSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'slug', 'description', 'release_date', 
            'duration', 'poster', 'banner', 'video_file', 'trailer_url',
            'categories', 'actors', 'rating', 'is_featured'
        ]

class MovieListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = ['id', 'title', 'slug', 'poster', 'categories', 'rating']