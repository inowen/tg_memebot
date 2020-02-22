""" This function takes a subreddit's name and the amount of images that should be downloaded
from it, and approximates a sensible amount of upvotes that a "good" post is likely to have. 

Relatively unknown subs will have their best posts at a low amount of upvotes, while well-known ones
will sometimes have a threshold around 10k.

Ways to do this: 
1) Use the amount of subscribers on the sub to calculate the amount of upvotes.
2) Go through the first few pages of the sub to find a maximum amount of upvotes, an average and 
	from that, estimate the perfect amount of upvotes.
"""


