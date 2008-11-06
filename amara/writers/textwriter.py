########################################################################
# amara/writers/textwriter.py
"""
Plain text writer for XSLT processor output
"""

import codecs

from amara.writers import streamwriter, _xmlstream


class textwriter(streamwriter):

    _encode = None

    def start_document(self):
        params = self.output_parameters
        params.setdefault('media_type', 'text/plain')
        # the default is actually system-dependent; we'll use UTF-8
        encoding = params.setdefault('encoding', 'UTF-8')
        self._encode = codecs.getencoder(encoding)
        return

    def text(self, data, disable_escaping=False):
        bytes, nbytes = self._encode(data)
        self.stream.write(bytes)
        return
