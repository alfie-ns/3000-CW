from django.db import models

# Create your models here.

class Video(models.Model):
    youtube_id = models.CharField(max_length=11, unique=True)  # YouTube ids are natively 11 characters long
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TranscriptSegment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='segments')
    start = models.FloatField()  # seconds into the video
    end = models.FloatField()
    text = models.TextField()

    class Meta:
        ordering = ['video', 'start']

    def __str__(self):
        return f'{self.video} @ {self.start:.1f}s'
