"""
ingestor.py - Data ingestor that reads Python dictionaries and saves information in Django db
"""
import re
import datetime
import time
import copy
from collections import Counter

from .SlurmDataGatherer import (parse_gres, run_sacct)

def pad(num):
    return str("%02d" % int(num))


class Ingestor():
    """
    Ingestor class - takes in python dictionaries that represent Slurm data and creates/saves django db objects.
    This class is designed to be used with Celery, with each of the public methods being called on an
    interval from Django tasks.
    """
    from django.contrib.auth.models import User
    from django.core.exceptions import ObjectDoesNotExist
    from main.models import (
        Cluster,
        Gres,
        Scheduler,
        Job,
        Group,
        CVTUser,
        UserGroupLink,
        GresClusterLink,
        GresGroupLink,
        GresCVTUserLink,
        GresUserGroupLinkLink,
    )

    SLURM_WEIRD_TIME_STRINGS = [
        "UNLIMITED",
        "Unknown",
        "N/A",
        "NOT_SET",
    ]

    def __init__(self):
        self.queue = None
        self.queue_dict = None

    def date_to_timestamp(self, time_string):
        """ converts a Slurm date string into python date object """

        if time_string.strip() in self.SLURM_WEIRD_TIME_STRINGS:
            return -1

        time_date = time.strptime("00", "%S")
        if "T" in time_string:
            time_list = re.split('[-T:]+', time_string)
            # feed time_list info into datetime object as integers and get the time in seconds
            # Example: time.strptime("2015 01 27 08 13 05", "%Y %m %d %H %M %S")
            try:
                time_date = time.strptime(pad(time_list[0]) + " " +
                                          pad(time_list[1]) + " " +
                                          pad(time_list[2]) + " " +
                                          pad(time_list[3]) + " " +
                                          pad(time_list[4]) + " " +
                                          pad(time_list[5]), "%Y %m %d %H %M %S")
            except IndexError as e:
                print("Error with time_string: %s" % time_string)
                print(e)
        else:
            raise ValueError("Error with time_string: %s. Incorrect format" % time_string)
        # convert the strptime object into seconds (since epoch, I think)
        return time.mktime(time_date)

    def time_to_seconds(self, time_string):
        """ Converts Slurm style time ddd-hh:mm:ss into seconds

        :param time_string: String representation of time in ddd-hh:mm:ss format

        :returns: Positive integer representing total seconds represented by the string.
        Returns -1 if "UNLIMITED" (which is valid for Slurm) and -2 on invalid input
        """

        if time_string.strip() in self.SLURM_WEIRD_TIME_STRINGS:
            return -1

        secs = 0
        try:
            days = 0
            if "-" in time_string:
                tmp = time_string.split('-')
                if len(tmp) > 2:
                    print("Error: time string '%s' is not convertible to seconds" % time_string)
                    return -2
                days = int(tmp[0])
                time_string = tmp[1]
            time_list = time_string.split(':')
            secs = days * 86400
            if len(time_list) == 3:
                secs += int(time_list[0]) * 3600
                secs += int(time_list[1]) * 60
                secs += int(time_list[2])
            elif len(time_list) == 2:
                secs += int(time_list[0]) * 60
                secs += int(time_list[1])
            elif len(time_list) == 1:
                secs += int(time_list[0])
            else:
                raise Exception("Error: time string '%s' is not convertible to seconds" % time_string)
        except IndexError as e:
            print("Error with parsing time_string: %s" % time_string)
            print(e)
            return -2
        except Exception as e:
            print(e)
            return -2

        return secs


    def update_jobs(self, cluster):
        if self.queue is None:
            raise Exception("can't update jobs due to self.queue not being initialized")
        else:
            db_jobs = Counter(self.Job.objects.filter(cluster=cluster))  # TODO: change this to filter by active/logged-in user
            curr_jobs = self.queue.copy()   # copy the variable so in case it's currently being written to by another method, we don't hose anything
            stale_jobs = db_jobs - curr_jobs # jobs that aren't in queue anymore - need to figure out their state info
            for job in stale_jobs:
                # get sacct info and save into new Job object
                job_info = run_sacct(job.sched_jobid)
                if len(job_info) == 0:
                    continue
                elif len(job_info) > 1:
                    raise Exception("update_jobs: got back more than one job")
                else:
                    job_info = job_info[0]  # run_sacct returns a list of dicts, so we need to get the first element
                    if len(job_info) == 0:
                        continue
                try:
                    if job.exec_start_time is None:
                        job.exec_start_time = self.date_to_timestamp(job_info['start'])
                        if not isinstance(job.exec_start_time, float):
                            print("****Error****: %s" % str(job.exec_start_time))
                            
                    if job.exec_end_time is None:
                        job.exec_end_time = self.date_to_timestamp(job_info['end'])
                    
                    if not isinstance(job.exec_start_time, float):
                        print("****Error****: %s" % str(job.exec_start_time))
                    
                    job.elapsed_time = job_info['elapsed']
                    job.state = job_info['state']
                    job.mem_usage = job_info['maxrss']  # TODO: This field is problematic because it doesn't show up in the main job, only the jobsteps
                    job.time_left = self.time_to_seconds(job_info['time_left'])
                    job.save()
                except KeyError as e:
                    print(e)

    def ingest_queue(self, cluster, queue):
        if self.queue is None:
            self.queue = Counter()
        self.queue_dict = queue

        for item in queue:
            # get group
            try:
                jGroup = self.Group.objects.get(name=item["account"], cluster=cluster)
            except self.ObjectDoesNotExist:
                jGroup = self.Group.objects.create(name=item["account"], cluster=cluster)

            # get user
            try:
                user = self.User.objects.get(username=item["user"])
                jUser = self.CVTUser.objects.get(user=user)
            except self.ObjectDoesNotExist:
                user = self.User.objects.create(username=item["user"])
                jUser = self.CVTUser.objects.create(user=user)

            # get job
            try:
                j = self.Job.objects.get(user=jUser, sched_jobid=item["job_id"])
            except self.ObjectDoesNotExist:
                j = self.Job()

            j.cluster = cluster
            j.command = item["exec_command"]
            j.elapsed_time = self.time_to_seconds(item["elapsed_time"])
            j.exec_end_time = None
            j.exec_start_time = self.date_to_timestamp(item["start_time"])
            j.exp_start_time = None
            j.group = jGroup
            j.licenses = item["licenses"]
            j.mem_usage = None
            j.name = item["job_name"]
            j.notes = item["comment"]
            j.partition = item["partition"]
            #j.pending_time = None #start_time - submit_time (?)
            j.reason_pending = item["reason"]
            j.qos = item["qos"]
            j.req_cores = item["cpus"]
            j.req_mem = item["memory"]
            j.req_nodes = item["nodes"]
            j.sched_jobid = item["job_id"]
            j.state = item["job_state"]
            j.submitted_time = self.date_to_timestamp(item["submit_time"])
            j.time_limit = float(self.time_to_seconds(item["time_limit"]))
            j.user = jUser
            j.work_dir = item["work_dir"]
            j.time_left = self.time_to_seconds(item['time_left'])
            j.save()
            self.queue[j] += 1

    def ingest_usage(self, cluster, usage):
        if not isinstance(cluster, self.Cluster):
            raise TypeError("expected 'Cluster' object but got %s" % str(type(cluster)))
        
        cluster.mem_usage = usage['memory']
        cluster.core_usage = usage['cpu']
        cluster.node_usage = usage['node']
        cluster.jobs_total = usage['jobs_total']
        cluster.jobs_pending = usage['jobs_pending']
        cluster.jobs_running = usage['jobs_running']
        cluster.save()

        for k, v in usage['gres'].items():
            try:
                gcl = self.GresClusterLink.objects.get(gres__type=k, cluster=cluster)
            except self.ObjectDoesNotExist:
                g, created = self.Gres.objects.get_or_create(type=k, total=v["total"])
                gcl = self.GresClusterLink(gres=g, cluster=cluster)
            gcl.usage = v["usage"]
            gcl.save()

    def ingest_tres_totals(self, cluster, tres):
        """
        The purpose of this method is to update the total_cpu and total_memory fields of the Group model. These represent
        the total number of cpu minutes and memory available at any given time for the whole group. This info is found
        through the SlurmDataGatherer, which calls the "sacctmgr show assoc" command and pulls the GrpTRESRunMins info
        for each group/account

        :param cluster: Cluster object
        :param tres: dict of slurm accounts as the keys and dicts of the cpumins and memory as the values
            Example:
                {
                    'account1': {'mem': '9700000000M', 'cpu': '700000'},
                    'account2': {'mem': '9700000000M', 'cpu': '700000'}
                }
        """
        if not isinstance(cluster, self.Cluster):
            raise TypeError("expected 'Cluster' object but got %s" % str(type(cluster)))

        for account, tres_info in tres.items():
            try:
                group, created = self.Group.objects.get_or_create(name=account, cluster=cluster)
                group.total_cpu = tres_info['cpu']
                group.total_memory = tres_info['mem']
                group.save()
            except Exception as e:
                print(e)

    def ingest_groupshare(self, cluster, groupshare):
        for group, stat in groupshare.items():
            try:
                g = self.Group.objects.get(name=group, cluster=cluster)
            except self.ObjectDoesNotExist:
                g = self.Group.objects.create(name=group, cluster=cluster)

            tres = stat["tresrunmins"]
            g.memory = tres["mem"]
            g.cpu = tres["cpu"]
            g.node = tres["node"]
            g.energy = tres["energy"]
            g.fairshare = stat["fairshare"]
            g.save()

    def ingest_usershare(self, cluster, usershare):
        for uid, user_info in usershare.items():
            for info in user_info:
                group = info["account"]
                g, created = self.Group.objects.get_or_create(name=group, cluster=cluster)
                try:
                    u = self.CVTUser.objects.get(user__username=uid)
                except self.ObjectDoesNotExist:
                    user = self.User.objects.create(username=uid)
                    user.save()
                    u = self.CVTUser.objects.create(user=user)
                try:
                    ugl = self.UserGroupLink.objects.get(user=u, group=g)
                except self.ObjectDoesNotExist:
                    ugl = self.UserGroupLink(user=u, group=g)
                tres = info["tresrunmins"]
                ugl.memory = tres["mem"]
                ugl.node = tres["node"]
                ugl.energy = tres["energy"]
                ugl.cpu = tres["cpu"]
                ugl.fairshare = info["fairshare"]
                ugl.save()

    def _ingest_user_gres(self, cluster, user_gres_input, gres_totals):
        
        # In the next 2 for loops, I'm just trying to change the values of the user_gres[user] fields to a 
        # different format. They start out as lists of strings like 'gpu:2', but I need them to be 
        # dictionaries of valid parsed info, like {'gpu': 2}. so for now I'm just doing 2 loops and basically 
        # just swapping the values out
        user_gres = copy.deepcopy(user_gres_input)
        tmp = {}
        for username, gres in user_gres.items():
            tmp[username] = parse_gres(gres)
        for username, gres in tmp.items():  # put the parsed gres data back into the original dict
            user_gres[username] = gres
        for gres_type, total_dict in gres_totals.items():
            for username in user_gres.keys():
                try:
                    # get usage information
                    if gres_type in user_gres[username].keys():
                        used = user_gres[username][gres_type]
                    else:
                        # add gres type to dict with usage of 0 if it wasn't found in the queue
                        user_gres[username][gres_type] = float(0)
                        used = float(0)
                    total = int(total_dict['total'])
                    user_gres[username][gres_type] = round(float(used) / float(total), 4)

                    # create database objects
                    user = self.CVTUser.objects.get(user__username=username) # TODO: should this be get_or_create?
                    gres, created = self.Gres.objects.get_or_create(type=gres_type, total=total)
                    gcvtul, created = self.GresCVTUserLink.objects.get_or_create(user=user, gres=gres)
                    gcvtul.usage = round(float(used) / float(total), 4)
                    gcvtul.save()
                except Exception as e:
                    print("Error: ", end="")
                    print(e)
        # return something for testing purposes
        return user_gres

    def _ingest_group_gres(self, cluster, group_gres_input, gres_totals):
        group_gres = copy.deepcopy(group_gres_input)
        tmp = {}
        for group, gres in group_gres.items():
            tmp[group] = parse_gres(gres)
        for group, gres in tmp.items():
            group_gres[group] = gres
        for gres_type, total_dict in gres_totals.items():
            for groupname in group_gres.keys():
                try:
                    # get usage information
                    if gres_type in group_gres[groupname].keys():
                        used = group_gres[groupname][gres_type]
                    else:
                        # add gres type with usage of 0 if not found in the queue
                        group_gres[groupname][gres_type] = float(0)
                        used = float(0)
                    total = int(total_dict['total'])
                    group_gres[groupname][gres_type] = round(float(used) / float(total), 4)
                    
                    # create database objects
                    group, created = self.Group.objects.get_or_create(name=groupname, cluster=cluster)
                    gres, created = self.Gres.objects.get_or_create(type=gres_type, total=total)
                    ggl, created = self.GresGroupLink.objects.get_or_create(group=group, gres=gres)
                    ggl.usage = round(float(used) / float(total), 4)
                    ggl.save()
                except Exception as e:
                    print("Error: _ingest_group_gres: ", end="")
                    print(e)

        return group_gres

    def _ingest_usergroup_gres(self, cluster, usergroup_gres_input, gres_totals):
        usergroup_gres = copy.deepcopy(usergroup_gres_input)
        for user, groups in usergroup_gres.items():
            for group in groups:
                group['gres'] = parse_gres(group['gres'])
        for gres_type, total_dict in gres_totals.items():
            for username, group_gres_info in usergroup_gres.items():
                for info in group_gres_info:
                    try:
                        if gres_type in info['gres'].keys():
                            used = info['gres'][gres_type]
                        else:
                            info['gres'][gres_type] = float(0)
                            used = float(0)
                        total = int(total_dict['total'])
                        info['gres'][gres_type] = round(float(used) / float(total), 4)

                        # create database objects
                        user, created = self.CVTUser.objects.get_or_create(user__username=username)
                        group, created = self.Group.objects.get_or_create(name=info['group'], cluster=cluster)
                        ugl, created = self.UserGroupLink.objects.get_or_create(user=user, group=group)
                        gres, created = self.Gres.objects.get_or_create(type=gres_type, total=total)
                        gugll, created = self.GresUserGroupLinkLink.objects.get_or_create(ugl=ugl, gres=gres)
                        gugll.usage = round(float(used) / float(total), 4)
                        gugll.save()
                    except Exception as e:
                        print("Error: ", end="")
                        print(e)
        
        return usergroup_gres

    def ingest_gres(self, cluster, gres_totals):
        """
        This method computes and stores the current gres usage information per user and per 
        group/account. This is determined by taking in a dictionary of the different gres
        types and their respective total number on the cluster (this is in the "gres_totals"
        param) and using the SlurmDataGatherer parse_gres function to build a list of usage
        information. This information is then stored in the database.

        :param cluster: Cluster object
        :param gres_totals: dict of gres types and their totals in the format:
            {
                "gpu": {
                           "total": 4,
                           "usage": 0.2
                },
                "mic": {
                           "total": 2,
                           "usage": 0.0
                       }
            }

        where "gpu" and "mic" are only examples of gres types. They can be anything that is defined in gres.conf
        on the compute nodes (see Slurm help for more info).

        This method builds and uses 3 different dictionary objects in order to ingest gres usage.
        The first is the "user_gres" dict, which holds the overall gres usage by each user. 
        It is formatted like this:
            user_gres = {
                "user1": {
                    "gpu": 0.7,
                    "mic": 0.1
                },
                "user2": {
                    "gpu": 0.3,
                    "mic": 0.0
                }
            }

        The next is group_gres, which holds the overall gres usage of each group. It looks like this:
            group_gres = {
                "group1": {
                    "gpu": 0.9,
                    "mic": 0.1
                },
                "group2": {
                    "gpu": 0.1,
                    "mic": 0.9
                }
            }
        
        **NOTE**: The above 2 dictionary examples are after the call to parse_gres has been made. Before this
        call, the dictionaries with "gpu" and "mic" would be lists that look something like ["gpu:tesla:3", "mic:mic:2"].
        After they are passed into parse_gres, they get transformed into usage dictionaries.

        The last is usergroup_gres, which holds the gres usage of a particular user/group combination.
        So if a user belongs to multiple groups, their gres usage for each group will be different
        depending on what gres they are using in each group. The following is an example of the
        dictionary and how it is formatted (before the call to parse_gres has been made):
            usergroup_gres = {
                "user1": [
                    {
                        "group": "group1",
                        "gres": ["gpu:tesla:4", "mic:mic:0"]
                    },
                    {
                        "group": "group2",
                        "gres": ["gpu:tesla:1", "mic:mic:2"]
                    }
                ],
                "user2": [
                    ...
                ]
            }
        :return: 3-tuple of user, group, and usergoup gres dictionaries
        """
        # TODO: refactor SlurmDataGatherer to include get_users and get_groups methods. Then build in these next 3 variables into Ingestor.__init__() 

        # get all users and groups so we can update everybody's gres
        all_users = Counter([u.user.username for u in self.CVTUser.objects.all()])
        all_groups = Counter([g.name for g in self.Group.objects.filter(cluster=cluster)])
        all_ugls = Counter([(ugl.user.user.username, ugl.group.name) for ugl in self.UserGroupLink.objects.filter(group__cluster=cluster)])

        # list to hold the combos of user/group that were found in the job queue (we will subtract each of these from all)
        job_ugls = []
        
        if self.queue_dict is None:
            raise Exception("can't ingest gres due to no queue information")
        else:
            user_gres = {}
            group_gres = {}
            usergroup_gres = {}
            for job in self.queue_dict:
                if job['job_state'] != "R":
                    continue
                username = job['user']
                gres = job['gres']
                groupname = job['account']

                if username not in user_gres.keys():
                    user_gres[username] = []
                if groupname not in group_gres.keys():
                    group_gres[groupname] = []
                if username not in usergroup_gres.keys():
                    usergroup_gres[username] = []
                if groupname not in [k['group'] for k in usergroup_gres[username]]:
                    # create new group with gres list
                    job_ugls.append((username, groupname))  # add this combo to our list that keeps track of all usergroups we've added from the queue
                    usergroup_gres[username].append(
                        {'group': groupname, 'gres': []}
                    )
                try:
                    # find the index of the right dict inside the usergroup_gres dict and append gres
                    # to that
                    groups = [k['group'] for k in usergroup_gres[username]]
                    idx = groups.index(groupname)
                    usergroup_gres[username][idx]['gres'].append(gres)
                except ValueError as e:
                    print("Error: ingest_gres: ", end="")
                    print(e)
                user_gres[username].append(gres)
                group_gres[groupname].append(gres)
            
            # now we need to set the gres values of all users who were not in the job queue to 0
            # first convert the gres dicts into Counters so we can subtract them from the "all_*" Counters
            job_users = Counter(user_gres.keys())
            job_groups = Counter(group_gres.keys())
            job_ugls = Counter(job_ugls)
            
            remaining_users = all_users - job_users
            remaining_groups = all_groups - job_groups
            remaining_ugls = all_ugls - job_ugls

            
            for user in list(remaining_users):
                user_gres[user] = []
            for group in list(remaining_groups):
                group_gres[group] = []
            for ugl in list(remaining_ugls):
                user = ugl[0]
                group = ugl[1]
                if user not in usergroup_gres.keys():
                    usergroup_gres[user] = []
                usergroup_gres[user].append(
                    {'group': group, 'gres': []}
                )
            
            user_gres = self._ingest_user_gres(cluster, user_gres, gres_totals)
            group_gres = self._ingest_group_gres(cluster, group_gres, gres_totals)
            usergroup_gres = self._ingest_usergroup_gres(cluster, usergroup_gres, gres_totals)

            return (user_gres, group_gres, usergroup_gres)
