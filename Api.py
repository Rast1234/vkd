__author__ = 'rast'

import json
import urllib2
from urllib import urlencode
import re
from time import sleep
import logging

def auth(args):
    """Interact with user to get access_token"""

    url = "https://oauth.vk.com/oauth/authorize?" + \
          "redirect_uri=https://oauth.vk.com/blank.html&response_type=token&" + \
          "client_id=%s&scope=%s&display=wap" % (args.app_id, ",".join(args.access_rights))

    print("Please open this url:\n\n\t{}\n".format(url))
    raw_url = raw_input("Grant access to your acc and copy resulting URL here: ")
    res = re.search('access_token=([0-9A-Fa-f]+)', raw_url, re.I)
    if res is not None:
        return res.groups()[0]
    else:
        return None

def captcha(data):
    """Ask user to solve captcha"""
    logging.debug("Captcha needed..")
    print("VK thinks you're a bot - and you are ;)")
    print("They want you to solve CAPTCHA. Please open this URL, and type here a captcha solution:")
    print("\n\t{}\n".format(data[u'error'][u'captcha_img']))
    solution = raw_input("Solution = ").strip()
    return data[u'error'][u'captcha_sid'], solution


def call_api(method, params, args):
    while True:
        if isinstance(params, list):
            params_list = [kv for kv in params]
        elif isinstance(params, dict):
            params_list = params.items()
        else:
            params_list = [params]
        params_list.append(("access_token", args.token))
        url = "https://api.vk.com/method/%s?%s" % (method, urlencode(params_list))

        json_stuff = urllib2.urlopen(url).read()
        result = json.loads(json_stuff)
        if u'error' in result.keys():
            if result[u'error'][u'error_code'] == 6:  # too many requests
                logging.debug("Too many requests per second, sleeping..")
                sleep(1)
                continue
            elif result[u'error'][u'error_code'] == 14:  # captcha needed :\
                sid, key = captcha(result)
                params.extend([(u"captcha_sid", sid), (u"captcha_key", key)])
                continue
            else:
                msg = "API call resulted in error ({}): {}".format(result[u'error'][u'error_code'],
                                                                   result[u'error'][u'error_msg'])
                logging.error(msg)
                raise RuntimeError(msg)
        else:
            logging.debug("API call succeeded: {}".format(url))
            break

    if not u'response' in result.keys():
        msg = "API call result has no response"
        logging.error(msg)
        raise RuntimeError(msg)
    else:
        #logging.debug("API call answer: {}".format(str(result[u'response'])))
        return result[u'response'], json_stuff
