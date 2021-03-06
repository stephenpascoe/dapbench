"""
Request slices in parallel.

"""

import random

from net.grinder.script import Test
from net.grinder.script.Grinder import grinder

from dapbench.jython.util import generate_subset_requests
from dapbench.jython.netcdf import Dataset

import data_urls

properties = grinder.properties.getPropertySubset('dapbench.')

variable = properties['variable']
datasets = properties['datasets']
time_len = int(properties['time_len'])
req_sample_size = int(properties['req_sample_size'])

partition_dict = {'time': time_len}
dataset_list = data_urls.load_dataset_list(datasets)

test = Test(1, "Parallel slice request")
def call_request(req):
    return req()
test.record(call_request)

class TestRunner(object):
    def __init__(self):
        self.thread = grinder.getThreadNumber()
        # Select random dataset
        #!TODO: select dataset by Thread number?
        self.dataset_url = random.choice(dataset_list)
        self.ds = Dataset(self.dataset_url)
        self.variable = self.ds.variables[variable]
        self.requests = generate_subset_requests(self.variable,
                                                 partition_dict)

        grinder.logger.output('Thread %d selecting %s' % (self.thread,
                                                          self.dataset_url))
        grinder.logger.output('Thread %d has partitions %s' % (self.thread,
                                                               partition_dict))
        grinder.logger.output('Thread %d has variable of shape %s' % (self.thread, self.variable.shape))

    def __call__(self):
        grinder.sleep(5000*self.thread, 0)
        grinder.logger.output('Thread %d starting requests' % self.thread)

        # Each thread randomly selects a sample requests
        reqs = list(self.requests)
        grinder.logger.output('Sampling %d requests from %d' % (req_sample_size, len(reqs)))
        requests = random.sample(reqs, req_sample_size)
        
        for req in requests:
            grinder.logger.output('Requesting %s' % req)
            data = call_request(req)
            grinder.logger.output('Data returned of shape %s' % data.shape)



