from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Movie(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('movie', 'Film'),
        ('series', 'Série'),
    ]
    
    # Informations de base
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(unique=True, blank=True)
    content_type = models.CharField(
        max_length=10, 
        choices=CONTENT_TYPE_CHOICES, 
        default='movie',
        verbose_name="Type de contenu"
    )
    description = models.TextField(verbose_name="Description")
    
    # Dates et durée
    release_date = models.DateField(verbose_name="Date de sortie")
    duration = models.DurationField(
        help_text="Durée (heures et minutes) - Pour les films uniquement", 
        null=True, 
        blank=True,
        verbose_name="Durée"
    )
    
    # Images
    poster = models.ImageField(upload_to='posters/', verbose_name="Affiche")
    banner = models.ImageField(
        upload_to='banners/', 
        null=True, 
        blank=True,
        verbose_name="Bannière"
    )
    
    # Fichiers vidéo (pour les films)
    video_file = models.FileField(
        upload_to='videos/', 
        null=True, 
        blank=True,
        verbose_name="Fichier vidéo",
        help_text="Pour les films uniquement"
    )
    trailer_url = models.URLField(
        null=True, 
        blank=True,
        verbose_name="URL de la bande-annonce"
    )
    
    # Relations et métadonnées
    categories = models.ManyToManyField(Category, related_name='movies', verbose_name="Catégories")
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name="Note"
    )
    is_featured = models.BooleanField(default=False, verbose_name="En vedette")
    
    # Champs spécifiques aux séries
    total_seasons = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name="Nombre total de saisons",
        help_text="Pour les séries uniquement"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('ongoing', 'En cours'),
            ('completed', 'Terminée'),
            ('cancelled', 'Annulée'),
        ],
        default='completed',
        verbose_name="Statut"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        content_type_display = "📺" if self.content_type == 'series' else "🎬"
        return f"{content_type_display} {self.title}"
    
    @property
    def is_series(self):
        return self.content_type == 'series'
    
    @property
    def is_movie(self):
        return self.content_type == 'movie'
    
    @property
    def total_episodes(self):
        if self.is_series:
            return Episode.objects.filter(season__series=self).count()
        return 0
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Film/Série"
        verbose_name_plural = "Films/Séries"

class Season(models.Model):
    series = models.ForeignKey(
        Movie, 
        on_delete=models.CASCADE, 
        related_name='seasons',
        limit_choices_to={'content_type': 'series'},
        verbose_name="Série"
    )
    season_number = models.PositiveIntegerField(verbose_name="Numéro de saison")
    title = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Titre de la saison",
        help_text="Optionnel - ex: 'Saison 1: Les Origines'"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Description de la saison"
    )
    release_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de sortie de la saison"
    )
    poster = models.ImageField(
        upload_to='seasons/', 
        null=True, 
        blank=True,
        verbose_name="Affiche de la saison"
    )
    
    def __str__(self):
        if self.title:
            return f"{self.series.title} - {self.title}"
        return f"{self.series.title} - Saison {self.season_number}"
    
    @property
    def episode_count(self):
        return self.episodes.count()
    
    class Meta:
        unique_together = ['series', 'season_number']
        ordering = ['series', 'season_number']
        verbose_name = "Saison"
        verbose_name_plural = "Saisons"

class Episode(models.Model):
    season = models.ForeignKey(
        Season, 
        on_delete=models.CASCADE, 
        related_name='episodes',
        verbose_name="Saison"
    )
    episode_number = models.PositiveIntegerField(verbose_name="Numéro d'épisode")
    title = models.CharField(max_length=200, verbose_name="Titre de l'épisode")
    description = models.TextField(verbose_name="Description")
    duration = models.DurationField(
        verbose_name="Durée",
        help_text="Durée de l'épisode (heures et minutes)"
    )
    
    # Fichiers
    video_file = models.FileField(
        upload_to='episodes/', 
        verbose_name="Fichier vidéo de l'épisode"
    )
    thumbnail = models.ImageField(
        upload_to='episode_thumbnails/', 
        null=True, 
        blank=True,
        verbose_name="Miniature de l'épisode"
    )
    
    # Métadonnées
    air_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de diffusion"
    )
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name="Note de l'épisode"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.season.series.title} S{self.season.season_number}E{self.episode_number:02d} - {self.title}"
    
    @property
    def series(self):
        return self.season.series
    
    class Meta:
        unique_together = ['season', 'episode_number']
        ordering = ['season', 'episode_number']
        verbose_name = "Épisode"
        verbose_name_plural = "Épisodes"

class Actor(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)
    photo = models.ImageField(
        upload_to='actors/', 
        null=True, 
        blank=True,
        verbose_name="Photo"
    )
    bio = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Biographie"
    )
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de naissance"
    )
    nationality = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Nationalité"
    )
    movies = models.ManyToManyField(
        Movie, 
        related_name='actors',
        verbose_name="Films/Séries"
    )
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = "Acteur"
        verbose_name_plural = "Acteurs"
# Ajoutez ces modèles à votre models.py existant

from django.contrib.auth.models import User
from django.db import models

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments', verbose_name="Film/Série")
    content = models.TextField(verbose_name="Commentaire")
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name="Note (sur 5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.rating}/5)"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        verbose_name = "Like"
        verbose_name_plural = "Likes"   
# Ajoutez ces modèles à votre models.py existant

from django.contrib.auth.models import User
from django.db import models

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments', verbose_name="Film/Série")
    content = models.TextField(verbose_name="Commentaire")
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name="Note (sur 5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.rating}/5)"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        verbose_name = "Like"
        verbose_name_plural = "Likes"             