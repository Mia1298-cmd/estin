from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Movie(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    release_date = models.DateField()
    duration = models.DurationField(help_text="Durée (heures et minutes)")
    poster = models.ImageField(upload_to='posters/')
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', null=True, blank=True)
    trailer_url = models.URLField(null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='movies')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class Actor(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    photo = models.ImageField(upload_to='actors/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    movies = models.ManyToManyField(Movie, related_name='actors')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name