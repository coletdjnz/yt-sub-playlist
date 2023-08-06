import sys
import time
import argparse
from yt_dlp import YoutubeDL
from yt_dlp.utils import (
    match_filter_func
)
from loguru import logger

GLOBAL_YDL_OPTS = {
    'quiet': True,
    'verbose': False,
    'extractor_retries': 5,
    'logger': logger
}


def get_new_subs(match_filter=None):
    ydl_opts = {
        **GLOBAL_YDL_OPTS,
        'extractor_args': {
            'youtubetab': {'approximate_date': ['yes']}
        },
        'extract_flat': True,
        'lazy_playlist': True
    }
    mmf = match_filter_func(match_filter)
    if not mmf:
        mmf = lambda x: False
    with YoutubeDL(ydl_opts) as ydl:
        logger.info('Fetching latest videos in subscriptions feed...')
        data = ydl.extract_info('https://www.youtube.com/feed/subscriptions', process=False, download=False)
        total = 0
        for info in data['entries']:
            res = mmf(info)
            total += 1
            if not res:
                yield info, total
            else:
                logger.debug(res)


def get_playlist_videos(playlist_id):
    ydl_opts = {
        **GLOBAL_YDL_OPTS,
        'extractor_args': {
            'youtubetab': {'approximate_date': ['yes']}  # requires latest yt-dlp master
        },
        'extract_flat': True,
        'ignoreerrors': True  # yt temporary broken
    }
    with YoutubeDL(ydl_opts) as ydl:
        logger.info('Fetching existing list of videos in playlist..')
        data = ydl.extract_info(f'https://www.youtube.com/playlist?list={playlist_id}', process=True, download=False)
        logger.debug(f'Retrieved {len(data["entries"])} videos from playlist')
        return data['entries']


def get_recent_watched():
    ydl_opts = {
        **GLOBAL_YDL_OPTS,
        'extractor_args': {
            'youtubetab': {'approximate_date': ['yes']}  # requires latest yt-dlp master
        },
        'extract_flat': True,
        'lazy_playlist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        logger.info(f'Initializing YouTube history fetcher')
        data = ydl.extract_info(f'https://www.youtube.com/feed/history', process=False, download=False)
        return data['entries']


def clear_playlist(playlist_id, ytie, ytcfg: dict):
    playlist_video_ids = [info['id'] for info in get_playlist_videos(playlist_id) if info]
    headers = ytie.generate_api_headers(ytcfg=ytcfg)
    logger.info(f'Clearing playlist of {len(playlist_video_ids)} videos...')
    cleared = 0
    for chunk in (playlist_video_ids[i:i + 100] for i in range(0, len(playlist_video_ids), 100)):
        ytie._extract_response(
            item_id=playlist_id, ep='browse/edit_playlist', ytcfg=ytcfg, headers=headers, fatal=False,
            note='Clearing playlist',
            query={
                'actions': [
                    {
                        'action': 'ACTION_REMOVE_VIDEO_BY_VIDEO_ID',
                        'removedVideoId': video_id
                    }
                    for video_id in chunk],
                'playlistId': playlist_id,
            })
        cleared += len(chunk)
        logger.info(f'Clearing playlist: {cleared}/{len(playlist_video_ids)}')
        time.sleep(5)

    if len(get_playlist_videos(playlist_id)) != 0:
        raise Exception('Failed to clear playlist')
    logger.info(f'Playlist cleared successfully')


def rewrite_playlist(playlist_id, new_video_ids):
    logger.info(f'Adding {len(new_video_ids)} videos to playlist')
    with YoutubeDL(GLOBAL_YDL_OPTS) as ydl:
        ytie = ydl.get_info_extractor('YoutubeTab')
        _, ytcfg = ytie._extract_data('https://www.youtube.com', item_id='ytcfg', fatal=False)

        clear_playlist(playlist_id, ytie, ytcfg)
        logger.info(f'Adding new videos to playlist')

        ytie._extract_response(
            item_id=playlist_id, ep='browse/edit_playlist', ytcfg=ytcfg, headers=ytie.generate_api_headers(ytcfg=ytcfg),
            fatal=True, note='Writing new videos to playlist',
            query={
                'actions': [
                    {
                        'action': 'ACTION_ADD_VIDEO',
                        'addedVideoId': video_id
                    }
                    for video_id in new_video_ids],
                'playlistId': playlist_id,
            })


def run(playlist_id, max_playlist_size=300, exclude_watched=False, match_filter=None):
    new_sub_iter = get_new_subs(match_filter=match_filter)
    watched_iter = get_recent_watched()
    watched = set()
    new_videos = dict()

    get_new_video_ids = lambda nv: list(reversed(sorted(nv.keys(), key=lambda x: nv.get(x) or 0)))

    while len(new_videos) < max_playlist_size:
        # Get a little more, so we can account for YouTube history not showing all watched videos
        while len(new_videos) < max_playlist_size + ((0.5*max_playlist_size) if exclude_watched else 0):
            info, total = next(new_sub_iter)
            video_id, timestamp = info['id'], info.get('timestamp')

            # FIXME: this grabs way too much videos from history while still missing some
            # Issue: yt-dlp doesn't get any sort of date from history feed
            if exclude_watched:
                # lazy workaround: get a little more of history than subscriptions fetched
                while len(watched) < int(total+total*((1.01**(-0.125*total))+1.1)+100):
                    watched.add(next(watched_iter)['id'])
                if video_id in watched:
                    continue
            new_videos[video_id] = timestamp

        new_videos_ids = get_new_video_ids(new_videos)
        rewrite_playlist(playlist_id, new_videos_ids)

        if exclude_watched:
            logger.info('Checking playlist for watched videos')

            playlist_videos = get_playlist_videos(playlist_id)
            for info in playlist_videos:
                if match_filter_func('!is_watched')(info):
                    # The video is already watched??
                    logger.debug(f'Video {info["id"]} ({info["title"]}) is already watched!?')
                    del new_videos[info['id']]
                    watched.add(info['id'])
        logger.debug(f'We have collected {len(new_videos)} videos from subscriptions feed so far (need: {max_playlist_size})')

    if exclude_watched:
        # Now all the videos we have should be unwatched. So rewrite the playlist with the latest videos
        logger.info(f'Rewriting playlist with {max_playlist_size} unwatched videos from subscriptions feed')
        rewrite_playlist(playlist_id, get_new_video_ids(new_videos)[:max_playlist_size])

    logger.info(f'Updated playlist with latest videos from subscriptions feed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Update YouTube playlist with latest videos from subscriptions feed')
    parser.add_argument('--playlist-id', required=True, help='YouTube playlist ID to update')
    parser.add_argument('--cookies', required=True, help='Path to cookies.txt file')
    parser.add_argument('--match-filter', help='yt-dlp match filter for subscriptions feed')
    parser.add_argument('--max-playlist-size', type=int, default=300, help='Maximum size of subscriptions playlist')
    parser.add_argument('--exclude-watched', action='store_true', help='Exclude watched videos from history in playlist', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output', default=False)

    args = parser.parse_args()
    GLOBAL_YDL_OPTS['cookiefile'] = args.cookies
    logger.remove()
    if args.verbose:
        logger.add(sys.stderr, level='DEBUG')
        GLOBAL_YDL_OPTS['verbose'] = True
        GLOBAL_YDL_OPTS['quiet'] = False
    else:
        logger.add(sys.stderr, level='INFO')
    logger.debug(args)

    run(playlist_id=args.playlist_id, max_playlist_size=args.max_playlist_size, exclude_watched=args.exclude_watched, match_filter=args.match_filter)
