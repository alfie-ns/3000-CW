from django.db import transaction
from youtube_transcript_api import YouTubeTranscriptApi

from .models import Video, TranscriptSegment


def fetch_transcript(youtube_id, title=''):
    video = Video.objects.filter(youtube_id=youtube_id).first()
    if video and video.segments.exists():
        return video  # store without needing to re-fetch

    fetched = YouTubeTranscriptApi().fetch(youtube_id) # fetch the transcript from YouTube API

    with transaction.atomic():  # no Video row without its segments
        video, _ = Video.objects.get_or_create(youtube_id=youtube_id, defaults={'title': title or youtube_id})
        TranscriptSegment.objects.bulk_create(
            TranscriptSegment(video=video, start=s.start, end=s.start + s.duration, text=s.text)
            for s in fetched
        )
    return video
