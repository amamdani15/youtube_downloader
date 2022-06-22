# Importing libraries
import sys
# import pytube # library for downloading youtube videos
import yt_dlp as youtube_dl
import json
import os
from subprocess import run
from slack_webhook import Slack
  
db_location = ''
video_dir = '.'
slack = Slack(url='https://hooks.slack.com/services/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')



with open(f'{db_location}db.json') as f:
	db = json.load(f)

def add_playlist(url, mapped_dir):
	if url not in db['playlists_watching']:
		db['playlists_watching'].append(url)
		if url in db['playlist_mapping']:
			print(f"this url has been moniored before, will be using the same directory {db['playlist_mapping'][url]}")
		else:
			db['playlist_mapping'][url] = mapped_dir
			db['downloaded'][url]=[]
	else:
		print("already monitoring playlist")

def remove_playlist(url):
	if url in db['playlists_watching']:
		db['playlists_watching'].remove(url)
		print(f"removed {url} from monitored playlists")
	else:
		print("was not monitoring provided url for playlist.")

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')



def download_new():
	for url in db['playlists_watching']:

		ydl_opts_playlist = {
			'extract_flat': True,
			'progress_hooks': [my_hook],
			'quiet': True,
		}
		ydl_opts_formats = {
			'extract_flat': True,
			'progress_hooks': [my_hook],
			'simulate': True,
			'quiet': True,
		}

		ydl_opts_videos_1080 ={
			'format': "bestvideo[vcodec!*=av01][height<=1080]+bestaudio[ext=m4a]/bestvideo[vcodec!*=av01][height<=1080]+bestaudio/best[vcodec!*=av01][height<=1080]",
			'progress_hooks': [my_hook],
			'outtmpl': f"{video_dir}{db['playlist_mapping'][url]}/%(title)s.%(ext)s",

		}
		ydl_opts_videos_max ={
			'format': "bestvideo[vcodec!*=av01][height>=1080]+bestaudio[ext=m4a]/bestvideo[vcodec!*=av01][height>=1080]+bestaudio/best[vcodec!*=av01][height>=1080]",
			'progress_hooks': [my_hook],
			'outtmpl': f"{video_dir}{db['playlist_mapping'][url]}_max/%(title)s.%(ext)s",
		}

		print(f'Starting to check playlist {url}')
		with youtube_dl.YoutubeDL(ydl_opts_playlist) as ydl_playlist:
			p = ydl_playlist.extract_info(url, download=False)
			for video in p['entries']:
				if video['url'] not in db['downloaded'][url]:
					print(f"Downloading {video['title']}.")
					download_greater_than_1080 = False
					with youtube_dl.YoutubeDL(ydl_opts_formats) as ydl_video_formats:
						formats = ydl_video_formats.extract_info(video['url'])
						maxResolution = max(filter(None, [d['height'] for d in formats['formats']]))
						if maxResolution > 1080:
							download_greater_than_1080 = True
					if download_greater_than_1080:
						print("Downloading quality higher than 1080p")
						with youtube_dl.YoutubeDL(ydl_opts_videos_max) as ydl_video_max:
							ydl_video_max.download([video['url']])
					print("downloading 1080p or lower quality")
					with youtube_dl.YoutubeDL(ydl_opts_videos_1080) as ydl_video_1080:
						ydl_video_1080.download([video['url']])
					db['downloaded'][url].append(video['url'])
					with open(f'{db_location}db.json', "w") as f:
						json.dump(db, f)
					slack.post(text='downloaded new video to directory: ' + db['playlist_mapping'][url] + ' https://youtube.com/watch?v=' + video['url'])
				else:
					print(f"already downloaded {video['url']}")


def manual_download(url):
	dir = video_dir + '/manual_downloads'
	download_greater_than_1080 = False

	ydl_opts_manual = {
	'extract_flat': True,
	'progress_hooks': [my_hook],
	'simulate': True,
	'quiet': True,
	}
	ydl_opts_formats = {
			'extract_flat': True,
			'progress_hooks': [my_hook],
			'simulate': True,
			'quiet': True,
	}

	ydl_opts_videos_1080 ={
			'format': "bestvideo[vcodec!*=av01][height<=1080]+bestaudio[ext=m4a]/bestvideo[vcodec!*=av01][height<=1080]+bestaudio/best[vcodec!*=av01][height<=1080]",
			'progress_hooks': [my_hook],
			'outtmpl': f"{video_dir}/%(title)s.%(ext)s",

		}
	ydl_opts_videos_max ={
			'format': "bestvideo[vcodec!*=av01][height>=1080]+bestaudio[ext=m4a]/bestvideo[vcodec!*=av01][height>=1080]+bestaudio/best[vcodec!*=av01][height>=1080]",
			'progress_hooks': [my_hook],
			'outtmpl': f"{video_dir}_max/%(title)s.%(ext)s",
		}

	with youtube_dl.YoutubeDL(ydl_opts_manual) as ydl_video:
		p = ydl_video.extract_info(url, download=False)
		# print(p)
		print(f"Downloading {p['title']}.")
		with youtube_dl.YoutubeDL(ydl_opts_formats) as ydl_video_formats:
			maxResolution = max(filter(None, [d['height'] for d in p['formats']]))
			if maxResolution > 1080:
				download_greater_than_1080 = True
			if download_greater_than_1080:
				print("Downloading quality higher than 1080p")
				# with youtube_dl.YoutubeDL(ydl_opts_videos_max) as ydl_video_max:
				# 	ydl_video_max.download([url])
			print("downloading 1080p or lower quality")
			with youtube_dl.YoutubeDL(ydl_opts_videos_1080) as ydl_video_1080:
				ydl_video_1080.download([url])
			slack.post(text='downloaded new video to directory: ' + ' https://youtube.com/watch?v=' + p['url'])					

def main(argv):

	if argv[0] == "add_playlist":
		add_playlist(argv[1],argv[2])

	elif argv[0] == "download_new":
		download_new()

	elif argv[0] == "remove_playlist":
		remove_playlist(argv[1]) 

	elif argv[0] == "manual_download":
		manual_download(argv[1]) 

	with open(f'{db_location}db.json', "w") as f:
		json.dump(db, f)


if __name__ == "__main__":
   main(sys.argv[1:])
