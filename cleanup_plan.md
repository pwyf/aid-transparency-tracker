
IATI Data Quality plan
======================

Objective: 

* get the code into a state where it can be maintained by people other than
  the original developers, roughtly by October
* do so by Fabian tactics, gradually replacing one bit at a time, keeping
  the system running during PWYF's launch process

High level goals
----------------

* establish an agreed set of coding standards
* clean up each python and template file, one by one
* get rid of runtime
* normalise schema
* split ui from db code
* remove logicful templating
* make organisation conditions incapable of causing missing data exceptions
* create test identifiers
* sort out queue handling, such that queues can run in parallel / background
* have summary and indicatorsummary objects
* fix tests for summaries
* split test runner into own repo
  * allow write access to result/aggregatedresult
  * don't allow UI write access to these tables
* fix how foxpath interfaces


Schema
------

The schema is partly normalised; the main problem is that we now want to get
rid of the "runtime" concept, and tidy up a few loose ends:

* result table: need to reify hierarchy and activity identifier
  * row should be uniquely identified by (activity_id, test_id, hierarchy)
* activity table:
  * row should be uniquely identified by (package_id, organisation_id)

We'll need to get there gradually, and ultimately have one result table per
test level

We should consider abandoning the practice of tolerating the creation of
the DB by SQLAlchemy, and maintain it separately in a file; this will allow
us to use VIEWs and other standard features.


Tickets
-------

#417

#411

#379

#372

#366

#355

#334

#329

#301

#203


Code Quality
------------

We should start here: make a hit list of things to clean up. We can detail
the steps for the long campaigns (e.g., schema normalisation) as we work
through this.

The list provided in the tracker report at the end of the 2013 engagement
is largely still relevant:

* “except KeyError” is basically a bug
* review error handling in general, particularly 
  * the suppression of errors (“except Foo: pass”)
  * overly broad (“try: a[x][y][0] = b[x][y][a[x]]; etc; except KeyError: …”)
  * getOrCreate() style should be replaced with “try: x = getFoo(); except foo.NonExistent: x = createFoo()”
* Javascript should be out of the templates; they have enough languages in them already (HTML, Jinja, English, Python)
* run stuff through pylint
* remove any and all repetitiveness (particularly those long lists of config data in dictionaries; use tuples to avoid implying that the dictionary keys mean something whcih might change from item to item)
* the idea of making collections of indicators (e.g., twentytwelve data) and then hacking extra keys into them because we know that this key is likely to be accessed by a survey template is wrong in principle and very risky in practice (throws an exception (Error 500) if we screw it up)
* should establish and adhere to a house style, e.g., max line width of 79 columns, max levels of indentation 4, max function length 40 lines
* remove the “magic numbers”, i.e., unexplained constant numbers passed around without explanation in the source code
