from yt_dlp.extractor.youtube import YoutubeTabIE
from yt_dlp.utils import traverse_obj


class YoutubeWatchStatusIE(YoutubeTabIE, plugin_name='watched'):

    def _extract_video(self, renderer):
        info = super()._extract_video(renderer)
        if traverse_obj(renderer, ('thumbnailOverlays', ..., 'thumbnailOverlayResumePlaybackRenderer'), get_all=False):
            info['is_watched'] = True
        return info


__all__ = []
