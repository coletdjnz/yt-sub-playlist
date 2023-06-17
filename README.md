# YouTube Subscriptions Playlist

Update a playlist with the latest videos from your YouTube subscriptions feed.

```
usage: Update YouTube playlist with latest videos from subscriptions feed [-h] --playlist-id PLAYLIST_ID --cookies COOKIES [--match-filter MATCH_FILTER] [--max-playlist-size MAX_PLAYLIST_SIZE] [--exclude-watched] [-v]

options:
  -h, --help            show this help message and exit
  --playlist-id PLAYLIST_ID
                        YouTube playlist ID to update
  --cookies COOKIES     Path to cookies.txt file
  --match-filter MATCH_FILTER
                        yt-dlp match filter for subscriptions feed
  --max-playlist-size MAX_PLAYLIST_SIZE
                        Maximum size of subscriptions playlist
  --exclude-watched     Exclude watched videos from history in playlist
  -v, --verbose         Verbose output

```

Additionally, a plugin is provided that extracts `is_watched` from YouTube subscriptions 
feed based on the video playback percentage. It should automatically be loaded when you run `update.py`. 
You can use this with `--match-filter` e.g. `--match-filter !is_watched`.

This can be used as an efficient alternative to `--exclude-watched`, which checks the history feed.

Do note this only shows for standard videos i.e. not shorts, so you may need to use `--exclude-watched` if you don't filter those.
## Setup

1. Install requirements
    

        pip install -r requirements.txt

2. Export your YouTube cookies into a file. See [the yt-dlp wiki page](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp) on how to.
3. Create a playlist on YouTube and get its ID from the URL. For example, the ID of `https://www.youtube.com/playlist?list=PL1234567890` is `PL1234567890`.

    **WARNING**: The playlist will be **cleared** and filled with the latest videos from your subscriptions feed.
4. Run the script with the required arguments:


        python update.py --playlist-id PL1234567890 --cookies cookies.txt


## Docker

Provided is a Dockerfile to build a Docker image that runs this script on a cron schedule.

Example usage:


        docker run -v /path/to/cookies.txt:/cookies.txt -e UPDATER_OPTS="--playlist-id PL1234567890" -e CRON_SCHEDULE="1 * * * *"$(docker build -q .)


An example [docker-compose.yml](docker-compose.yml) file is also provided.