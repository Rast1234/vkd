__author__ = 'rast'

import logging
from os import path, makedirs
import json
from ThreadedDownload import ThreadedDownload

def make_dir(base_dir, name):
    """Make new dir into base dir, return concatenation"""
    if path.exists(base_dir) and path.isdir(base_dir):
        directory = path.join(base_dir, name)
        if path.exists(directory) and path.isdir(directory):
            raise RuntimeError("Directory already exists: {}".format(directory))
        else:
            makedirs(directory)
            return directory
    else:
        raise RuntimeError("Directory does not exist: {}".format(base_dir))

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
    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if not hasattr(cls, '_instance'):
            cls._instance = super(PostParser, cls).__new__(cls, *args, **kwargs)
        return cls._instance  # call __init__

    def __init__(self, base_dir, user_id):
        """Make directory for current user"""
        self.directory = make_dir(base_dir, user_id)

    def __call__(self, raw_data, json_stuff):
        """Process whole post into directory"""
        keys = []
        funcs = []
        self.urls = []
        ignore = ['id', 'to_id', 'from_id', 'date',
                  'likes', 'reposts', 'signer_id',
                  'copy_owner_id', 'copy_post_id', 'copy_post_date',
                  'copy_post_type', 'reply_count', 'post_type',
                  'post_source', 'online', 'attachment', 'copy_text',
                  'media'
                ]
        # WTF are online, attachment, post_type fields?
        for k in raw_data.keys():
            if k in ignore:
                continue
            try:
                f = getattr(self, k)
                keys.append(k)
                funcs.append(f)
            except AttributeError:
                logging.warning("Not implemented: {}".format(k))
        logging.info("Saving: {} for post {}".format(', '.join(keys), raw_data['id']))
        self.post_directory = make_dir(self.directory, str(raw_data['id']))

        self.save_raw(json_stuff)
        for (f, k) in zip(funcs, keys):
            f(k, raw_data)

        #download urls in threads
        #args: urls=[], destination='.', directory_structure=False, thread_count=5, url_tries=3
        downloader = ThreadedDownload(self.urls,
                                      self.post_directory,
                                      False,
                                      8,
                                      3
        )

        print 'Downloading %s files' % len(self.urls)
        downloader.run()

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
        out_file = open(f_name, 'w+')
        out_file.write(stuff.encode("utf-8"))
        out_file.close()

    def attachments(self, key, raw_data):
        """Download and save all attachments"""
        f_args = []
        funcs = []
        for att in raw_data[key]:
            logging.debug(str(att.keys()) + " => " + att['type'])
            t = att['type']
            k = 'dl_' + t
            try:
                f = getattr(self, k)
                f_args.append(att[t])
                funcs.append(f)
            except AttributeError:
                logging.warning("Not implemented downloader: {}".format(t))
        for (f, a) in zip (funcs, f_args):
            f(a)

    def save_raw(self, data):
        """Save raw post data"""
        data = json.loads(data)
        data = json.dumps(data, indent=4, ensure_ascii=False)

        f_name = path.join(self.post_directory, 'raw.json')
        out_file = open(f_name, 'w+')
        out_file.write(data.encode('utf-8'))
        out_file.close()

    def save_url(self, url):
        self.urls.append(url)
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
        url  = None
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
        print data