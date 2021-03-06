# -*- coding: utf-8 -*-

"""
    Lastship Add-on (C) 2018
    Credits to Exodus and Covenant; our thanks go to their creators

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import duckduckgo
from resources.lib.modules import client
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['hdkino.to']
        self.base_link = 'https://hdkino.to'
        self.search_link = '/search/%s'
        self.stream_link = '/embed.php?video_id=%s&provider=%s'
        self.year_link = self.base_link + '/index.php?a=year&q=%s&page=%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = duckduckgo.search([localtitle] + source_utils.aliases_to_array(aliases), year, self.domains[0], '<b>(.*?)\\(')
            if not url:
                url = self._getMovieLink([year, localtitle] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)

            r = cache.get(client.request, 4, query)

            links = re.findall('data-video-id="(.*?)"\sdata-provider="(.*?)"', r)

            for id, hoster in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': (id, hoster), 'direct': False, 'debridonly': False, 'checkquality': True})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            link = self.stream_link % (url[0], url[1])
            link = urlparse.urljoin(self.base_link, link)
            content = cache.get(client.request, 4, link)
            return dom_parser.parse_dom(content, 'iframe')[0].attrs['src']

        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return

    def _getMovieLink(self, titles, year):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]

            link = self.year_link % (year, "%s")

            for i in range(1, 100, 1):
                content = cache.get(client.request, 4, link % str(i))

                links = dom_parser.parse_dom(content, 'div', attrs={'class': 'search_frame'})
                if len(links) == 0: return
                links = [dom_parser.parse_dom(i, 'a') for i in links]
                links = [(i[1], i[2]) for i in links]
                links = [(i[0].attrs['href'], re.findall('>(.*?)<', i[0].content)[0], i[1].content) for i in links]
                links = sorted(links, key=lambda i: int(i[2]), reverse=True)  # with year > no year
                links = [i[0] for i in links if cleantitle.get(i[1]) in t and year == i[2]]

                if len(links) > 0:
                    return source_utils.strip_domain(links[0])
            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
