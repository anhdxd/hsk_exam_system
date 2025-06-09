from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class HSKLevel(models.Model):
    """HSK Level model"""
    level = models.IntegerField(unique=True)
    name = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    vocabulary_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['level']
        verbose_name = 'HSK Level'
        verbose_name_plural = 'HSK Levels'
    
    def __str__(self):
        return f"HSK {self.level}"
