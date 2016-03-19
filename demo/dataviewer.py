#
# Copyright 2008 The ndb Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""A GQL-based viewer for the Google App Engine Datastore."""

import cgi
import logging
import os
import re
import sys
import time
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import ndb


FORM = """\
<html>
  <head>
    <title>Data Viewer - %(APPLICATION_ID)s - %(CURRENT_VERSION_ID)s</title>
  </head>
  <body>
    <form method=get action=/dataviewer>
      <input type=text size=100 name=query value="%(query)s">
      <input type=submit>
    </form>
    <p style="font-weight:bold">%(error)s</p>
    %(next)s
    %(data)s
  </body>
</html>
"""


class DataViewer(webapp.RequestHandler):

  @ndb.toplevel
  def get(self):
    conn = ndb.make_connection(default_model=ndb.Expando)
    ndb.set_context(ndb.make_context(conn=conn))
    params = dict(os.environ)
    params['error'] = ''
    params['data'] = ''
    query_string = self.request.get('query')
    page_size = int(self.request.get('page') or 10)
    start_cursor = self.request.get('cursor')
    params['query'] = query_string or 'SELECT *'
    params['next'] = ''
    if query_string:
      prefix = 'parsing'
      try:
        query = ndb.gql(query_string)
        prefix = 'binding'
        query.bind()
        prefix = 'execution'
        cursor = None
        if start_cursor:
          try:
            cursor = ndb.Cursor.from_websafe_string(start_cursor)
          except Exception:
            pass
        results, cursor, more = query.fetch_page(page_size,
                                                 start_cursor=cursor)
      except Exception, err:
        params['error'] = '{0!s} error: {1!s}.{2!s}: {3!s}'.format(prefix,
                                                   err.__class__.__module__,
                                                   err.__class__.__name__,
                                                   err)
      else:
        if not results:
          params['error'] = 'No query results'
        else:
          columns = set()
          rows = []
          for result in results:
            if isinstance(result, ndb.Key):
              rows.append({'__key__': repr(result)})
            else:
              row = {'__key__': repr(result._key)}
              for name, prop in sorted(result._properties.iteritems()):
                columns.add(name)
                values = prop.__get__(result)
                row[name] = repr(values)
              rows.append(row)
          data = []
          data.append('<table border=1>')
          data.append('<thead>')
          data.append('<tr>')
          columns = ['__key__'] + sorted(columns)
          for col in columns:
            data.append('  <th>{0!s}</th>'.format(cgi.escape(col)))
          data.append('</tr>')
          data.append('</thead>')
          data.append('<tbody>')
          for row in rows:
            data.append('<tr>')
            for col in columns:
              if col not in row:
                data.append('  <td></td>')
              else:
                data.append('  <td>{0!s}</td>'.format(cgi.escape(row[col])))
            data.append('</tr>')
          data.append('</tbody>')
          data.append('</table>')
          params['data'] = '\n    '.join(data)
          if more:
            next = ('<a href=/dataviewer?{0!s}>Next</a>'.format(
                    urllib.urlencode([('query', query_string),
                                      ('cursor', cursor.to_websafe_string()),
                                      ('page', page_size),
                                      ])))
            params['next'] = next
    self.response.out.write(FORM % params)


urls = [
  ('/dataviewer', DataViewer),
]

app = webapp.WSGIApplication(urls)


def main():
  util.run_wsgi_app(app)


if __name__ == '__main__':
  main()
