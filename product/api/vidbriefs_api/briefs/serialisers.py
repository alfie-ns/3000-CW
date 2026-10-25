from rest_framework import serializers

from .models import Video, TranscriptSegment

'''
'rest_framework.serializers' for the Video and TranscriptSegment models (converts model instances to JSON and vice versa)
'''

class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = ['start', 'end', 'text']


class VideoSerializer(serializers.ModelSerializer):
    segments = TranscriptSegmentSerializer(many=True, read_only=True)  # in start order, via the model's Meta

    class Meta:
        model = Video
        fields = ['youtube_id', 'title', 'created_at', 'segments']