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

class VideoView(APIView):

    def post(self, request):
        youtube_id = request.data.get('youtube_id', '') # extract youtube_id from request data of 'youtube_id' in POST request
        stored = Video.objects.filter(youtube_id=youtube_id, segments__isnull=False).exists()  # checked first, as fetch_transcript stores it

        try:
            video = fetch_transcript(youtube_id) # use transcripts.py's fetch_transcript def(ined) function to store video's transcript segments in 'video'
        except (CouldNotRetrieveTranscript, RequestException, ParseError) as e:
            for kinds, code, message in FETCH_ERRORS:
                if isinstance(e, kinds):
                    return Response({'detail': message}, status=code)

        if not video.segments.exists():  # YouTube returned an empty caption track
            return Response({'detail': "This video's transcript is empty"}, status=422)
        return Response(VideoSerializer(video).data, status=200 if stored else 201) # return serialised video data with status code (200 if already stored, 201 if newly created)
