import praw
import os
import csv
import pathlib
import re
import requests
import shutil
import json
import youtube_dl
#import subprocess

#Information about the application registered on Reddit
clientid = ''
clientsecret = ''
useragent = ''

#Recognised file formats for which download will be attempted
file_formats = ['jpg', 'png', 'gif', 'bmp', 'mp4', 'jpeg', 'gifv']
#Invalid characters for a Windows file name
invalid = "<>:\"/\\|?*"

reddit = praw.Reddit(
        client_id=clientid,
        client_secret=clientsecret,
        user_agent=useragent,
)

dir = os.path.dirname(__file__)

#Collect a list of successfully processed shortlink codes
if os.path.isfile(os.path.join(dir, 'done.txt')):
        with open(os.path.join(dir, 'done.txt'), 'r') as file:
                done = file.read().splitlines()
else:
        done = []

def namefix(name, format, sub, opt=''):
        '''
        Return an appropriate file name (including full path) avoiding duplicates.
        name = the Reddit post title
        format = extension of the file
        sub = name of the subreddit
        opt = any optional text to add after the name -- this is currently deprecated as v.redd.it is handled by youtube-dl
        '''
        for c in invalid:
                name = name.replace(c, '')
        name.strip()
        fullname = name + opt + '.' + format
        if os.path.isfile(os.path.join(dir, sub, fullname)):
                i = 2
                while True:
                        newname = name + opt + ' (' + str(i) + ').' + format
                        if os.path.isfile(os.path.join(dir, sub, newname)):
                                i+=1
                        else:
                                break
                fullname = newname
        return os.path.join(dir, sub, fullname)

def success(code):
        '''
        Used after the shortlink is successfully downloaded, to prevent future duplicates
        '''
        with open(os.path.join(dir, 'done.txt'), 'a') as file:
                file.write(f"{code}\n")

def fail(code, thread, url, error_code=''):
        '''
        Used if requesting a file returns a response other than 200.
        Add details to a log file: Reddit thread name and shortlink code, url of the linked content, and response code
        '''
        with open(os.path.join(dir, 'issues.txt'), mode='a', encoding='utf_8') as file:
                if error_code:
                        file.write(f"{code}\n{thread.title}\n{url}\nStatus code: {error_code}\n\n")
                else:
                        file.write(f"{code}\n{thread.title}\n{url}\nNot downloaded\n\n")

def CreateFile(code):
        '''
        The bulk of the program: attempt to download a shortlink with the given code.
        If it is a text post (self post), create a text file with the content of the post.
        If it is a link post, attempt to download its content - this is done on a case-by-case basis depending on the type of link
        Currently supported:
        - text post (self posts)
        - direct link to files with an extension listed in file_formats that can be freely accessed (i.e. don't return an error code, e.g. 403)
        - crosspost pointing to a supported type of post
        - imgur.com or i.imgur.com single post link (i.e. albums are not supported), including .gifv
        - gfycat.com link
        - youtube.com or youtu.be link (requires youtube-dl)
        - v.redd.it link (requires youtube-dl)
        - streamable.com (requiers youtube-dl)
        '''
        thread = reddit.submission(id = code)

        if hasattr(thread, 'crosspost_parent'):
                '''
                If the post is a crosspost, grab the corresponding link.
                If the original content is successfully downloaded, it will be added to the list of completed files and will be skipped on the next run.
                '''
                newcode = thread.crosspost_parent[3:]
                if newcode in done:
                        with open(os.path.join(dir, 'done.txt'), 'a') as file:
                                        file.write(code + '\n')
                code = newcode
                thread = reddit.submission(id = code)

        sub = thread.subreddit_name_prefixed[2:]

        '''
        This parameter is used when downloading videos using youtube-dl (pretty much anything that is not a direct link to a video file)
        youtube-dl will attempt to download the best format for the video
        ydl_opts can be changed to specify if you have any restriction (e.g. max 1080p)
        '''
        ydl_opts = {'outtmpl': namefix(thread.title, 'mp4', sub)}

        #Create a folder for the subreddit if it does not exist yet
        pathlib.Path(os.path.join(dir, sub)).mkdir(parents=True, exist_ok=True)
        if thread.is_self:
                with open(namefix(thread.title, 'txt', sub), mode='w', encoding='utf_8') as file:
                        file.write(thread.selftext)
                success(code)
        else:
                url = thread.url

                #Link to an imgur single post page -> extract the direct URL
                if imgur_ID:=re.match(r"^https://imgur\.com/(\w+)$", url):
                        #Unsure if imgur only uses .png to store pictures, change if needed
                        url = f"https://i.imgur.com/{imgur_ID[1]}.png"

                #Link to a 'deformed' imgur file (e.g. ending with .png?1) -> extract the correct URL
                if imgur_link:=re.match(r"^(https://i.imgur.com/\w+\.\w{3,4})", url):
                        url = imgur_link[1]

                #Direct link to a supported format
                if (m:=re.match(r"^.*\.(\w+)$", url)) and (ext:=m[1]) in file_formats:
                        #gifv are basically mp4, so we can grab that directly
                        if ext == 'gifv':
                                url = url[:-4] + 'mp4'
                                ext = 'mp4'
                        r = requests.get(url, stream=True)
                        if r.status_code == 200:
                                with open(namefix(thread.title, ext, sub), 'wb') as file:
                                        r.raw.decode_content = True
                                        shutil.copyfileobj(r.raw, file)
                                success(code)
                        else:
                                fail(code, thread, url, r.status_code)
                #Link to v.redd.it content
                elif re.match(r"^https://v\.redd\.it/(\w+)$", url):
                        r = requests.get(url)
                        if r.status_code == 200:
                                video_url = re.match(r"^(.*)&", thread.secure_media['reddit_video']['hls_url'])[1]
                                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                        ydl.download([video_url])
                                success(code)
                        else:
                                fail(code, thread, url, r.status_code)
                        '''
                        #This is left in case youtube-dl breaks - it requires some tweaking to correctly obtain the audio link - if it exists!
                        video_url = thread.secure_media['reddit_video']['fallback_url']
                        audio_url = f'{url}/audio' #<-- requires parsing of the u3m8 file to grab the correct link (if it exists)
                        print(video_url)
                        print(audio_url)
                        checks = True
                        vdir = namefix(thread.title, 'mp4', sub, '_video')
                        adir = namefix(thread.title, 'mp3', sub, '_audio')
                        with open(vdir, 'wb') as file:
                                print('Downloading Video...', end='', flush = True)
                                response = requests.get(video_url)
                                if(response.status_code == 200):
                                        file.write(response.content)
                                        print('\rVideo Downloaded...!')
                                else:
                                        checks = False
                                        print(response.status_code)
                                        print('\rVideo Download Failed..!')
                        with open(adir, 'wb') as file:
                                print('Downloading Audio...', end = '', flush = True)
                                response = requests.get(audio_url)
                                if(response.status_code == 200):
                                        file.write(response.content)
                                        print('\rAudio Downloaded...!')
                                else:
                                        checks = False
                                        print('\rAudio Download Failed..!')
                        if checks:
                                subprocess.call([ffmpeg_path,'-i',vdir,'-i',adir,'-map','0:v','-map','1:a','-c:v','copy',namefix(thread.title, 'mp4', sub)])
                                os.remove(vdir)
                                os.remove(adir)
                                with open(os.path.join(dir, 'done.txt'), 'a') as file:
                                        file.write(code + '\n')
                        '''
                #Link to youtube.com
                #I did not find exact rules about what is allowed for the video ID string, so I only excluded '&', which normally separates other 'properties'
                elif youtube_url:=re.match(r"^(https://www\.youtube\.com/watch\?v=[^&]+)", url):
                        video_url = youtube_url[1]
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_url])
                        success(code)
                #Link to youtu.be
                #As for youtube.com links, I put minimal restrictions on the video ID
                elif youtube_ID:=re.match(r"^https://youtu\.be/([^&]+)", url):
                        video_url = f"https://www.youtube.com/watch?v={youtube_ID[1]}"
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_url])
                        success(code)
                #Link to streamable.com
                #Not sure if there is any restriction on video ID, the regex can be changed accordingly if needed
                elif streamable_link:=re.match(r"^(https://streamable\.com/\w+)", url):
                        video_url = streamable_link[1]
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_url])
                        success(code)
                #Link to gfycat.com
                elif gfycat_ID:=re.match(r"^https://gfycat\.com/(\w+)", url):
                        r = requests.get(f"https://api.gfycat.com/v1/gfycats/{gfycat_ID[1]}")
                        if r.status_code == 200:
                                r = json.loads(r.content)
                                url = r['gfyItem']['content_urls']['mp4']['url']
                                r = requests.get(url, stream=True)
                                if r.status_code == 200:
                                        with open(namefix(thread.title, ext, sub), 'wb') as file:
                                                r.raw.decode_content = True
                                                shutil.copyfileobj(r.raw, file)
                                        success(code)
                                else:
                                        fail(code, thread, url, r.status_code)
                        else:
                                fail(code, thread, url, r.status_code)
                else:
                        fail(code, thread, url)

with open('post_votes.csv', mode = 'r', encoding = 'utf_8') as csv_file:
        '''
        Parse a csv file and attempt to download the linked content.
        The current format used by Reddit is "id,permalink,direction":
                id = code for the shortlink
                permalink = full link
                direction = up or down (upvote or downvote)
        '''
        csv_reader = csv.reader(csv_file, delimiter = ',')
        line = 1
        for entry in csv_reader:
                if entry[2] == 'up' and entry[0] not in done:
                                CreateFile(entry[0])
                line += 1
