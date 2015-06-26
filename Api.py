# -*- coding: utf-8 -*-

__author__ = 'rast'

import json
import re
from time import sleep
import logging
import requests
import datetime
from pprint import pprint
from DataObjects import *

"""Vk.com API wrapper"""
class Api:

    apiVersion = 5.34  # actual as of 25.06.2015

    urlTemplate = 'https://api.vk.com/method/{}'

    authUrlTemplate = "https://oauth.vk.com/oauth/authorize" \
              "?redirect_uri=https://oauth.vk.com/blank.html" \
              "&response_type=token" \
              "&client_id={}" \
              "&scope={}" \
              "&display=wap"

    authPermissions = ["wall", "audio", "friends", "notes", "video", "docs"]

    def __init__(self, appId, id, maxAttempts=5, token=None):
        self.appId = appId
        self.id = id
        self.maxAttempts = maxAttempts
        self._set_token(token)
        logging.debug("Api client created for id {}".format(self.id))

    def _set_token(self, token=None):
        logging.debug("Getting token...")
        self.token = token if token else self._auth(self.appId)
        if not self.token:
            raise RuntimeError("Access token not found, can not proceed")


    def call_api(self, method, params):
        """
        This method does not raise errors, just returns None in case of error.
        """
        logging.debug('Calling api method {}, params={}'.format(method, params))
        for n in xrange(self.maxAttempts):
            try:
                result = self._call_api_simple(method, params)
                if result:
                    return result
                else:
                    raise ValueError("Result is empty!")
            except TooManyRequestsError as e:
                logging.debug(e)
                logging.debug("Sleeping for 1 second...")
                sleep(1)
            except CaptchaError as e:
                logging.debug(e)
                key = self._captcha(e.imgUrl)
                sid = e.sid
                params.extend([("captcha_sid", sid), ("captcha_key", key)])
            except Exception as e:
                logging.debug(e)
                logging.error("API request failed, {}/{} retries left".format(self.maxAttempts-(n+1), self.maxAttempts))
        return None  # totally failed

    def _call_api_simple(self, method, params):
        paramsDict = dict(params)
        paramsDict["access_token"] = self.token
        paramsDict["v"] = Api.apiVersion
        url = Api.urlTemplate.format(method)
        response = requests.get(url, params=paramsDict)
        assert response.status_code == 200
        assert response.encoding == "utf-8"

        data = response.json()
        if data.get("error"):
            logging.debug("Response with error: {}".format(str(data["error"])))
            if data["error"]["error_code"] == 6:  # too many requests
                raise TooManyRequestsError(data["error"])
            elif data["error"]["error_code"] == 14:  # captcha needed
                raise CaptchaError(data["error"])
            else:
                raise OtherError(data["error"])

        logging.debug("Api call succeeded")
        return data["response"]

    def _auth(self, appId):
        """Interact with user to get access_token"""

        url = Api.authUrlTemplate.format(appId, ",".join(Api.authPermissions))

        print("Please open this url:\n\n\t{}\n".format(url))
        raw_url = raw_input("Grant access to your account and copy resulting URL here: ")
        res = re.search('access_token=([0-9A-Fa-f]+)', raw_url, re.I)
        exp = re.search('expires_in=(\d+)', raw_url, re.I)

        token = res.groups()[0] if res else None
        if token is None:
            return None, None

        expiresInSeconds = int(exp.groups()[0])
        now = datetime.datetime.now()
        expirationDateTime = now + datetime.timedelta(seconds=expiresInSeconds)
        logging.info("Token will expire in {}s - at {}".format(expiresInSeconds, expirationDateTime))

        return token

    def _captcha(self, imgUrl):
        """Ask user to solve captcha"""
        logging.debug("Captcha needed..")
        print("VK thinks you're a bot - and you are ;)")
        print("They want you to solve CAPTCHA. Please open this URL, and type here a captcha solution:")
        print("\n\t{}\n".format(imgUrl))
        solution = raw_input("Solution = ").strip()
        return solution


class Wall:

    method = "wall.get"
    maxCount = 100

    @staticmethod
    def process(api, download, start, end):
        wall = Wall(api)
        count = wall.getCount()
        logging.info("Total wall posts: {}".format(count))
        maxRange = min(count, end) if end != -1 else count
        logging.info("Download range: {} - {}".format(start, maxRange))
        posts = []
        for offset in xrange(start, maxRange, Wall.maxCount):
            posts += wall.getRange(offset, Wall.maxCount)

        pprint(posts)


    def __init__(self, api):
        self.api = api

    def getCount(self):
        params = [
            ("owner_id", self.api.id),
            ("count", 1),
            ("offset", 0)
            ]
        result = self.api.call_api(Wall.method, params)
        return result["count"]

    def getRange(self, offset, count):
        params = [
            ("owner_id", self.api.id),
            ("count", count),
            ("offset", offset),
            ("extended", 1)  # returns profiles and other stuff for easier parsing
            ]
        response = self.api.call_api(Wall.method, params)
        return [WallPost(rawPost) for rawPost in response["items"]]


class Audio:
    @staticmethod
    def process(api, download, start, end):
        logging.fatal("Not implemented")

class Docs:
    @staticmethod
    def process(api, download, start, end):
        logging.fatal("Not implemented")

class Notes:
    @staticmethod
    def process(api, download, start, end):
        logging.fatal("Not implemented")

class Video:
    @staticmethod
    def process(api, download, start, end):
        logging.fatal("Not implemented")

class Messages:
    @staticmethod
    def process(api, download, start, end):
        logging.fatal("Not implemented")

class TooManyRequestsError(Exception):
    def __init__(self, errorData):
        self.errorData = errorData
        self.message = errorData["error_msg"]
    def __str__(self):
        return self.message


class CaptchaError(Exception):
    def __init__(self, errorData):
        self.errorData = errorData
        self.message = errorData["error_msg"]
        self.sid = errorData["captcha_sid"]
        self.imgUrl = errorData["captcha_img"]
    def __str__(self):
        return self.message


class OtherError(Exception):
    def __init__(self, errorData):
        self.errorData = errorData
    def __str__(self):
        return str(self.errorData)
