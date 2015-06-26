__author__ = 'rast'

import argparse
import json
import logging
import datetime
import sys
import Api

class Config():
    def __init__(self, jsonDict):
        self.verbose = jsonDict["verbose"]
        self._configureLogging(self.verbose)

        self.saveTo = jsonDict["saveTo"]
        self.ids = jsonDict["ids"]

        self.token = jsonDict.get("token")  # None if no token

        self.appId = jsonDict["appId"]
        self.simulate = jsonDict["simulate"]

        self.targets = list(Target.getTargets(jsonDict["targets"]))

    @staticmethod
    def createConfig():
        filename = _parseArgs().config
        return Config._readFile(filename)

    @staticmethod
    def _readFile(filename):
        with open(filename) as configFile:
            jsonDict = json.load(configFile)
            return Config(jsonDict)

    @staticmethod
    def _configureLogging(isVerbose):
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)

        dateFormat = '%Y-%m-%d %H:%M:%S'
        fileFormatter = logging.Formatter('%(asctime)s  %(filename)6.6s:%(lineno)4s %(levelname)8.8s %(message)s', datefmt=dateFormat)
        fileName = 'log_{:%Y.%m.%d_%H-%M-%S}.log'.format(datetime.datetime.now())
        fileLogger = logging.FileHandler(fileName)
        fileLogger.setFormatter(fileFormatter)
        logger.addHandler(fileLogger)

        dateFormat = '%H:%M:%S'
        consoleFormatter = logging.Formatter('%(asctime)s %(levelname)8.8s %(message)s', datefmt=dateFormat)
        consoleLogger = logging.StreamHandler(sys.stdout)
        consoleLogger.setFormatter(consoleFormatter)
        consoleLogger.setLevel(logging.NOTSET if isVerbose else logging.INFO)
        logger.addHandler(consoleLogger)

        import requests
        logging.getLogger("requests").setLevel(logging.WARNING)

        logging.debug("Logging started")


class Target:

    _enumValues = ["wall", "audio", "docs", "notes", "video", "messages"]
    wall, audio, docs, notes, video, messages = _enumValues

    def __init__(self, targetType, params):
        if targetType not in Target._enumValues:
            raise ValueError("Unknown target type {}. Should be one of {}".format(targetType, Target._enumValues))

        self.type = targetType

        self.download = params["download"]
        self.start = params["start"]
        self.end = params["end"]

        logging.debug("New target: {}".format(self.__str__()))

    def process(self, api):
        logging.debug("Processing {0}".format(self.__str__()))
        if self.type == Target.wall:
            Api.Wall.process(api, self.download, self.start, self.end)
        elif self.type == Target.audio:
            Api.Audio.process(api, self.download, self.start, self.end)
        elif self.type == Target.docs:
            Api.Docs.process(api, self.download, self.start, self.end)
        elif self.type == Target.notes:
            Api.Notes.process(api, self.download, self.start, self.end)
        elif self.type == Target.video:
            Api.Video.process(api, self.download, self.start, self.end)
        elif self.type == Target.messages:
            Api.Messages.process(api, self.download, self.start, self.end)
        else:
            raise Exception("Unknown target type {}".format(self.type))

    def __str__(self):
        return "{} (dl={}, start={}, end={})".format(self.type, self.download, self.start, self.end)

    @staticmethod
    def getTargets(jsonDict):
        for t in Target._enumValues:
            params = jsonDict.get(t)
            if params is None:
                continue
            yield Target(t, params)


def _parseArgs():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--config",
                           type=str,
                           help="Configuration file",
                           dest="config",
                           required=False,
                           metavar="FILE",
                           default="config.json")
    args = argparser.parse_args()
    return args
