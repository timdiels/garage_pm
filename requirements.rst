Requirements
============

General
-------
There are no users, this is a single user app. There are people to delegate to,
but they are simply strings.

With the calendar extensions, keep them as lean as possible by delegating
whatever you can to the GaragePM API. Pick something with little overhead for
the API so we can call it a lot.

Aim to be self-documenting with tooltips and clear error messages. For odd
workflows, try to make them not odd, and otherwise do document it in some user
doc. We don't plan to write much user doc as we'll pretty much be the only
user.

Tags
----
- Tags can be defined globally and per project. They have a name/slug and a
  description. The description should be shown on a tag overview page. Per
  project tags cannot shadow/override global tags, tags are unique regardless
  of whether they're project or global tags. You can promote a project tag to
  global tag. Basically a tag optionally has a project, you can only set a
  project on it if that's the only place it has been used.

- Issue tags and time tracking tags are separate. So an issue tag autocomplete
  should only show tags used on issues, not those only used in time tracking.

  **TODO** Not sure how this affects global vs project tags, e.g. project time
  tracking tag with the same name as a global issue tag?

Issues (before known as tasks)
------------------------------
- Has name
- Has comments. The first comment is the description.
- Has tags. 
- Has a project

- [low prio] Has optional start_date, to indicate this start cannot start
  before that date (explain in tooltip or rather name your label appropriately,
  e.g. 'Cannot start before:'; maybe we should have named it min_date (and the
  other max_date) but too trivial and too late to bother now)

- [low prio] Has optional end_date, for deadlines (hint in tooltip or maybe
  label it Deadline instead in the UI), though we are limited in detecting
  exceeding the deadline as we no longer support deps and only schedule the
  todo list. We work around this by letting the scheduler always schedule any
  issues with deadlines at the end of the todo list if they're not already a
  part of it. To get a proper estimation of your deadlines, manually throw and
  order everything on the todo list.

- [low prio] Has optional time estimates, defaults to 4h for scheduling calc if
  missing. Warn if setting effort beyond 85h (you better split into subtasks at
  that point). Estimates on parent tasks estimate the effort needed to finish
  the task minus any effort on child tasks; i.e. it should estimate the various
  bits of work not worth putting in its own child task.

- Optionally/usually has a parent issue. The idea of the tree is to form a WBS
  down to the smallest of tasks.

- [lowest prio] Has optional delegate. This is a simple string. A correct term for
  the person is "the delegate", yes. Needn't be a leaf task to allow
  delegation. Though this begs the question of whether delegate should
  automatically be set on child tasks as well... probably not, better let the
  user do that manually if it indeed applies.

- [lowest prio] Can set a reminder, this is to check up on whether the delegate has done the
  work and we can close the issue. Leaving it open regardless of delegate in
  case it has more uses.

- Think of parent/child constraints

  - Cannot add child to closed task
  - Cannot close task with open child

- Can reopen a task
- Cannot delete a task

- [low prio] Record changes to name, comments and tags. We do what GitLab does, especially
  when it comes to the presentation, if the below differs from GitLab, GitLab
  wins, they have experience in this.

  - Do not store old versions of messages, only record the *last* time it was
    edited. E.g. [comment body] edited (5d ago / 2018-05-03 18:20).
  - Record which tags were added/removed and when. E.g. added tag t1, t2
    (datetime), removed tag t1, t2 (datetime).
  - Record old names and when each change happened. E.g. changed name from foo
    to bar (datetime).
  - Record who and when we delegated the work, on set/change/unset delegate
  - Record open/closed
  - Anything we've missed?

Time tracking
-------------
time_track_entry's have: begin (datetime), end (datetime), tags, optional issue, optional message

- Instead of hamster's overview, show it in the calendar.
- Allow editing it from within the calendar too.
- Additionally show stats, like hamster (have a look at hamster and pick those
  we use). Some useful ones: total of each day, total of each week, filterable
  by tag.

Logic:

- may assign to both leaf and parent tasks. E.g. assigning to parent task could
  mean work on various tidbits not worth having their own issue.

- though it may make sense to assign to multiple issues, we may not support
  this and instead require you to pick one. Maybe split up your time spent
  according to what you think it could be at the time...


Scheduling
----------
Thunderbird+Lightning is used as the view (the ical/dav may end up being stored
at our server). We add our stuff to it via extentions
(https://wiki.mozilla.org/Calendar:Creating_an_Extension). View layer and
interop:

- We will have a calendar in which to place available time slots for each
  project. The task name should match the project name and then it will be
  assigned to that project for scheduling.

- (Low prio; can work around by manually making holes in time slots above)
  Events marked as unavailable in other calendars (you can select in garagePM
  which cals to take into account, e.g. will want to ignore M's calendar) will
  be subtracted from your available time slots.

- A calendar is added with the scheduled issues from GaragePM. Doesn't matter
  whether you set these to unavailable or not. These events are read only and
  should allow you to quickly open up the corresponding issue from within the
  calendar. (e.g. by clicking a url or right clicking the event and having some
  special option which via IPC tells GaragePM to open the right issue).

- (Low prio; hold off until we come across a case where we actually needed this feature)
  "Go to schedule" from within GaragePM on an issue page, opens the calendar at
  the date where the issue is scheduled.

Risk: our events shift around a lot due to discrepancies between what was
originally scheduled and what's being done in reality (e.g. not working when
scheduled or working too long); this may cause performance issues, though there
won't be many events due to using todo lists instead of scheduling the entire
WBS.

Scheduling logic (model layer):

- What to shedule: anything on the todo list, we do not schedule the entire
  WBS. Plus, also schedule any issues with an end_date not yet on the todo
  list, scheduling them after any issues on the todo list.

- Schedule order per project is simply todo list order. GaragePM does not
  assume dependencies between tasks, that's up to the user. No, not even
  between parent/child tasks.

- Each project's schedule is fitted in the project's time slots.

- When a scheduled end_date exceeds the issue's desired end_date, show an icon in
  the systray which makes clear there is an error with garagepm, also show a
  notification message stating we are on the path to missing a deadline. If the
  notification bubble in the corner of the screen is permanent, not even
  cancelled out by the notification of another program, then there's no need for
  a systray icon. This should be checked every time the schedule changes.
  At other points no systray icon should be shown.

- Even when there's only 5 min left in a day, schedule 5 min of work in it
  anyway. We can improve on this later if needed.

Todo list
---------
- one per project
- an ordered list of issues
- adding a parent issue does not imply adding its children
- Delegated issues musn't be part of a todo list. This includes both when
  trying to add a delegated to the list and when trying to set a delegate on an
  issue in a todo list. Disable the field and explain why it's not possible in
  tooltip.
