Project abandoned in favor of using GitLab + Hamster (+ a PM tool). Should
anyone wish to develop this, requirements.rst contains the latest idea for how
the program should behave, the current head is messy, you may want to start
from commit 2a5d44d2529 instead. In either version, it is unusable as most
features are still missing.

----

A basic cross-platform project management tool with a focus on one-man projects
with no need for resource management.

Out of scope:

- Resources. We assume a single person works on the project and no resources
  need to be assigned. Garage PM has no clue what resources are.

Installation
------------

- Install PyQt 5.x.x or later with your package manager or manually
- Use `python setup.py`
- run with `garage-pm`
