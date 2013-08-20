from goose.videos.video_info import VideoInfo
from goose.videos.video_info import youtube

__author__ = 'nimast'

import urllib2
import json

class YouTubeVideoExtractor(object):
    YOUTUBE_VIDEO_INFORMATION_URL_FORMAT = 'http://www.youtube.com/get_video_info?&video_id={0}'
    YOUTUBE_VIDEO_GDATA_INFO_URL_FORMAT = 'http://gdata.youtube.com/feeds/api/videos?alt=json&q={0}'

    def __init__(self, article, config):
        # article
        self.article = article

        # config
        self.config = config

        # cached properties
        self.youtube_info = None
        self.gdata_youtube_info = None
        self.video_id = None

    def get_video_info(self):
        result = self.extract_using_video_information()
        if not result:
            result = self.extract_using_gdata()

        result.provider = 'youtube'
        result.video_id = self.get_video_id()
        return result

    def extract_using_video_information(self):
        youtube_info = self.get_youtube_info()
        if not youtube_info or youtube_info['status'] is 'fail':
            return None

        result = VideoInfo()
        result.preview_image_url = youtube_info['iurlsd'] if youtube_info['iurlsd'] else youtube_info['thumbnail_url']
        result.title = youtube_info['title']

    def extract_using_gdata(self):
        try:
            mediaGroup = self.get_gdata_media_group()
            result = VideoInfo()
            thumbnails = mediaGroup.get('media$thumbnail')
            if thumbnails:
                result.preview_image_url = thumbnails[0]['url']

            title = mediaGroup.get('media$title')
            if title:
                result.title = title['$t']

            description = mediaGroup.get('media$description')
            if description:
                result.description = description['$t']

            return result
        except KeyError:
            return None

    def get_gdata_media_group(self):
        gdata_info = self.get_gdata_youtube_info()
        mediaGroup = gdata_info['feed']['entry'][0]['media$group']
        return mediaGroup

    def get_video_id(self):
        if not self.video_id:
            self.video_id = self.get_video_id_from_url()
        return self.video_id

    def get_youtube_info(self):
        if not self.youtube_info:
            self.youtube_info = self.fetch_youtube_info()
        return self.youtube_info

    def get_gdata_youtube_info(self):
        if not self.gdata_youtube_info:
            self.gdata_youtube_info = self.fetch_gdata_youtube_info()
        return self.gdata_youtube_info

    def fetch_gdata_youtube_info(self):
        gdata_video_info_url = self.YOUTUBE_VIDEO_GDATA_INFO_URL_FORMAT.format(self.get_video_id())
        response = urllib2.urlopen(gdata_video_info_url)
        if response is None:
            return response

        responseJSON = json.loads(response.read())
        return responseJSON

    def fetch_youtube_info(self):
        video_info_url = self.YOUTUBE_VIDEO_INFORMATION_URL_FORMAT.format(self.get_video_id())
        response = urllib2.urlopen(video_info_url)
        if response is None:
            return response
        result = {}
        data = response.read()
        for kvp in data.split('&'):
            tuple = kvp.split('=')
            if tuple:
                if len(tuple) >= 2:
                    result[tuple[0]] = urllib2.unquote(tuple[1])

        return result

    def get_video_id_from_url(self):
        url = self.article.final_url
        if not 'v=' in url:
            return None

        split = url.split('v=')
        if not '&' in split[1]:
            return split[1]

        id = split[1].split('&')
        return id[0]