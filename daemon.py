#!/usr/bin/env python

import json
import os
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
    with open('config.json') as f:
        config = json.load(f)
    return config

def sync_item(config):
    root = config['video_store_root']
    
    for playlist in config['playlists']:
        print("GET", playlist['url'])
        response = requests.get(playlist['url'])
        page = response.text

        video_ids_str = re.findall("videoId\":\"...........\"", page)
        video_ids = [video_id_str.split(":")[1].strip('"') for video_id_str in video_ids_str]

        unique_video_ids = get_unique_ordered(video_ids)
        to_sync_video_ids = unique_video_ids[:playlist['max_history']]
        print("unique video ids parsed: ", len(unique_video_ids))
        
        playlist_path = os.path.join(root, playlist['name'])
        if not os.path.exists(playlist_path):
            os.makedirs(playlist_path)

        existing_files = os.listdir(playlist_path)
        to_download_video_ids = []
        to_delete_files = existing_files
        for to_sync_video_id in to_sync_video_ids:
            found = False
            for existing_file in existing_files:
                if to_sync_video_id in existing_file:
                    found = True
                    to_delete_files.remove(existing_file)
            if not found:
                to_download_video_ids.append(to_sync_video_id)

        print("Will download files: ", ','.join(to_download_video_ids))

        for video_id in to_download_video_ids:
            ydl_opts = {
                'outtmpl': playlist_path + '/' + '%(upload_date>%Y-%m-%d)s %(title)s [%(id)s].%(ext)s',
                'simulate': False,
                'prefer_free_formats': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=' + video_id])

        print("Will delete files: ", ','.join(to_delete_files))
        for oldfile in to_delete_files:
            os.remove(oldfile)


config = read_config()
sync_item(config)
clean_old_items(config)
