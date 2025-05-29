from django.conf import settings
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, StreamingHttpResponse, FileResponse, HttpResponse
from django.db.models import Q
from wsgiref.util import FileWrapper
import os, mimetypes, re
from .models import Category, Movie, Season, Episode, Actor
from .serializers import CategorySerializer, MovieSerializer, MovieListSerializer, ActorSerializer

# API ViewSets (inchangés)
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

class ActorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

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

def index(request):
    """Page d'accueil alternative"""
    categories = Category.objects.all()[:5]
    return render(request, 'index.html', {'categories': categories})

def movies_and_shows(request):
    """Page qui affiche tous les films et séries groupés par catégorie"""
    categories = Category.objects.all()
    categories_with_movies = []
    
    for category in categories:
        category_data = {
            'category': category,
            'movies': Movie.objects.filter(categories=category)[:5]
        }
        categories_with_movies.append(category_data)
    
    all_movies = Movie.objects.all()
    
    context = {
        'categories_with_movies': categories_with_movies,
        'all_movies': all_movies,
        'categories': categories,
    }
    
    return render(request, 'movies/movies_and_shows.html', context)

def movie_detail(request, slug):
    """Page de détail d'un film ou série"""
    content = get_object_or_404(Movie, slug=slug)
    similar_content = Movie.objects.filter(
        categories__in=content.categories.all()
    ).exclude(id=content.id).distinct()[:4]
    
    context = {
        'movie' if content.is_movie else 'series': content,
        'similar_movies': similar_content,
    }
    
    template = 'movies/movie_detail.html' if content.is_movie else 'movies/series_detail.html'
    return render(request, template, context)

def watch_content(request, slug):
    """Page de visionnage - redirige vers la bonne template selon le type"""
    content = get_object_or_404(Movie, slug=slug)
    similar_content = Movie.objects.filter(
        categories__in=content.categories.all()
    ).exclude(id=content.id).distinct()[:5]
    
    context = {
        'movie' if content.is_movie else 'series': content,
        'similar_movies': similar_content,
    }
    
    if content.is_movie:
        return render(request, 'movies/watch_movie.html', context)
    else:
        return render(request, 'movies/watch_series.html', context)

def category_detail(request, slug):
    """Page de détail d'une catégorie"""
    category = get_object_or_404(Category, slug=slug)
    movies = Movie.objects.filter(categories=category)
    
    context = {
        'category': category,
        'movies': movies,
    }
    return render(request, 'movies/category_detail.html', context)

def search_movies(request):
    """Recherche de films et séries"""
    query = request.GET.get('q', '').strip()
    movies = Movie.objects.none()
    
    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(actors__name__icontains=query) |
            Q(categories__name__icontains=query)
        ).distinct()
    
    context = {
        'query': query,
        'movies': movies,
    }
    return render(request, 'movies/search.html', context)

def movie_stream(request, slug):
    """API pour streamer un film ou le premier épisode d'une série"""
    content = get_object_or_404(Movie, slug=slug)
    
    # Pour les films
    if content.is_movie and content.video_file:
        file_path = content.video_file.path
    # Pour les séries, prendre le premier épisode de la première saison
    elif content.is_series:
        first_season = content.seasons.order_by('season_number').first()
        if first_season:
            first_episode = first_season.episodes.order_by('episode_number').first()
            if first_episode and first_episode.video_file:
                file_path = first_episode.video_file.path
            else:
                return HttpResponse("Aucun épisode disponible", status=404)
        else:
            return HttpResponse("Aucune saison disponible", status=404)
    else:
        return HttpResponse("Aucun fichier vidéo disponible", status=404)
    
    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        return HttpResponse("Le fichier vidéo n'existe pas", status=404)
    
    # Obtenir les informations du fichier
    file_size = os.path.getsize(file_path)
    content_type, encoding = mimetypes.guess_type(file_path)
    content_type = content_type or 'video/mp4'
    
    # Support pour HTTP Range (lecture partielle)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    
    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if end >= file_size:
                end = file_size - 1
            
            length = end - start + 1
            
            # Ouvrir le fichier et se positionner au bon endroit
            file_handle = open(file_path, 'rb')
            file_handle.seek(start)
            
            # Créer la réponse de streaming partiel
            response = StreamingHttpResponse(
                FileWrapper(file_handle, 8192),
                status=206,
                content_type=content_type
            )
            
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'
            
            return response
    
    # Streaming complet
    file_handle = open(file_path, 'rb')
    response = StreamingHttpResponse(
        FileWrapper(file_handle, 8192),
        content_type=content_type
    )
    
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'no-cache'
    
    return response

def episode_stream(request, series_slug, season_number, episode_number):
    """API pour streamer un épisode spécifique"""
    series = get_object_or_404(Movie, slug=series_slug, content_type='series')
    season = get_object_or_404(Season, series=series, season_number=season_number)
    episode = get_object_or_404(Episode, season=season, episode_number=episode_number)
    
    if not episode.video_file:
        return HttpResponse("Le fichier vidéo de l'épisode n'existe pas", status=404)
    
    file_path = episode.video_file.path
    
    if not os.path.exists(file_path):
        return HttpResponse("Le fichier vidéo n'existe pas sur le disque", status=404)
    
    # Même logique de streaming que movie_stream
    file_size = os.path.getsize(file_path)
    content_type, encoding = mimetypes.guess_type(file_path)
    content_type = content_type or 'video/mp4'
    
    range_header = request.META.get('HTTP_RANGE', '').strip()
    
    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if end >= file_size:
                end = file_size - 1
            
            length = end - start + 1
            
            file_handle = open(file_path, 'rb')
            file_handle.seek(start)
            
            response = StreamingHttpResponse(
                FileWrapper(file_handle, 8192),
                status=206,
                content_type=content_type
            )
            
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'
            
            return response
    
    file_handle = open(file_path, 'rb')
    response = StreamingHttpResponse(
        FileWrapper(file_handle, 8192),
        content_type=content_type
    )
    
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'no-cache'
    
    return response
# Ajoutez ces vues à votre views.py existant

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Movie, Category, Actor, Season, Episode, Comment, Like

def watch_content(request, slug):
    """Page de visionnage avec gestion des commentaires"""
    content = get_object_or_404(Movie, slug=slug)
    similar_content = Movie.objects.filter(
        categories__in=content.categories.all()
    ).exclude(id=content.id).distinct()[:5]
    
    # Récupérer les commentaires
    comments = Comment.objects.filter(movie=content).select_related('user')[:10]
    
    # Traitement du formulaire de commentaire
    if request.method == 'POST' and request.user.is_authenticated:
        comment_content = request.POST.get('comment_content', '').strip()
        rating = request.POST.get('rating')
        
        if comment_content and rating:
            try:
                rating_float = float(rating)
                if 0 <= rating_float <= 5:
                    Comment.objects.create(
                        user=request.user,
                        movie=content,
                        content=comment_content,
                        rating=rating_float
                    )
                    messages.success(request, 'Votre commentaire a été ajouté avec succès!')
                    return redirect('watch_content', slug=slug)
            except ValueError:
                messages.error(request, 'Note invalide.')
    
    context = {
        'movie' if content.is_movie else 'series': content,
        'similar_movies': similar_content,
        'comments': comments,
        'user_can_comment': request.user.is_authenticated,
    }
    
    if content.is_movie:
        return render(request, 'movies/watch_movie.html', context)
    else:
        return render(request, 'movies/watch_series.html', context)

@login_required
@csrf_exempt
def add_comment_ajax(request, slug):
    """Ajouter un commentaire via AJAX"""
    if request.method == 'POST':
        content = get_object_or_404(Movie, slug=slug)
        
        try:
            data = json.loads(request.body)
            comment_content = data.get('content', '').strip()
            rating = float(data.get('rating', 0))
            
            if comment_content and 0 <= rating <= 5:
                comment = Comment.objects.create(
                    user=request.user,
                    movie=content,
                    content=comment_content,
                    rating=rating
                )
                
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'user': comment.user.username,
                        'content': comment.content,
                        'rating': float(comment.rating),
                        'created_at': comment.created_at.strftime('%B %d, %Y')
                    }
                })
            else:
                return JsonResponse({'success': False, 'error': 'Données invalides'})
                
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Format de données invalide'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})