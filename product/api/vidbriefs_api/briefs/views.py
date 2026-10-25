import re
from urllib.parse import parse_qs, urlparse
from xml.etree.ElementTree import ParseError

from django.shortcuts import render
from requests import RequestException
from rest_framework.response import Response
from rest_framework.views import APIView
from youtube_transcript_api import (
    AgeRestricted, CouldNotRetrieveTranscript, InvalidVideoId, NoTranscriptFound,
    RequestBlocked, TranscriptsDisabled, VideoUnavailable, VideoUnplayable, YouTubeRequestFailed,
)

from .models import Video
from .serialisers import VideoSerializer
from .transcripts import fetch_transcript

 
# Create your views here.

FETCH_ERRORS = [  # specific first, the library's catch-all last
    (InvalidVideoId, 400, 'Not a valid YouTube video'),
    (VideoUnavailable, 404, 'This video is unavailable'),
    (TranscriptsDisabled, 422, 'Captions are turned off for this video'),
    (NoTranscriptFound, 422, 'This video has no English transcript'),
    ((AgeRestricted, VideoUnplayable), 422, 'This video cannot be played without signing in'),
    ((RequestBlocked, YouTubeRequestFailed, RequestException), 503, 'YouTube could not be reached; try again'),
    ((CouldNotRetrieveTranscript, ParseError), 502, 'The transcript could not be fetched; try again'),  # ParseError: malformed captions from YouTube
]

YOUTUBE_ID = re.compile(r'[A-Za-z0-9_-]{11}')


def youtube_id_from(url):  # watch?v=, youtu.be/, shorts/, embed/, live/ links, or a bare id
    url = url.strip()
    if YOUTUBE_ID.fullmatch(url):
        return url
    try:
        parts = urlparse(url if '://' in url else f'https://{url}')
    except ValueError:  # e.g. an unclosed '[' host
        return None
    host = (parts.hostname or '').removeprefix('www.').removeprefix('m.')
    path = parts.path.strip('/').split('/')  # '/shorts/x' -> ['shorts', 'x'], i.e., first element indicates type of YouTube URL

    if host == 'youtu.be': # short link that works on app-derived URL
        candidate = path[0]
    elif host in ('youtube.com', 'music.youtube.com') and path[0] == 'watch': # standard watch URL with 'v' query parameter
        candidate = parse_qs(parts.query).get('v', [''])[0] 
    elif host == 'youtube.com' and path[0] in ('shorts', 'embed', 'live') and len(path) > 1: # standard web URL for shorts, embed, or live videos
        candidate = path[1]
    else:
        return None
    return candidate if YOUTUBE_ID.fullmatch(candidate) else None


class VideoView(APIView):

    def post(self, request):
        url = request.data.get('url') if isinstance(request.data, dict) else None  # a JSON list body has no .get
        youtube_id = youtube_id_from(url) if isinstance(url, str) else None
        if not youtube_id: # catch non-youtube links
            return Response({'detail': 'Not a YouTube link'}, status=400)

        stored = Video.objects.filter(youtube_id=youtube_id, segments__isnull=False).exists()  # checked first; fetch_transcript stores it

        try:
            video = fetch_transcript(youtube_id) # use transcripts.py's fetch_transcript def(ined) function to store video's transcript segments in 'video'
        except (CouldNotRetrieveTranscript, RequestException, ParseError) as e:
            for kinds, code, message in FETCH_ERRORS:
                if isinstance(e, kinds):
                    return Response({'detail': message}, status=code)

        if not video.segments.exists():  # YouTube returned an empty caption track
            return Response({'detail': "This video's transcript is empty"}, status=422)
        return Response(VideoSerializer(video).data, status=200 if stored else 201) # return serialised video data with status code (200 if already stored, 201 if newly created)
