from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Video
from .serialisers import VideoSerializer
from .transcripts import fetch_transcript

 
# Create your views here.

class VideoView(APIView):

    def post(self, request):
        youtube_id = request.data.get('youtube_id', '') # extract youtube_id from request data of 'youtube_id' in POST request
        stored = Video.objects.filter(youtube_id=youtube_id, segments__isnull=False).exists()  # checked first, as fetch_transcript stores it

        video = fetch_transcript(youtube_id) # use transcripts.py's fetch_transcript def(ined) function to store video's transcript segments in 'video'
        return Response(VideoSerializer(video).data, status=200 if stored else 201) # return serialised video data with status code (200 if already stored, 201 if newly created)
