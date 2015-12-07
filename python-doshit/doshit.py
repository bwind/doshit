#!/usr/bin/python

# -*- coding: utf-8 -*-
import re
import sys
import argparse
import doshit.worker

def _print_help():
    print 'DoShit is a remote executing job / task queue.'
    print ''
    print 'usage:'
    print 'doshit [command] [command args]'
    print ''
    print 'commands:'
    print 'worker - starts a worker process the will execture the job / task'
    print ''
    print 'examples:'
    print '"doshit worker my_task.py" will start a worker that will excute the functions in my_task.py'
    print '"doshit worker -h" will print the help for starting a worker'
    print ''
    print 'To use doshit you need to:'
    print ' 1) start a redis-server'
    print ' 2) start worker via "doshit worker [task_file]"'
    print ' 3) call the function from python or NodeJS'
    print ''
    print 'check https://github.com/metocean/doshit/ for more info'



def _trim_first_arg():
    """
    removes the first argument so we can call the main()
    function of then module call won't crash.
    """
    last_arg = len(sys.argv) - 1
    for i in range(0, len(sys.argv)):
        if i < last_arg:
            sys.argv[i] = sys.argv[i + 1]
        elif i == last_arg:
            del sys.argv[last_arg]

if __name__ == '__main__':

    if (len(sys.argv) < 2
        or sys.argv[1] == '-h'
        or sys.argv[1] == '--help'):
        _print_help()
        sys.exit(0)

    elif (sys.argv[1] == 'worker'):
        _trim_first_arg()
        sys.exit(doshit.worker.main())
