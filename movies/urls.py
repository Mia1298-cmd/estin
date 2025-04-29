from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'movies', views.MovieViewSet)
router.register(r'actors', views.ActorViewSet)

urlpatterns = [
    path('', include(router.urls)),
     # Template URLs
    path('', views.home, name='home'),
    path('', views.index, name='index'),
    path('movies-and-shows/', views.movies_and_shows, name='movies_and_shows'),
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('watch/<slug:slug>/', views.watch_movie, name='watch_movie'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('api/movie-stream/<slug:slug>/', views.movie_stream, name='movie-stream'),

]