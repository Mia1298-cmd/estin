from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'movies', views.MovieViewSet)
router.register(r'actors', views.ActorViewSet)

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Template URLs
    path('', views.home, name='home'),
    path('movies-and-shows/', views.movies_and_shows, name='movies_and_shows'),
    path('content/<slug:slug>/', views.movie_detail, name='content_detail'),
    path('watch/<slug:slug>/', views.watch_content, name='watch_content'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('search/', views.search_movies, name='search_movies'),
   
    # Comment URLs
    path('add-comment/<slug:slug>/', views.add_comment_ajax, name='add_comment_ajax'),
    
    # Streaming URLs
    path('stream/<slug:slug>/', views.movie_stream, name='movie_stream'),
    path('stream/<slug:series_slug>/s<int:season_number>/e<int:episode_number>/', 
         views.episode_stream, name='episode_stream'),
]