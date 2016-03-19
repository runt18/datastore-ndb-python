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

# Example from "Writing Property Subclasses".
from ndb import *

# Pay no attention to the testbed behind the curtain.
from google.appengine.ext import testbed
tb = testbed.Testbed()
tb.activate()
tb.init_datastore_v3_stub()
tb.init_memcache_stub()

from datetime import date


class FuzzyDate(object):

  def __init__(self, first, last=None):
    assert isinstance(first, date)
    assert last is None or isinstance(last, date)
    self.first = first
    self.last = last or first

  def __repr__(self):
    return 'FuzzyDate({0!r}, {1!r})'.format(self.first, self.last)


class FuzzyDateModel(Model):
  first = DateProperty()
  last = DateProperty()


class FuzzyDateProperty(StructuredProperty):

  def __init__(self, **kwds):
    super(FuzzyDateProperty, self).__init__(FuzzyDateModel, **kwds)

  def _validate(self, value):
    assert isinstance(value, FuzzyDate)

  def _to_base_type(self, value):
    return FuzzyDateModel(first=value.first, last=value.last)

  def _from_base_type(self, value):
    return FuzzyDate(value.first, value.last)

# Class to record historic people and events in their life.


class HistoricPerson(Model):
  name = StringProperty()
  birth = FuzzyDateProperty()
  death = FuzzyDateProperty()
  # Parallel lists:
  event_dates = FuzzyDateProperty(repeated=True)
  event_names = StringProperty(repeated=True)

# Record Christopher Columbus.
columbus = HistoricPerson(
  name='Christopher Columbus',
  birth=FuzzyDate(date(1451, 8, 22), date(1451, 10, 31)),
  death=FuzzyDate(date(1506, 5, 20)),
  event_dates=[FuzzyDate(date(1492, 1, 1), date(1492, 12, 31))],
  event_names=['Discovery of America'])
columbus.put()

# Query for historic people born no later than 1451.
q = HistoricPerson.query(HistoricPerson.birth.last <= date(1451, 12, 31))
print q.fetch()
