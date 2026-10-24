from django.db import models

# Create your models here.

class Video(models.Model):
    youtube_id = models.CharField(max_length=11, unique=True)  # YouTube ids are natively 11 characters long
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
