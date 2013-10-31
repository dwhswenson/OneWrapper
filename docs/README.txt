Basic structure of the RepExWrapper stuff:

First, I recommend downloading Doxygen and using it to generate browsable
documentation on these scripts. It'll make navigating them a lot easier.

Second, there are a couple of simple demo scripts in here. That should give
you most of the information you need.


The basic idea here is to take an object-oriented programming approach. I
know that a lot of scientific programmers are a bit intimidated by OOP, so
let me try to clarify what OOP features we're using and why.

At the heart of all programming is the idea of "abstraction" -- finding a
generic way to describe your problem. ***


So what does that mean for these scripts?

Well, first off there are two main classes: RepExWrapper and RepExSwapper.
RepExWrapper is the overall wrapper script that manages the whole replica
exchange calculation. ***

Although the default classes are designed to be enough that you can use them
as-is (with lots of external scripts to do the heavy lifting), note that you
can also create subclasses of these to bring more of the work within Python,
or to create more complicated versions of these ideas. This is illustrated
in the SimpleSwapping and SegmentedRepEx subclasses.


