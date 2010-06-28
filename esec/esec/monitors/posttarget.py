'''Provides `PostTarget`, a file-like object that posts anything written
to a given URL.
'''

import traceback
from httplib import HTTPConnection, urlsplit

class PostTarget(object):
    '''Provides a file-like object that forwards all writes to a given
    URL using the ``POST`` method.
    '''
    def __init__(self, url, autoflush=False):
        '''Instantiates a new `PostTarget`.
        
        :Parameters:
          url : string
            A URL with the address to post to.
          
          autoflush : bool [default is ``False``]
            ``True`` to post every string written; ``False`` to only
            post when `flush` is called.
        '''
        self._url = url
        self._connection = HTTPConnection(urlsplit(url)[1], timeout=10)
        self._autoflush = autoflush
        
        self._body = ''
    
    def _post(self, msg):
        '''Posts `msg` to the URL given in the constructor.'''
        self._connection.request("POST", self._url, msg)
        try: self._connection.getresponse()
        except: traceback.print_exc()   #pylint: disable=W0702
        try: self._connection.close()
        except: traceback.print_exc()   #pylint: disable=W0702
    
    def write(self, text):
        '''Posts `text` to the URL given in the constructor. If
        ``autoflush`` was ``False``, `text` is accumulated and stored
        until `flush` is called.
        '''
        if self._autoflush:
            self._post(text)
        else:
            self._body += text
    
    def flush(self):
        '''Posts accumulated text to the URL given in the constructor.
        If ``autoflush`` was ``True``, this method does nothing.
        '''
        if not self._autoflush:
            self._post(self._body)
