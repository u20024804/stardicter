# -*- coding: utf-8 -*-
#
# Copyright © 2006 - 2017 Michal Čihař <michal@cihar.com>
#
# This file is part of Stardicter <https://cihar.com/software/slovnik/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals

import codecs
import datetime
import gzip
import hashlib
import json
from operator import attrgetter
import os
import re
import struct

from six.moves.urllib.request import urlopen
from six import BytesIO

from stardicter.word import Word


README_TEXT = r'''{title}
{line}

This is autogenerated dictionary for StarDict.

Data were downloaded from following website:
<{url}>

The original source is available under {license}.

Dictionary was generated using:
Stardicter version {version}

You can get conversion script from:
<https://cihar.com/software/slovnik/>

Install dictionary by copying dictionary files to dic/ folder in
StarDict. On Linux it is usually /usr/share/stardict/dic/, on Windows
C:\Program files\stardict\dic\.
'''

STRIPTAGS = re.compile(r"<.*?>", re.DOTALL)

CONFIGFILE = os.path.expanduser('~/.stardicter')

# type of word (used as title)
FMT_TYPE = '<span size="larger" color="darkred" weight="bold">{0}</span>\n'

AUTHOR = 'Stardicter'
URL = 'https://cihar.com/software/slovnik/'


class StardictWriter(object):
    '''
    Generic writer for stardict dictionary.
    '''
    url = None
    name = 'Generic'
    prefix = ''
    source = 'aa'
    target = 'bb'
    license = ''
    bidirectional = True
    download_url = None
    download_charset = 'utf-8'
    download_gzip = False

    def __init__(self, ascii=False, notags=False, keyprefix='',
                 source='', target='', file=None):
        self.words = {}
        self.reverse = {}
        self.description = ''
        self.ascii = ascii
        self.notags = notags
        self._data = None
        self._checksum = None
        self.keyprefix = keyprefix
        if source:
            self.source = source
        if target:
            self.target = target
        self.file = file

    @property
    def data(self):
        '''
        Returns downloaded data file.
        '''
        if self._data is None:
            self._data = self.download()
        return self._data

    @property
    def lines(self):
        '''
        Returns lines.
        '''
        return self.data.splitlines()

    @property
    def checksum(self):
        '''
        Returns data checksum.
        '''
        if self._checksum is None:
            self._checksum = self.get_checksum()
        return self._checksum

    def get_filename(self, forward=True):
        '''
        Returns filename for dictionary.
        '''
        if forward:
            name = '{0}-{1}'.format(self.source, self.target)
        else:
            name = '{0}-{1}'.format(self.target, self.source)

        suffix = ''
        if self.ascii:
            suffix += '-ascii'
        if self.notags:
            suffix += '-notags'

        return '{0}{1}{2}'.format(self.prefix, name, suffix)

    def get_name(self, forward=True):
        '''
        Returns dictionary name.
        '''
        return self.name

    def is_data_line(self, line):
        '''
        Checks whether line is used for checksum. Can be used to exclude
        timestamps from data.
        '''
        return True

    def is_header_line(self, line):
        '''
        Checks whether line is header.
        '''
        return line[0] == '#'

    def add_description(self, line):
        '''
        Adds description from line.
        '''
        self.description += line[1:] + '\n'

    def get_checksum(self):
        '''
        Calculated dictionary checksum.
        '''
        md5 = hashlib.md5()
        for line in self.lines:
            if self.is_data_line(line):
                md5.update(line.encode('utf-8'))
        return md5.hexdigest()

    def download(self):
        '''
        Downloads dictionary.
        '''
        if self.file:
            handle = self.file
            self.download_gzip = self.file.name.endswith('.gz')
        else:
            if self.download_url is None:
                return 'word\ttranslation\ttype\tnote\tauthor'
            handle = urlopen(self.download_url)
        if self.download_gzip:
            stringio = BytesIO(handle.read())
            handle.close()
            handle = gzip.GzipFile(fileobj=stringio)
        text = handle.read()
        return text.decode(self.download_charset)

    def parse_line(self, line):
        '''
        Parses single line with word.
        '''
        return [Word.from_slovnik(line)]

    def parse(self):
        '''
        Parses dictionary.
        '''
        for line in self.lines:
            # Skip blank lines
            if line.strip() == '':
                continue

            # Description from header
            if self.is_header_line(line):
                self.add_description(line)
                continue

            # Parse line
            words = self.parse_line(line)

            for word in words:

                # Skip not translated words
                if not word.word or not word.translation:
                    continue

                # Store word
                if len(word.word) < 256:
                    if word.word not in self.words:
                        self.words[word.word] = []

                    self.words[word.word].append(word)

                # Other direction
                if self.bidirectional and len(word.translation) < 256:
                    if word.translation not in self.reverse:
                        self.reverse[word.translation] = []
                    self.reverse[word.translation].append(word.reverse())

        # Sort by translation alphabetically

        for word in self.words:
            self.words[word].sort(key=attrgetter('translation'))

        for word in self.reverse:
            self.reverse[word].sort(key=attrgetter('translation'))

    def convert(self, text, convert=True):
        '''
        Converts text to match wanted format.
        '''
        if self.notags:
            text = STRIPTAGS.sub('', text)

        if not convert:
            return text

        if self.ascii:
            return text.encode('ascii', 'deaccent')

        return text.encode('utf-8')

    def formatentry(self, words):
        '''
        Formats dictionary entry.
        '''
        # sort alphabetically
        # array for different word types
        alltypes = [
            'n:',
            'v:',
            'adj:',
            'adv:',
            'prep:',
            'conj:',
            'interj:',
            'num:',
            '',
        ]
        # variables used for data
        result = ''
        typed = {}
        # array holding typed words
        for key in alltypes:
            typed[key] = []
        # process all translations
        for word in words:
            tokens = word.wtype.split()
            saved = False
            for key in alltypes:
                # check if translation is current type
                if key in tokens:
                    saved = True
                    # remove type from translation, it will be in title
                    del tokens[tokens.index(key)]
                    word.wtype = ' '.join(tokens)
                    # handle irregullar word specially (display them first)
                    if '[neprav.]' in tokens:
                        typed[key].insert(0, word)
                    else:
                        typed[key].append(word)
                    break
            if not saved:
                typed[''].append(word)

        # and finally convert entries to text
        for typ in alltypes:
            if len(typed[typ]) > 0:
                # header to display
                if typ == '':
                    result += '\n'
                else:
                    result += FMT_TYPE.format(typ)
                for word in typed[typ]:
                    result += '    '
                    result += word.format()

        return result

    def getsortedwords(self, words):
        '''
        Returns keys of hash sorted case insensitive.
        '''
        if self.ascii:
            tuples = [
                (item.encode('ascii', 'deaccent').lower(), item)
                for item in words
            ]
        else:
            tuples = [
                (item.encode('utf-8').lower(), item)
                for item in words
            ]
        tuples.sort()
        return [item[1] for item in tuples]

    def write_words(self, basefilename, name, words):
        '''
        Writes word list to dictionary files.
        '''
        # initialize variables
        offset = 0
        count = 0
        idxsize = 0

        # File names
        dictn = '{0}.dict'.format(basefilename)
        idxn = '{0}.idx'.format(basefilename)

        # Write dictionary and index
        with open(dictn, 'wb') as dictf, open(idxn, 'wb') as idxf:
            for key in self.getsortedwords(words):
                # format single entry
                entry = self.convert(self.formatentry(words[key]))

                # write dictionary text
                dictf.write(entry)

                # write index entry
                idxf.write(self.convert(key))
                idxf.write(b'\0')
                idxf.write(struct.pack(b'!I', offset))
                idxf.write(struct.pack(b'!I', len(entry)))

                # calculate offset for next index entry
                offset += len(entry)
                count += 1

            # index size is needed in ifo
            idxsize = idxf.tell()

        self._write_ifo(name, basefilename, count, idxsize)

    def _write_ifo(self, name, basefilename, count, idxsize):
        '''
        Writes info file.
        '''
        filename = '{0}.ifo'.format(basefilename)
        with codecs.open(filename, 'w', 'utf-8') as handle:
            handle.write('StarDict\'s dict ifo file\n')
            handle.write('version=2.4.2\n')
            handle.write(self.convert('bookname={0}\n'.format(name), False))
            handle.write('wordcount={0}\n'.format(count))
            handle.write('idxfilesize={0}\n'.format(idxsize))
            handle.write(self.convert('author={0}\n'.format(AUTHOR), False))
            handle.write(self.convert('website={0}\n'.format(URL), False))
            # we're using pango markup for all entries
            handle.write('sametypesequence=g\n')
            handle.write(datetime.date.today().strftime('date=%Y.%m.%d\n'))

    def write_dict(self, directory):
        '''
        Writes dictionary into directory.
        '''
        # Write readme
        with open(os.path.join(directory, 'README'), 'wb') as readme:
            readme.write(self.get_readme().encode('utf-8'))
            if self.description:
                readme.write(
                    '\nOriginal description of dictionary:\n{0}'.format(
                        self.description
                    ).encode('utf-8')
                )
        # Write forward dictioanry
        self.write_words(
            os.path.join(directory, self.get_filename(True)),
            self.get_name(True),
            self.words
        )
        # Write reverse dictionary
        if self.bidirectional:
            self.write_words(
                os.path.join(directory, self.get_filename(False)),
                self.get_name(False),
                self.reverse
            )

    def get_readme(self):
        '''
        Generates README text for dictionary.
        '''
        title = '{0} for StarDict'.format(self.name)
        return README_TEXT.format(
            title=title,
            line='-' * len(title),
            url=self.url,
            license=self.license,
            version='0.1',
        )

    def get_config_key(self):
        '''
        Key used to store MD5 in config.
        '''
        return 'md5-{0}{1}'.format(self.keyprefix, self.get_filename())

    def load_config(self):
        '''
        Loads checksum cache.
        '''
        try:
            with open(CONFIGFILE) as handle:
                return json.load(handle)
        except (ValueError, IOError):
            return {}

    def save_config(self, changes):
        '''
        Loads checksum cache.
        '''
        config = self.load_config()
        config.update(changes)
        with codecs.open(CONFIGFILE, 'wb', 'utf-8') as handle:
            json.dump(config, handle, indent=2)

    def was_changed(self):
        '''
        Detects whether dictionary has same content as on last run.
        '''
        key = self.get_config_key()
        config = self.load_config()
        if key not in config:
            return True
        return self.checksum != config[key]

    def save_checksum(self):
        '''
        Saves checksum to configuration.
        '''
        key = self.get_config_key()
        self.save_config({key: self.checksum})

    def get_source_name(self):
        """Name for source file."""
        name = os.path.basename(self.download_url)
        if name.endswith('.gz'):
            name = name[:-3]
        return name

    def write_source(self, directory):
        """Write source file."""
        with open(os.path.join(directory, self.get_source_name()), 'wb') as handle:
            handle.write(self.data.encode(self.download_charset))
