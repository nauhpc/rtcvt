"""
DataGatherer - Base class for gathering data
"""

import os
import sys
import re
import subprocess
from subprocess import Popen, call


def run(cmd):
    """
    Runs a subprocess command
    :param cmd: string of the command to invoke
    :return: ??
    """
    popen = Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = popen.communicate()
    # TODO: see if this is the right way to handle errors for popen
    if out[1] is not None:
        return out[1]  # exit error?
    else:
        out = out[0].decode().strip()
        return out

class DataGathererError(ValueError):
    pass
 
 
class DataGatherer:
    """
    Base Class for interacting with scheduler
    """
    def __init__(self, scheduler, cluster_name):
        self._scheduler = scheduler
        self._scheduler_version = None
        self._cluster = cluster_name
        self._os_type = self._get_os()
        self._os_version = self._get_os(os_type=False)
        self._num_cpus = None
        self._num_nodes = None
        self._total_mem = None
        self._queue = None

    def _get_os(self, os_type=True):
        cmd = "cat /etc/issue | head -n 1"
        out = run(cmd)
        out = out.split()
        if os_type:
            return out[0]
        else:
            for e in out:
                try:
                    float(e)
                    return e
                except ValueError:
                    continue
        return ""



    def get_num_cpus(self):
        raise NotImplementedError

    def get_num_nodes(self):
        raise NotImplementedError

    def get_total_mem(self):
        raise NotImplementedError

    def get_scheduler(self):
        return self._scheduler

    def get_scheduler_version(self):
        return self._scheduler_version

    def get_cluster_name(self):
        return self._cluster

    def get_os(self):
        return self._os_type

    def get_os_version(self):
        return self._os_version

    def get_queue(self):
        raise NotImplementedError

    def get_cpu_usage(self):
        raise NotImplementedError

    def get_node_usage(self):
        raise NotImplementedError

    def get_mem_usage(self):
        raise NotImplementedError

    def get_group_share(self, group):
        raise NotImplementedError

    def get_user_share(self, user):
        raise NotImplementedError

    def get_total_jobs(self, state):
        raise NotImplementedError