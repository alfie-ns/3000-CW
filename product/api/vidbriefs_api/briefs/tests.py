from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase
from youtube_transcript_api import FetchedTranscriptSnippet, VideoUnavailable

from .models import Video, TranscriptSegment
from .transcripts import fetch_transcript
from .views import youtube_id_from

# 1- AI-assisted: generated example code with ChatGPT for unit tests; utilised to create tests reviewed, tested and understood by me

'''
python manage.py test:

```output
fetch_transcript: Ran 3 tests in 0.002s
youtube_id_from: Ran 1 test in 0.000s
VideoView: Ran 2 tests in 0.007s

OK
Destroying test database for alias 'default'...
```

'''

# Create your tests here.

FAKE_CAPTIONS = [  # out of order, to check the model's ordering
    FetchedTranscriptSnippet(text='second line', start=4.0, duration=2.5),
    FetchedTranscriptSnippet(text='first line', start=0.5, duration=3.0),
]


# NOTE: Tests for fetch_transcript function, ensuring correct storage then handling of YouTube transcripts.

@patch('briefs.transcripts.YouTubeTranscriptApi')  # no real YouTube calls
class FetchTranscriptTests(TestCase):

    def test_stores_each_caption_with_start_and_end(self, api): # ensures each caption's stored with the genuine start and end times
        api.return_value.fetch.return_value = FAKE_CAPTIONS
        video = fetch_transcript('abcdefghijk', 'Test video')

        segments = list(video.segments.all())
        self.assertEqual([s.text for s in segments], ['first line', 'second line'])# 
        self.assertEqual((segments[0].start, segments[0].end), (0.5, 3.5))
        self.assertEqual((segments[1].start, segments[1].end), (4.0, 6.5))

    def test_stored_video_is_not_fetched_again(self, api): # ensure non-duplicate fetch for already stored video
        api.return_value.fetch.return_value = FAKE_CAPTIONS
        fetch_transcript('abcdefghijk')
        fetch_transcript('abcdefghijk')

        api.return_value.fetch.assert_called_once()
        self.assertEqual(TranscriptSegment.objects.count(), 2)

    def test_failed_fetch_leaves_no_video_row(self, api): # ensure fetches fail properely, i.e., no 'ghost' video row is created
        api.return_value.fetch.side_effect = VideoUnavailable('xxxxxxxxxxx')

        with self.assertRaises(VideoUnavailable):
            fetch_transcript('xxxxxxxxxxx')
        self.assertFalse(Video.objects.exists())


class YouTubeIdTests(TestCase):

    def test_link_styles(self):  # test to verify youtube_id_from correctly extracts YouTube IDs from all the different url styles
        links = {
            'abcdefghijk': 'abcdefghijk',
            'https://www.youtube.com/watch?v=abcdefghijk&t=30s': 'abcdefghijk',
            'youtube.com/watch?v=abcdefghijk': 'abcdefghijk',
            'https://m.youtube.com/watch?v=abcdefghijk': 'abcdefghijk',
            'https://music.youtube.com/watch?v=abcdefghijk': 'abcdefghijk',
            'https://youtu.be/abcdefghijk?si=xyz': 'abcdefghijk',
            'https://www.youtube.com/shorts/abcdefghijk': 'abcdefghijk',
            'https://www.youtube.com/embed/abcdefghijk': 'abcdefghijk',
            'https://www.youtube.com/live/abcdefghijk': 'abcdefghijk',
            'https://youtube.com.evil.com/watch?v=abcdefghijk': None,  # lookalike host
            'https://vimeo.com/123456': None,
            'https://youtube.com/watch?v=short': None,
            'https://www.youtube.com/watch': None,
            'https://www.youtube.com/shorts/': None,
            'https://youtu.be/': None,
            'http://[': None,
        }
        for link, expected in links.items(): # loop through each link and test it
            with self.subTest(link=link):
                self.assertEqual(youtube_id_from(link), expected)


# NOTE: Tests for POST /api/videos/, i.e., what the app gets back for each link

@patch('briefs.transcripts.YouTubeTranscriptApi')  # no real YouTube calls
class VideoEndpointTests(APITestCase):

    '''
        1- init post helper method
        2- test new link with correctly ordered segments with captions returns 201 (Created)
        3- test stored video returns 200 (OK) without refetching transcript
    '''

    def post(self, body):
        return self.client.post('/api/videos/', body, format='json')

    def test_new_link_returns_201_with_ordered_segments(self, api):
        api.return_value.fetch.return_value = FAKE_CAPTIONS
        response = self.post({'url': 'https://youtu.be/abcdefghijk'})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['youtube_id'], 'abcdefghijk')
        self.assertEqual([s['text'] for s in response.data['segments']], ['first line', 'second line'])
        self.assertEqual(response.data['segments'][0]['end'], 3.5)

    def test_stored_video_returns_200_without_refetch(self, api):
        api.return_value.fetch.return_value = FAKE_CAPTIONS
        self.post({'url': 'https://youtu.be/abcdefghijk'})
        response = self.post({'url': 'https://www.youtube.com/watch?v=abcdefghijk'})  # same video, other link style

        self.assertEqual(response.status_code, 200)
        api.return_value.fetch.assert_called_once()
