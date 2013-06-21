__author__ = 'rast'

import logging
from os import path, makedirs
import json
#from ThreadedDownload import ThreadedDownload  # buggy like hell
from Download import download
from Api import call_api
from collections import defaultdict
import re

def make_dir(base_dir, name):
    """Make new dir into base dir, return concatenation"""
    if path.exists(base_dir) and path.isdir(base_dir):
        directory = path.join(base_dir, name)
        if path.exists(directory) and path.isdir(directory):
            #raise RuntimeError("Directory already exists: {}".format(directory))
            return directory
        else:
            makedirs(directory)
            return directory
    else:
        raise RuntimeError("Directory does not exist: {}".format(base_dir))

def escape(name):
    """Escape the filename"""
    result =  unicode(re.sub('[^+=\-()$!#%&,.\w\s]', '_', name, flags=re.UNICODE).strip())
    #print("\t{}\n\t{}".format(name, result))
    return result[:100]

class PostParser(object):
    """Parses given post into data lists (text, music, photos, info, etc.)

        parse post - store useful data:
            id (of the post)
            to_id (always user?)
            from_id (post author)
            date (unix timestamp, convert to time)
            text (unicode)
            attachments: (multimedia!)
                type (type name)
                <type>:
                    ...
            comments: (obvious)
                count
                can_post (0|1)
            likes: (people list)
                count
                user_likes (if user liked it)
                can_like
                can_publish
            reposts: (people list)
                count
                user_reposted (0|1)
            signer_id (if group, and if post is signed)
            copy_owner_id (if repost, author's id)
            copy_post_id (if repost, original post id)
            copy_text (if repost, user's response)

"""

    def __init__(self, base_dir, subdir, args):
        """Make directory for current user"""
        self.directory = make_dir(base_dir, subdir)
        self.args = args

    def __call__(self, tpl, raw_data, json_stuff):
        """Process whole post into directory"""
        keys = []
        funcs = []
        self.urls = []
        self.prefix = tpl[0]
        self.number = tpl[1]
        ignore = ['id', 'to_id', 'from_id', 'date',
                  'likes', 'reposts', 'signer_id',
                  'copy_owner_id', 'copy_post_id', 'copy_post_date',
                  'copy_post_type', 'reply_count', 'post_type',
                  'post_source', 'online', 'attachment', 'copy_text',
                  'media', 'can_edit',
                  # comments fix
                  'uid', 'cid', 'reply_to_cid', 'reply_to_uid',
                  'reply_owner_id', 'reply_post_id',
                ]
        for k in raw_data.keys():
            if k in ignore:
                continue
            try:
                f = getattr(self, k)
                keys.append(k)
                funcs.append(f)
            except AttributeError:
                logging.warning("Not implemented: {}".format(k))
        logging.info("Saving: {} for {}".format(', '.join(keys), raw_data['id']))
        self.post_directory = make_dir(self.directory, str(raw_data['id']))

        self.save_raw(json_stuff)
        for (f, k) in zip(funcs, keys):
            f(k, raw_data)

        if self.urls and not self.args.no_download:
            download(self.urls,
                      self.post_directory,
            )

    def text(self, key, raw_data):
        """Save text of the note"""
        text = raw_data['text']
        users_text = raw_data['copy_text']
        stuff = ''
        if raw_data['copy_post_id'] == '':  # user's post
            if text == '':
                return
            else:
                stuff = '<h1>Text:</h1>\n' + text
        else:  # repost
            if text == '':
                if users_text == '':
                    return
                else:
                    stuff = '<h1>Text:</h1>\n' + users_text
            else:
                if users_text == '':
                    stuff = '<h1>Original text:</h1>\n' + text
                else:
                    stuff = "<h1>User's text:</h1>\n" + users_text + \
                            '<h1>Original text:</h1>\n' + text


        f_name = path.join(self.post_directory, 'text.html')
        out_file = open(f_name, 'a+')
        out_file.write(stuff.encode("utf-8"))
        out_file.close()

    def attachments(self, key, raw_data):
        """Save all attachments"""
        f_args = []
        funcs = []
        for att in raw_data[key]:
            t = att['type']
            k = 'dl_' + t
            try:
                f = getattr(self, k)
                f_args.append(att[t])
                funcs.append(f)
            except AttributeError:
                logging.warning("Not implemented downloader: {}".format(t))
        for (f, a) in zip(funcs, f_args):
            f(a)

    def comments(self, key, data):
        """Save all comments"""
        count = data[key]['count']
        if count == 0:
            return
        comments = [count, ]
        for x in xrange(data[key]['count']):
            (comment_data, json_stuff) = call_api("wall.getComments",
                                                [("owner_id", self.args.id),
                                                    ("post_id", data["id"]),
                                                    ("sort", "asc"),
                                                    ("offset", x),
                                                    ("count", 1),
                                                    ("preview_length", 0),
                                                    ("need_likes", 1),
                                                    ("v", 4.4),
                                                 ], self.args)
            comments.append(comment_data[1])
            cdata = defaultdict(lambda: '', comment_data[1])
            pp = PostParser(self.post_directory, 'comments', self.args)
            pp(('comment to ',self.number), cdata, json_stuff)
        json_data = json.dumps(comments, indent=4, ensure_ascii=False)
        f_name = path.join(self.post_directory, 'comments.json')
        out_file = open(f_name, 'a+')
        out_file.write(json_data.encode('utf-8'))
        out_file.close()

    def save_raw(self, data):
        """Save raw post data"""
        data = json.loads(data)
        data = json.dumps(data, indent=4, ensure_ascii=False)

        f_name = path.join(self.post_directory, 'raw.json')
        out_file = open(f_name, 'a+')
        out_file.write(data.encode('utf-8'))
        out_file.close()

    def save_url(self, url, name=None, subdir=''):
        if name is not None:
            name = escape(name)
        self.urls.append((url, name, subdir))
        f_name = path.join(self.post_directory, 'media_urls.txt')
        out_file = open(f_name, 'a+')
        out_file.write(url)
        out_file.write('\n')
        out_file.close()

    def dl_photo(self, data):
        """Download a photo
            vk is a bit crazy, it stores photo in a bunch of sizes:
            src
            src_small
            src_big
            src_xbig
            src_xxbig
            src_xxxbig
            (and what else?)
        """
        sizes = ['src_xxxbig', 'src_xxbig', 'src_xbig', 'src_big', 'src', 'src_small']
        url = None
        for s in sizes:
            try:
                url = data[s]  # try to get biggest size
                break
            except KeyError:
                pass
        if url is None:
            logging.error("Unable to get photo url!")
        else:
            self.save_url(url)

    def dl_link(self, data):
        """Store links in a file"""
        url = data['url']
        f_name = path.join(self.post_directory, 'links.txt')
        out_file = open(f_name, 'a+')
        out_file.write(url)
        out_file.write('\n')
        out_file.close()

    def dl_photos_list(self, data):
        """Download list of photos"""
        for x in data:
            self.dl_photo(x)

    def dl_audio(self, data):
        aid = data["aid"]
        owner = data["owner_id"]
        request = "{}_{}".format(owner, aid)
        (audio_data, json_stuff) = call_api("audio.getById", [("audios", request), ], self.args)
        try:
            data = audio_data[0]
            name = u"{artist} - {title}.mp3".format(**data)
            self.save_url(data["url"], name)
        except IndexError: # deleted :(
            logging.warning("Deleted track: {}".format(str(data)))
            return


        # store lyrics if any
        try:
            lid = data["lyrics_id"]
        except KeyError:
            return
        (lyrics_data, json_stuff) = call_api("audio.getLyrics", [("lyrics_id", lid), ], self.args)
        text = lyrics_data["text"].encode('utf-8')
        name = escape(name)
        f_name = path.join(self.post_directory, name+'.txt')
        # escape!
        out_file = open(f_name, 'a+')
        out_file.write(text)
        out_file.write('\n')
        out_file.close()


    """Download video
        There's a walkaround:
        http://habrahabr.ru/sandbox/57173/
        But this requires authorization as another app

    def dl_video(self, data):

        #print data
    """


    def dl_doc(self, data):
        """Download document (GIFs, etc.)"""
        url = data["url"]
        name = data["title"]
        name, ext = path.splitext(name)
        name = name + '.' + data["ext"]
        self.save_url(url, name)

    def dl_note(self, data):
        """Download note, not comments"""
        (note_data, json_stuff) = call_api("notes.getById", [
            ("owner_id", data["owner_id"]),
            ("nid", data["nid"]),
            ], self.args)
        stuff = u"<h1>{title}</h1>\n{text}".format(**note_data)
        ndir = make_dir(self.post_directory, 'note_'+note_data["id"])
        f_name = path.join(ndir, 'text.html')
        out_file = open(f_name, 'a+')
        out_file.write(stuff.encode("utf-8"))
        out_file.close()

        ndata = json.dumps(note_data, indent=4, ensure_ascii=False)

        f_name = path.join(ndir, 'raw.json')
        out_file = open(f_name, 'a+')
        out_file.write(ndata.encode("utf-8"))
        out_file.close()