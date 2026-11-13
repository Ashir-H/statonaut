# The median

## What it means

The median is the value in the middle, once the data has been put in ascending
order, which means smallest first. Half the values lie at or below it and half lie at or above it.

Because it depends only on position, one very large or very small value cannot
drag the median about. That is its defining property and the reason it is worth
having at all alongside the mean.

## How it is computed

**From a list**, put the values in ascending order first — this is not optional
and it is worth a mark on its own. Then count to the $\frac{n+1}{2}$ th value,
where $n$ is how many values there are.

When $n$ is odd this lands on a single value. When $n$ is even it lands halfway
between two values, and the median is the mean of those two: for eight values it
is the value halfway between the 4th and the 5th.

**From a frequency table**, the values are already in ascending order down the $x$
column, but the middle row is not the median. Build a running total of the
frequencies instead. There are $n = \Sigma f$ values altogether, so the median is
still the $\frac{n+1}{2}$ th of them; count down the running total until it first
reaches that position, and give the $x$ value on that row.

## When it is used

Use the median when the data contains a value far away from the rest, because it
describes the typical value honestly where the mean does not.

Six salaries of 18, 19, 20, 21, 22 and 120 thousand have a mean of 36.7
thousand, which is higher than five of the six people actually earn. The median
is 20.5 thousand, which is a fair description of the group. Remove the 120 and
both measures agree at 20 — the single extreme value is doing all the damage.

Its weakness is the mirror image of its strength: because it only looks at the
middle, it ignores how large or small the values at the ends are.

## How it is marked

Ordering the data earns a mark of its own in every small-list median question.
Mark schemes award it for an attempt to order, so an ordered list with a slip in
it still earns the mark — but an unordered list earns nothing, however good the
final answer looks.

For a table, the mark schemes ask for the position to be identified, in words
like "identify the 20th item", and then for the value. The position is
therefore written down before it is sought in the running total.

Giving the position instead of the value is the other common loss. With nine
values the median is the fifth value in the ordered list, not 5.
