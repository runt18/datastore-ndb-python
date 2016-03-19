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

"""Benchmark for keys_only fetch() -- see also dbench,py."""

import cProfile
import os
import pstats
import sys

from google.appengine.ext import testbed

from ndb import utils
utils.DEBUG = False

from ndb import eventloop
from ndb import model
from ndb import tasklets

# Hack: replace os.environ with a plain dict.  This is to make the
# benchmark more similar to the production environment, where
# os.environ is also a plain dict.  In the environment where we run
# the benchmark, however, it is a UserDict instance, which makes the
# benchmark run slower -- but we don't want to measure this since it
# doesn't apply to production.
os.environ = dict(os.environ)


class Foo(model.Model):
  pass


def populate(n):
  xs = [Foo() for i in xrange(n)]
  ks = model.put_multi(xs)


qry = Foo.query()


def bench(n):
  ks = qry.fetch(n, keys_only=True)
  assert len(ks) == n


def profiler(func, n):
  prof = cProfile.Profile()
  prof = prof.runctx('{0!s}({1:d})'.format(func.__name__, n), globals(), locals())
  stats = pstats.Stats(prof)
  stats.strip_dirs()
  stats.sort_stats('time')  # 'time', 'cumulative' or 'calls'
  stats.print_stats(20)  # Arg: how many to print (optional)
  # Uncomment (and tweak) the following calls for more details.
  # stats.print_callees(100)
  # stats.print_callers(100)


def main():
  utils.tweak_logging()  # Interpret -v and -q flags.

  tb = testbed.Testbed()
  tb.activate()
  tb.init_datastore_v3_stub()
  tb.init_memcache_stub()

  n = 1000
  for arg in sys.argv[1:]:
    try:
      n = int(arg)
      break
    except Exception:
      pass

  populate(n)

  profiler(bench, n)


if __name__ == '__main__':
  main()
