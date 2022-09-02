# The Self-Other game and supporting code

This was a set of web applications that would ask research participants a series of questions, such as "would you rather get $3.25, or for a stranger to get $6.88," and based on their answers, use logistic regression to seek the ratio where people were equally likely to choose either answer. It did some work to make the seeking behavior less obvious.

It was written around 2009 by Nate Vack and Drew Fox. The code is old. Very likely, don't try to run it yourself. It required Python 2.7 and Django 1.2.5. Seriously, it is old and there are probably better ways to do the things we did here.

## What's all here?

Folder | Description
--- | ---
demo | A version of the game designed for demonstration, not research, shows their indifference point at the end
subject_spindler | A utility used to generate subject ids and pair subjects within sessions
others | see `offers/templates/instructions.djhtml` to see what we told participants