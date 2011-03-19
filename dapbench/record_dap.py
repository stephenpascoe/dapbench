#!/usr/bin/env python
"""
Execute a programme that makes NetCDF-API OPeNDAP calls capturing
request events and timings.

"""

import tempfile
import os, sys
from subprocess import Popen, PIPE
import re
import urllib

from dapbench.dap_request import DapRequest
from dapbench.dap_stats import DapStats

TMP_PREFIX='record_dap-'
DODSRC = '.dodsrc'
LOGFILE = 'record_dap.log'

class Wrapper(object):
    def __init__(self, tmpdir=None):
        if tmpdir is None:
            tmpdir = tempfile.mkdtemp(prefix=TMP_PREFIX)
        self.tmpdir = tmpdir
        self.logfile = os.path.join(self.tmpdir, LOGFILE)


    def check_dodsrc(self):
        try:
            rcpath = os.path.join(os.environ['HOME'], DODSRC)
            assert os.path.exists(rcpath)
            rcdata = open(rcpath).read()
            mo = re.search(r'^\s*CURL.VERBOSE\s*=\s*1', rcdata, re.M)
            assert mo
        except AssertionError:
            raise Exception("~/.dodsrc doesn't have CURL.VERBOSE defined")

    def call(self, command):
        self.check_dodsrc()
        
        cmd = 'strace -ttt -f -e trace=network %s' % command
        pipe = Popen(cmd, shell=True, stderr=PIPE).stderr

        return DapStats(self.iter_requests(pipe))

    def iter_requests(self, pipe):
        timestamp = None
        host = 'unknown'
        for line in pipe:
            mo = re.match('\* Connected to ([^\s]+)', line)
            if mo:
                host = mo.group(1)
            elif re.match('> GET ', line):
                #!TODO: handle other stderr output from wrapped tool
                req = urllib.unquote(line.strip()[2:])
                request = DapRequest.from_get(host, req)
                assert timestamp is not None
                yield (timestamp, request)
                timestamp = None
            else:                
                mo = re.match('(\d+\.\d+)\s+(send|recv)', line)
                if mo:
                    timestamp, syscall = mo.groups()
                    timestamp = float(timestamp)

        # Mark terminal event
        yield (timestamp, None)


def make_parser():
    import optparse
    
    usage = "%prog [options] [--] command"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-s', '--stats', action="store", 
                      help="Store stats in the pickle file STATS")

    return parser

def main(argv=sys.argv):
    import pickle

    parser = make_parser()
    
    opts, args = parser.parse_args()
    
    if not args:
        parser.error("No command specified")
    

    w = Wrapper('.', storage)
    command = ' '.join(args)
    stats = w.call(command)
    stats.print_summary()

    if opts.stats:
        statfile = open(opt.stats, 'w')
        pickle.dump(stats, statfile)
        statfile.close()

if __name__ == '__main__':
    main()

    #test_dataset = 'http://esg-dev1.badc.rl.ac.uk:8081/ta_20101129/ta_6hrPlev_HadGEM2-ES_piControl_r1i1p1_197812010600-197901010000.nc'
    #stats = w.call('cdo runmean,10 http://esg-dev1.badc.rl.ac.uk:8080/opendap/ta_20101129/ta_6hrPlev_HadGEM2-ES_piControl_r1i1p1_197812010600-197901010000.nc out.nc')
