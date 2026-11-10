# Systematic sample

## The idea

Choose every *k*th member of the population, starting from a random point.
The table is used **once only**, to find that starting point. Everything
after it is arithmetic.

## The method

1. Find the interval: $k = \frac{\text{size of the population}}{\text{size of the sample}}$.
2. The random start must be one of the first *k* members, so read the table in
   blocks wide enough for the **largest possible start**, which is *k* - not
   the width of the population labels.
3. Take the first number in the table that could be a start.
4. Add *k* each time until you have the whole sample.

## Where marks are lost

- A number can be a real member of the population and still be **rejected as a
  start** because it is bigger than the interval. With 70 members and a sample
  of 7, the interval is 10, so 68 is a member but cannot be the start.
- The interval decides the block width. With 400 bottles and a sample of 8 the
  interval is 50, so the start is read in **pairs**, even though the bottles
  are numbered 001 to 400.
- Check the last member of your sample is still inside the population.

## How it is marked

0479 2027 specimen paper 2 Q2(b)(ii) awards `M1 method, M1 interval, A1
accuracy` - the interval carries a mark of its own, so always write it down.
