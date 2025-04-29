from django.conf import settings
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.http import Http404, StreamingHttpResponse
from wsgiref.util import FileWrapper
import os, mimetypes, re
from .models import Category, Movie, Actor
from .serializers import CategorySerializer, MovieSerializer, MovieListSerializer, ActorSerializer

# API ViewSets
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def movies(self, request, slug=None):
        category = self.get_object()
        movies = category.movies.all()
        serializer = MovieListSerializer(movies, many=True)
        return Response(serializer.data)

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['release_date', 'rating']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MovieListSerializer
        return MovieSerializer
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_movies = Movie.objects.filter(is_featured=True)
        serializer = MovieListSerializer(featured_movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_movies = Movie.objects.order_by('-release_date')[:10]
        serializer = MovieListSerializer(recent_movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        top_rated = Movie.objects.order_by('-rating')[:10]
        serializer = MovieListSerializer(top_rated, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stream(self, request, slug=None):
        """Stream le fichier vidéo avec support pour la lecture partielle (HTTP Range)"""
        movie = self.get_object()
        
        if not movie.video_file:
            return Response({"error": "Aucun fichier vidéo disponible"}, status=404)
        
        path = movie.video_file.path
        
        # Vérifier si le fichier existe
        if not os.path.exists(path):
            return Response({"error": "Fichier vidéo introuvable"}, status=404)
        
        # Obtenir le type MIME
        content_type, encoding = mimetypes.guess_type(path)
        content_type = content_type or 'application/octet-stream'
        
        # Obtenir la taille du fichier
        file_size = os.path.getsize(path)
        
        # Support pour HTTP Range (lecture partielle)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if range_match:
            start_byte = int(range_match.group(1))
            end_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if end_byte >= file_size:
                end_byte = file_size - 1
                
            length = end_byte - start_byte + 1
            
            resp = StreamingHttpResponse(
                FileWrapper(open(path, 'rb'), 8192),
                status=206,
                content_type=content_type
            )
            
            resp['Content-Length'] = str(length)
            resp['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
        else:
            resp = StreamingHttpResponse(
                FileWrapper(open(path, 'rb'), 8192),
                content_type=content_type
            )
            resp['Content-Length'] = str(file_size)
        
        resp['Accept-Ranges'] = 'bytes'
        return resp

class ActorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def movies(self, request, slug=None):
        actor = self.get_object()
        movies = actor.movies.all()
        serializer = MovieListSerializer(movies, many=True)
        return Response(serializer.data)

# Vues pour les templates
def home(request):
    """Page d'accueil avec films en vedette et catégories"""
    featured_movies = Movie.objects.filter(is_featured=True).order_by('-created_at')[:6]
    categories = Category.objects.all()
    latest_movies = Movie.objects.order_by('-created_at')[:8]
    
    context = {
        'featured_movies': featured_movies,
        'categories': categories,
        'latest_movies': latest_movies,
    }
    return render(request, 'movies/home.html', context)

def movie_detail(request, slug):
    """Page de détail d'un film"""
    movie = get_object_or_404(Movie, slug=slug)
    related_movies = Movie.objects.filter(categories__in=movie.categories.all()).exclude(id=movie.id).distinct()[:4]
    
    context = {
        'movie': movie,
        'related_movies': related_movies,
    }
    return render(request, 'movies/movie_detail.html', context)

def watch_movie(request, slug):
    """Page de lecture du film"""
    movie = get_object_or_404(Movie, slug=slug)
    
    context = {
        'movie': movie,
    }
    return render(request, 'movies/watch.html', context)

def category_movies(request, slug):
    """Films par catégorie"""
    category = get_object_or_404(Category, slug=slug)
    movies = Movie.objects.filter(categories=category)
    
    context = {
        'category': category,
        'movies': movies,
    }
    return render(request, 'movies/category.html', context)

def search_movies(request):
    """Recherche de films"""
    query = request.GET.get('q', '')
    if query:
        movies = Movie.objects.filter(title__icontains=query)
    else:
        movies = Movie.objects.none()
    
    context = {
        'query': query,
        'movies': movies,
    }
    return render(request, 'movies/search.html', context)
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Movie, Category, Actor

def index(request):
    """Page d'accueil"""
    categories = Category.objects.all()[:5]
    return render(request, 'index.html', {'categories': categories})

def movies_and_shows(request):
    """Page qui affiche tous les films et séries groupés par catégorie"""
    categories = Category.objects.all()
    
    # Créer un dictionnaire pour stocker les films par catégorie
    categories_with_movies = []
    
    # Récupérer les films pour chaque catégorie
    for category in categories:
        # Créer un dictionnaire avec la catégorie et ses films
        category_data = {
            'category': category,
            'movies': Movie.objects.filter(categories=category)[:5]
        }
        categories_with_movies.append(category_data)
    
    # Tous les films pour la vue en grille
    all_movies = Movie.objects.all()
    
    context = {
        'categories_with_movies': categories_with_movies,
        'all_movies': all_movies,
    }
    
    return render(request, 'movies/movies_and_shows.html', context)

def movie_detail(request, slug):
    """Page de détail d'un film"""
    movie = get_object_or_404(Movie, slug=slug)
    
    # Films similaires (même catégorie)
    similar_movies = Movie.objects.filter(categories__in=movie.categories.all()).exclude(id=movie.id).distinct()[:4]
    
    context = {
        'movie': movie,
        'similar_movies': similar_movies,
    }
    
    return render(request, 'movies/movie_detail.html', context)

def watch_movie(request, slug):
    """Page de visionnage d'un film"""
    movie = get_object_or_404(Movie, slug=slug)
    
    # Films similaires (même catégorie)
    similar_movies = Movie.objects.filter(categories__in=movie.categories.all()).exclude(id=movie.id).distinct()[:5]
    
    context = {
        'movie': movie,
        'similar_movies': similar_movies,
    }
    
    return render(request, 'movies/watch.html', context)

def category_detail(request, slug):
    """Page de détail d'une catégorie"""
    category = get_object_or_404(Category, slug=slug)
    movies = Movie.objects.filter(categories=category)
    
    context = {
        'category': category,
        'movies': movies,
    }
    
    return render(request, 'movies/category_detail.html', context)
def movie_stream(request, slug):
    """API pour streamer un film"""
    movie = get_object_or_404(Movie, slug=slug)
    
    # Vérifiez si le fichier vidéo existe
    if not movie.video_file:
        raise Http404("Le fichier vidéo n'existe pas")
    
    # Chemin complet vers le fichier vidéo
    file_path = os.path.join(settings.MEDIA_ROOT, str(movie.video_file))
    
    # Vérifiez si le fichier existe sur le disque
    if not os.path.exists(file_path):
        raise Http404("Le fichier vidéo n'existe pas sur le disque") # type: ignore
    
    # Retournez le fichier vidéo en streaming
    response = FileResponse(open(file_path, 'rb'), content_type='video/mp4') # type: ignore
    response['Accept-Ranges'] = 'bytes'
    return response