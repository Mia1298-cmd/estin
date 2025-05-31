from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from movies.models import Movie

class Profile(models.Model):
    SUBSCRIPTION_CHOICES = (
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('none', 'Aucun')
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='none')
    subscription_expiry = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def is_subscription_active(self):
        from datetime import date
        if not self.subscription_expiry:
            return False
        return self.subscription_expiry >= date.today()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'movie')
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    watched_date = models.DateTimeField(auto_now=True)
    progress = models.IntegerField(default=0, help_text="Progression en secondes")
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'movie')
        verbose_name_plural = "Watch histories"
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
# Ajouter ce modèle à votre fichier models.py existant

class SupportMessage(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente')
    )
    
    STATUS_CHOICES = (
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé')
    )
    
    first_name = models.CharField(max_length=100, default='name')
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Message de {self.first_name} {self.last_name} - {self.created_at.strftime('%d/%m/%Y')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message de support"
        verbose_name_plural = "Messages de support"    