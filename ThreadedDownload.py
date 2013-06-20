__author__ = 'chandlerprall'

import urllib2
import threading
from Queue import Queue
import sys
import os
import re
import logging

counter = 0
class ThreadedDownload(object):
    """Taken from:
    https://gist.github.com/chandlerprall/1017266
    """

    REGEX = {
    'hostname_strip': re.compile('.*\..*?/', re.I)
    }


    class MissingDirectoryException(Exception):
        pass


    class Downloader(threading.Thread):
        def __init__(self, queue, report, print_str, verbose):
            threading.Thread.__init__(self)
            self.queue = queue
            self.report = report
            self.bak_str = print_str
            self.print_str = print_str + "/ downloaded: {}"
            self.verbose = verbose

        def run(self):
            global counter
            while self.queue.empty() == False:
                url = self.queue.get()

                response = url.download()
                if response == False and url.url_tried < url.url_tries:
                    self.queue.put(url)
                elif response == False and url.url_tried == url.url_tries:
                    logging.error("\tDownload failure: " + url.url)
                    self.report['failure'].append(url)
                elif response == True:
                    logging.info("\tDownload success: " + url.url)
                    self.report['success'].append(url)
                    # progress-bar magic
                    counter += 1
                    to_print = self.print_str.format(counter)

                    if self.verbose:
                        sys.stdout.write(to_print)

                        # real magic!
                        if sys.platform.lower().startswith('win'):
                            sys.stdout.write('\r')
                        else:
                            sys.stdout.write(chr(27) + '[A')

                self.queue.task_done()
                if self.verbose:
                    tmp = self.bak_str.strip()
                    tmp = int(tmp[tmp.rindex(' '):])
                    if counter == tmp:
                        sys.stdout.write("\n\n")
                    else:
                        sys.stdout.write("\n")


    class URLTarget(object):
        def __init__(self, url, destination, url_tries):
            self.url = url
            self.destination = destination
            self.url_tries = url_tries
            self.url_tried = 0
            self.success = False
            self.error = None

        def download(self):
            self.url_tried = self.url_tried + 1

            try:
                if os.path.exists(self.destination): # This file has already been downloaded
                    self.success = True
                    return self.success

                remote_file = urllib2.urlopen(self.url)
                package = remote_file.read()
                remote_file.close()

                if os.path.exists(os.path.dirname(self.destination)) == False:
                    os.makedirs(os.path.dirname(self.destination))

                dest_file = open(self.destination, 'wb')
                dest_file.write(package)
                dest_file.close()

                self.success = True

            except Exception, e:
                self.error = e

            return self.success

        def __str__(self):
            return 'URLTarget (%(url)s, %(success)s, %(error)s)' % {'url': self.url, 'success': self.success,
                                                                    'error': self.error}


    def __init__(self, urls=[], destination='.', verbose=False, thread_count=5, url_tries=3, print_str=""):
        if os.path.exists(destination) == False:
            raise ThreadedDownload.MissingDirectoryException('Destination folder does not exist.')

        self.queue = Queue(0) # Infinite sized queue
        self.report = {'success': [], 'failure': []}
        self.threads = []

        if destination[-1] != os.path.sep:
            destination = destination + os.path.sep
        self.destination = destination
        self.thread_count = thread_count
        self.print_str = print_str
        self.verbose = verbose

        # Prepopulate queue with any values we were given
        for t in urls:
            url = t[0]
            name = t[1]
            self.queue.put(ThreadedDownload.URLTarget(url, self.fileDestination(url, name), url_tries))


    def fileDestination(self, url, desired_name=None):
        if desired_name is None:
            # no filename, use URL
            name = url
        else:
            name = desired_name
        file_destination = '%s%s' % (self.destination, os.path.basename(name))
        return file_destination


    def addTarget(self, url, url_tries=3):
        self.queue.put(ThreadedDownload.URLTarget(url, self.fileDestination(url[0], url[1]), url_tries))


    def run(self):
        global counter
        counter = 0
        #sys.stdout.write(self.print_str.format(counter))
        for i in range(self.thread_count):
            thread = ThreadedDownload.Downloader(self.queue, self.report, self.print_str, self.verbose)
            thread.start()
            self.threads.append(thread)
        if self.queue.qsize() > 0:
            self.queue.join()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print 'No source URLs given.'
        sys.exit()

    url_source_path = sys.argv[1]
    if not os.path.exists(url_source_path):
        print '`%s` not found.' % url_source_path
        sys.exit()

    # Load urls
    url_source = open(url_source_path, 'r')
    urls = [url.strip() for url in url_source.readlines()]
    url_source.close()

    # Download destination
    if len(sys.argv) >= 3:
        destination = sys.argv[2]
        if not os.path.exists(destination):
            print 'Destination `%s` does not exist.'
            sys.exit()
    else:
        destination = '.'

    # Number of threads
    if len(sys.argv) >= 4:
        threads = int(sys.argv[3])
    else:
        threads = 5

    downloader = ThreadedDownload(urls, destination, True, threads, 3)

    print 'Downloading %s files' % len(urls)
    downloader.run()
    print 'Downloaded %(success)s of %(total)s' % {'success': len(downloader.report['success']), 'total': len(urls)}

    if len(downloader.report['failure']) > 0:
        print '\nFailed urls:'
        for url in downloader.report['failure']:
            print url