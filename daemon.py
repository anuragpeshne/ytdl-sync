#!/usr/bin/env python3

import json
import os
import pathlib
import requests
from yt_dlp import YoutubeDL

import re

def get_unique_ordered(items):
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items

def read_config():
    with open(str(pathlib.Path(__file__).parent.absolute()) + '/config.json') as f:
        config = json.load(f)
    return config

def try_get_yt_playlist(page):
    video_ids_str = re.findall("videoId\":\"...........\"", page)
    return [video_id_str.split(":")[1].strip('"') for video_id_str in video_ids_str]

def try_get_yt_search(page):
    video_ids_search_str = re.findall("/watch?v=...........", page)
    return [url_str.split("=")[1] for url_str in video_ids_search_str]

def try_get_zee5(page):
    video_ids = re.findall("href=\"(.*)\" class=\"noSelect content\" data-minutely", page)
    return ["https://www.zee5.com/global" + vids for vids in video_ids]

def sync_item(config):
    root = config['video_store_root']

    for playlist in config['playlists']:
        if playlist['ignore']:
            continue

        print("GET", playlist['url'])
        response = requests.get(playlist['url'])
        page = response.text

        video_urls = []
        if "youtube" in playlist['url']:
            yt_playlist_ids = try_get_yt_playlist(page)
            yt_search_ids = try_get_yt_search(page)
            video_urls.extend(
                    ['https://www.youtube.com/watch?v=' + id_
                     for id_ in yt_playlist_ids])
            video_urls.extend(
                    ['https://www.youtube.com/watch?v=' + id_
                     for id_ in yt_search_ids])
        elif "zee5" in playlist["url"]:
            zee_ids = try_get_zee5(page)
            video_urls.extend(zee_ids)

        unique_video_urls = get_unique_ordered(video_urls)
        to_sync_video_urls = unique_video_urls[:playlist['max_history']]

        playlist_path = os.path.join(root, playlist['name'])
        if not os.path.exists(playlist_path):
            os.makedirs(playlist_path)

        existing_files = os.listdir(playlist_path)
        print(existing_files)
        print(to_sync_video_urls)
        to_download_video_urls = []
        to_delete_files = existing_files
        for to_sync_video_url in to_sync_video_urls:
            found = False
            for existing_file in existing_files:
                existing_id = re.findall("\[(.*)\]", existing_file)[0]
                if existing_id in to_sync_video_url:
                    found = True
                    to_delete_files.remove(existing_file)
            if not found:
                to_download_video_urls.append(to_sync_video_url)

        print("Will download files: ", ','.join(to_download_video_urls))

        for video_url in to_download_video_urls:
            ydl_opts = {
                'outtmpl': playlist_path + '/' + '%(upload_date>%Y-%m-%d)s %(title)s [%(id)s].%(ext)s',
                'simulate': False,
                'prefer_free_formats': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        print("Will delete files: ", ','.join(to_delete_files))
        for oldfile in to_delete_files:
            os.remove(os.path.join(playlist_path, oldfile))


config = read_config()
sync_item(config)
