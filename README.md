# What is this

Reddit only displays the latest 1000 items of most lists, including the list of threads you upvoted, and there is no way to access other items on said lists through the website - presumably because of some design decision.

However, such data is not lost, and it is possible to file a GDPR request to retrieve all of it. In particular, your up- and downvoted threads are listed in the post_votes.csv file in the format

```id, link, direction```

i.e. id used for the short link, full link, up or down (direction of the vote)

This tool is designed to fetch all the links of your upvoted threads from the csv and attempt to download their content, sorted by subreddit.

This was designed around my specific use-case, where most link are text posts, picture links, or links to an embedded video. Other uses may be added on a case-by-case basis if deemed worthy.

# How to use it

It requires Python and the modules listed at the top of the file.

You also need to [register your own app here](https://old.reddit.com/prefs/apps/): edit the clientid, clientsecret, and useragent values with the information unique to your app.

Place the post_votes.csv and RedditVotedDownload.py files in the same parent folder where you want your collection to be, and run the .py file. Ideally you want to run it on a console in order to more easily identify errors that may have occurred.

If anything runs smoothly, it will also produce two files in the parent folder:
* 'done.txt' includes a list of all the links that were successfully downloaded. If an id is deleted from the list, running the program again will re-attempt the download, possibly generating duplicate entries.
* 'issues.txt' includes a lists of all the links that were not downloaded. If this is due to error with the request, the error code will be listed (likely 403 or 404), otherwise a generic 'Not downloaded' will be logged. The latter case is generally for links not covered by the program use-case (e.g. generic html pages, imgur albums).

# What can be downloaded

Currently supported links:
* text post (self posts)
* direct link to files with an extension listed in file_formats that can be freely accessed (i.e. don't return an error code, e.g. 403)
* crosspost pointing to a supported type of post
* imgur.com or i.imgur.com single post link (i.e. albums are not supported), including .gifv
* gfycat.com link
* youtube.com or youtu.be link (requires youtube-dl)
* v.redd.it link (requires youtube-dl)
* streamable.com link (requiers youtube-dl)
