#!/usr/bin/env python

"""Save everything from your VK wall"""

__author__ = "Rast"

import logging

from pprint import pprint

from Config import Config
from Api import Api


def interact(localsDict=None):
    vars = globals()
    vars.update(localsDict if localsDict else locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()


def process_post(number, post_data, post_parser, json_stuff):
    """Post-processing :)"""
    data = defaultdict(lambda: "", post_data[1])
    post_parser(number, data, json_stuff)


def process_audio(number, audio_data, post_parser, json_stuff):
    """Audio-processing"""
    # data = defaultdict(lambda: "", audio_data[1])
    try:
        data = {'attachments': [{'type': 'audio',
                                 'audio': audio_data[0],
                                }],
                'id': 'audio'
        }

        post_parser(number, data, json_stuff)
    except IndexError:  # deleted :(
        logging.warning("Deleted track: {}".format(str(audio_data)))
        return


def process_doc(number, doc_data, post_parser, json_stuff):
    """Doc-processing"""
    data = {'attachments': [{'type': 'doc',
                             'doc': doc_data,
                            }],
            'id': 'doc'
    }
    post_parser(number, data, json_stuff)


def ranges(start, end, count):
    """Determine ranges"""
    if end == 0:
        end = count
    if not 0 <= start < count + 1:
        raise RuntimeError("Start argument not in valid range")
    if not start <= end <= count:
        raise RuntimeError("End argument not in valid range")
    logging.info("Working range: from {} to {}".format(start, end))
    total = end - start
    return start, end, total




def main():

    config = Config.createConfig()

    for id in config.ids:
        api = Api(config.appId, id, token=config.token)
        config.token = api.token  # for future
        for target in config.targets:
            target.process(api)

    return


    for id in config.ids:
        api.setId(id)
        for target, settings in config.targets.items():
            if not settings.download:
                logging.info("{}: do not download.".format(target))
                continue
            if target == 'wall':
                logging.info('Current target: {}'.format(target))
                # determine posts count
                r = api.wallCount()
                interact(locals())
                logging.info("Total posts: {}".format(count))
                logging.info("Wall dowload start")
                return
                args.wall_start, args.wall_end, total = ranges(args.wall_start, args.wall_end, count)
                counter = 0.0  # float for %
                post_parser = PostParser(args.directory, str(args.id), args)
                for x in xrange(args.wall_start, args.wall_end):
                    if args.verbose and counter % 10 == 0:
                        logging.info("\nDone: {:.2%} ({})".format(counter / total, int(counter)))
                    (post, json_stuff) = call_api("wall.get", [("owner_id", args.id), ("count", 1), ("offset", x)], args)
                    process_post(("wall post", x), post, post_parser, json_stuff)
                    counter += 1
                if args.verbose:
                    logging.info("\nDone: {:.2%} ({})".format(float(total) / total, int(total)))
                continue

            elif target == 'audio':
                raise NotImplementedError
            elif target == 'friends':
                raise NotImplementedError
            elif target == 'notes':
                raise NotImplementedError
            elif target == 'video':
                raise NotImplementedError
            elif target == 'docs':
                raise NotImplementedError
            else:
                continue
            logging.info("End")
            return


    '''
        # determine posts count
        (response, json_stuff) = call_api("wall.get", [("owner_id", args.id), ("count", 1), ("offset", 0)], args)
        count = response[0]
        logging.info("Total posts: {}".format(count))
        logging.info("Wall dowload start")
        args.wall_start, args.wall_end, total = ranges(args.wall_start, args.wall_end, count)
        counter = 0.0  # float for %
        post_parser = PostParser(args.directory, str(args.id), args)
        for x in xrange(args.wall_start, args.wall_end):
            if args.verbose and counter % 10 == 0:
                logging.info("\nDone: {:.2%} ({})".format(counter / total, int(counter)))
            (post, json_stuff) = call_api("wall.get", [("owner_id", args.id), ("count", 1), ("offset", x)], args)
            process_post(("wall post", x), post, post_parser, json_stuff)
            counter += 1
        if args.verbose:
            logging.info("\nDone: {:.2%} ({})".format(float(total) / total, int(total)))

    if 'audio' in args.mode:
        # determine audio count
        (response, json_stuff) = call_api("audio.getCount", [("oid", args.id)], args)
        count = response
        logging.info("Total audio tracks: {}".format(count))
        logging.info("Audio dowload start")
        args.audio_start, args.audio_end, total = ranges(args.audio_start, args.audio_end, count)
        counter = 0.0  # float for %
        # audio_dir = os.path.join(str(args.id), 'audio')
        audio_dir = str(args.id)
        post_parser = PostParser(args.directory, audio_dir, args)
        id_param = "uid" if args.id > 0 else "gid"
        args.id *= -1 if args.id < 0 else 1
        for x in xrange(args.audio_start, args.audio_end):
            if args.verbose and counter % 10 == 0:
                logging.info("\nDone: {:.2%} ({})".format(counter / total, int(counter)))
            (audio, json_stuff) = call_api("audio.get", [(id_param, args.id), ("count", 1), ("offset", x)], args)
            process_audio(("audiotrack", x), audio, post_parser, json_stuff)
            counter += 1
        if args.verbose:
            logging.info("\nDone: {:.2%} ({})".format(float(total) / total, int(total)))

    if 'video' in args.mode:
        raise NotImplementedError("Video mode is not written yet, sorry :(")
    if 'notes' in args.mode:
        raise NotImplementedError("Notes mode is not written yet, sorry :(")
    if 'docs' in args.mode:
        # get ALL docs
        (response, json_stuff) = call_api("docs.get", [("oid", args.id)], args)
        count = response[0]
        data = response[1:]
        logging.info("Total documents: {}".format(count))
        logging.info("Wall dowload start")
        args.docs_start, args.docs_end, total = ranges(args.docs_start, args.docs_end, count)
        counter = 0.0  # float for %
        docs_dir = str(args.id)
        post_parser = PostParser(args.directory, docs_dir, args)
        data = data[args.docs_start:args.docs_end]
        num = args.docs_start
        for x in data:
            if args.verbose and counter % 10 == 0:
                logging.info("\nDone: {:.2%} ({})".format(counter / total, int(counter)))
            process_doc(("document", num), x, post_parser, json_stuff)
            counter += 1
            num += 1
        if args.verbose:
            logging.info("\nDone: {:.2%} ({})".format(float(total) / total, int(total)))
    '''

if __name__ == '__main__':
    ok = False
    try:
        main()
        ok = True
    except KeyboardInterrupt:
        logging.critical("Interrupted by keystroke")
        logging.info("Why, cruel world?..\n")
        ok = True
    finally:
        if not ok:
            logging.critical("Fail")
