vkd (en)
===

VK dumper - save stuff your vk.com to local drive
---

**Features:**

* Download almost anything from your wall:
    * Posts
    * Multimedia attachments
    * Comments
    * Comment attachments
    * Some extra raw info for your history
* Download audio tracks
    * Correct fime naming
    * Text stored also (if available)
    * **TODO:** sort by playlists
* **TODO:** Downloading video 
* **TODO** Downloading notes

**Known limitations, bugs and other considerations:**

* Unable to download videos (Someone need this?)
* Unable to download note comments (Maybe an unneeded feature?)
* Tested on a particular user, not tested for a group
* Can't grant access by itself, so you need to enter auth token manually (see below)
* Not tested on Windows

Usage and requirements
---
You need **Python 2.7** only for this to work. Should work under different OSes, not tested.  
For all available list of arguments see `--help` output.
Essential options described below:
* `-i / --id`    User ID or group ID to dump. Group ID should be prefixed with `-`, e.x. `-123456`
* `-a / --app_id`	Application ID, see below.
* `-m / --mode` Working mode. Supported modes are `wall` and `audio`, you may specify both at the same time. Script will download your wall, or audio tracks, respectively.

How-to
---
1. Clone this repo
2. Register your own [vk app here](https://vk.com/editapp?act=create) to get Application ID. Be sure to select **standalone** application type.
3. Write down your Application ID (ex. **1234567**).
4. Find your [profile ID here](https://vk.com/settings) near the bottom of the page. For example, **1**.
5. What do you want to dump? `audio`, `wall` or both?
6. Now specify everything to the script:

        main.py --app_id 1234567 --id 1 --mode wall audio

7. Script will ask you to go to a given URL, so, do it :)
8. Give access for this application to your profile.
9. You will be redirected to a white page with text about security.
10. Copy URL of this page. Yeah, I know, VK tells you not to do that for security reasons. But this application is your just registered app, and this script is open-source, so go and read sources if you don't trust me..
11. Paste URL int script, it is waiting for you!
12. Enjoy downloading process. This will take a lot of time, though.

You may set limits of posts and audio tracks to download, change directory to store data, etc. See `--help` output.

Bugs
---
Any bug reports, pul requests appreciated. Open an issue here or [PM me](https://vk.com/rast1234)

Credits:
---

Me :)  
http://habrahabr.ru/post/143972/ (call_api function)  
http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python  
Pavel Durov for great social network and its buggy API :)  
    
