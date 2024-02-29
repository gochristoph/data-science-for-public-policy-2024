"""Test script for matrix math operations."""

import logging
# automatically write messages to logfile instead of stdout
logging.basicConfig(format='%(asctime)s  %(message)s', 
                    datefmt='%y-%m-%d %H:%M:%S', 
                    level=logging.INFO)
import numpy as np

logging.info('generating random matrix with 1e7 128 dim row vectors')
a = np.random.rand(int(1e7), 128)

logging.info('computing L2 norm for each row')
a_norm = np.linalg.norm(a, axis=1)

logging.info('starting calculation of 1e7 cosine similarity for 100 random rows each')
for i in range(100):
    # pick random row index
    rand_row = np.random.randint(0, a.shape[0])
    # extract a random row
    b = a[rand_row, :]
    # compute cosine similarity
    c = np.matmul(a, b)
    sim = c / a_norm / np.linalg.norm(b)
logging.info('finished')