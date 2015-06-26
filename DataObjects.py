__author__ = 'rast'

import logging
import datetime

class WallPost:
    """
    Represents single post on user's or group's wall
    See https://vk.com/dev/post
    """
    def __init__(self, rawPost):
        # Post ID on the wall
        self.id = rawPost["id"]

        # Date the post was added
        self.date = datetime.datetime.fromtimestamp(rawPost["date"])

        # Text of the post
        self.text = rawPost["text"]

        # Text of the comment added when reposting (if the post was reposted from someone else's wall)
        self.copyText = rawPost.get("copy_text")

        self.repostData = []
        for repostData in rawPost.get("copy_history", []):
            self.repostData.append(WallPost(repostData))

        self.attachments = []
        for attachment in rawPost.get("attachments", []):
            attType = attachment["type"]
            if attType == "photo":
                self.attachments.append(Photo(attachment["photo"]))
            elif attType == "video":
                self.attachments.append(Video(attachment["video"]))
            elif attType == "doc":
                self.attachments.append(Doc(attachment["doc"]))
            elif attType == "audio":
                self.attachments.append(Audio(attachment["audio"]))
            elif attType == "note":
                self.attachments.append(Note(attachment["note"]))
            elif attType == "link":
                self.attachments.append(Link(attachment["link"]))
            else:
                logging.fatal("Not implemented attachment type: {}".format(attType))

        """
        Comments are:
            id
            date
            text
            attachments!
            so... they are WallPost too!
            but we need to get them separately
        """



class Photo:
    def __init__(self, data):
        """
        VK is crazy and returns photo links in random keys:
            photo_75: 'https://pp.vk.me/....jpg',
            photo_130: 'https://pp.vk.me/....jpg',
            photo_604: 'https://pp.vk.me/....jpg',
            photo_807: 'https://pp.vk.me/....jpg',
            photo_1280: 'https://pp.vk.me/....jpg',
            photo_2560: 'https://pp.vk.me/....jpg'
        Need to parse key with max suffix

        And sometimes there is text under photo with link to original uploaded image
        """
        self.id = data["id"]
        self.albumId = data["album_id"]

        self.url = None
        text = data.get("text")
        if text:
            self.url = self._parseText(text)
        if not self.url:  # failed
            self.url = self._parseDictKeys(data)

    def _parseText(self, text):
        parts = text.split("Original: ", 1)
        if len(parts) != 2:
            return None
        return parts[1]

    def _parseDictKeys(self, data):
        keys = filter(lambda x: x.startswith("photo_"), data.keys())
        maxSuffix = max(map(lambda x: int(x.split("_", 1)[1]), keys))
        preferredKey = "photo_{}".format(maxSuffix)
        return data[preferredKey]

class Video:
    def __init__(self, data):
        self.id = data["id"]
        self.ownerId = data["owner_id"]
        logging.fatal("Not implemented")

class Audio:
    def __init__(self, data):
        self.id = data["id"]
        self.ownerId = data["owner_id"]
        self.url = data["url"]
        self.artist = data["artist"]
        self.name = data["title"]

class Doc:
    def __init__(self, data):
        self.id = data["id"]
        self.ownerId = data["owner_id"]
        self.url = data["url"]
        self.filename = data["title"]  # seems to be filename. maybe.
        self.extension = data["ext"]  # file extension

class Link:
    def __init__(self, data):
        self.title = data["title"]
        self.url = data["url"]

class Note:
    def __init__(self, data):
        self.id = data["id"]
        self.ownerId = data["owner_id"]
        self.title = data["title"]
        self.viewUrl = data["view_url"]
