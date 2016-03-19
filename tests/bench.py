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

"""Benchmark for task creation and execution."""

import cProfile
import os
import pstats
import sys

from ndb import eventloop
from ndb import tasklets
from ndb import utils

# Hack: replace os.environ with a plain dict.  This is to make the
# benchmark more similar to the production environment, where
# os.environ is also a plain dict.  In the environment where we run
# the benchmark, however, it is a UserDict instance, which makes the
# benchmark run slower -- but we don't want to measure this since it
# doesn't apply to production.
os.environ = dict(os.environ)


@tasklets.tasklet
def fibonacci(n):
  """A recursive Fibonacci to exercise task switching."""
  if n <= 1:
    raise tasklets.Return(n)
  a = yield fibonacci(n - 1)
  b = yield fibonacci(n - 2)
  raise tasklets.Return(a + b)


def bench(n):
  """Top-level benchmark function."""
  futs = []
  for i in range(n):
    fut = fibonacci(i)
    futs.append(fut)
  eventloop.run()
  for fut in futs:
    fut.check_success()


def main():
  utils.tweak_logging()  # Interpret -v and -q flags.
  n = 15  # Much larger and it takes forever.
  for arg in sys.argv[1:]:
    try:
      n = int(arg)
      break
    except Exception:
      pass
  prof = cProfile.Profile()
  prof = prof.runctx('bench({0:d})'.format(n), globals(), locals())
  stats = pstats.Stats(prof)
  stats.strip_dirs()
  stats.sort_stats('time')  # 'time', 'cumulative' or 'calls'
  stats.print_stats(20)  # Arg: how many to print (optional)
  # Uncomment (and tweak) the following calls for more details.
  # stats.print_callees(100)
  # stats.print_callers(100)


if __name__ == '__main__':
  main()
