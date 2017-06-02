"""
slurm.py - subprocess-based API to slurm squeue commands
 
This gives Python programs the ability to call slurm commands using the `squeue ...` commands instead of the C API.
IMPORTANT - This module may not provide enough speed for realistic use cases due to the overhead of commandline calls.
"""
from collections import OrderedDict
from .DataGatherer import (DataGatherer, DataGathererError, run)


def parse_gres(data=None):
    d = {}
    if data is not None:
        if type(data) != list:
            raise TypeError("data parameter must be a list")
        for line in data:
            gres = line.split(',')
            for g in gres:
                info = g.split(':')
                if len(info) < 2 or 'no_consume' in info or 'null' in info:
                    # this means the resource is either a 'non-consumable' resource or there's an error and shouldn't be counted
                    continue
                try:
                    num = int(info[
                                  -1])  # try to turn the amount of the resource from string into int (should be the last item)
                except ValueError:
                    continue
                if info[0] in d:
                    d[info[0]] += num
                else:
                    d[info[0]] = num
    return d

def run_sacct(job_ids):
    """
    runs the sacct command and returns information from sacct

    :param job_ids: String. Comma-separated list of slurm jobids
    :return: list of dictionaries, each holding job information
    """
    """ TODO: Implement these fields
    fields = OrderedDict([
        (1, "jobid"),
        (2, "avecpu"),
        (3, "avecpufreq"),
        (4, "averss"),
        (5, "avevmsize"),
        (6, "elapsed"),
        (7, "maxrss"),
        (8, "maxvmsize"),
        (9, "start"),
        (10, "state"),
        (11, "usercpu")
    ])
    """
    fields = ["jobid", "elapsed", "start", "end", "state", "maxrss"]

    fields_str = ','.join(fields)

    if not isinstance(job_ids, str):
        raise TypeError("expected string of a single jobid or comma-separated jobids")
    else:
        # TODO: Watch out for the "grep" pipe in this call! If we refactor this to include job steps, we'll have to take that out!
        cmd = "sacct --jobs=%s --parsable2 --noheader --format=%s | grep -v [.]" % (job_ids, fields_str)
        if "," in job_ids:
            raise NotImplementedError("the functionality of running sacct on multiple jobs is not done yet")
        else:
            out = run(cmd)
            jobs = out.split('\n')
            results = []
            i = 0
            if len(jobs) == 0:
                return {}
            for job in jobs:
                job_info = job.split('|')
                if len(job_info) < len(fields):  # in jobs submitted with sbatch, the first result can sometimes be missing a lot of stuff
                    continue
                results.append({})
                for j, v in enumerate(fields):
                    results[i][v] = job_info[j]
                i += 1
        return results


class SlurmDataGatherer(DataGatherer):
    """
    Class for interacting with Slurm via command line calls (not the C api)
    """
    queue_fields = {
        "account": "%a",
        "job_id": "%A",
        "gres": "%b",
        "memory": "%m",
        "cpus": "%C",
        "nodes": "%D",
        "features": "%f",
        "job_name": "%j",
        "comment": "%k",
        "time_limit": "%l",
        "elapsed_time": "%M",
        "exec_command": "%o",
        "priority": "%p",
        "partition": "%P",
        "qos": "%q",
        "reason": "%r",
        "start_time": "%S",
        "job_state": "%t",
        "user": "%u",
        "reservation": "%v",
        "submit_time": "%V",
        "licenses": "%W",
        "work_dir": "%Z",
        "time_left": "%L",
    }

    def __init__(self, scheduler, cluster):
        super().__init__(scheduler, cluster)
        self._scheduler_version = self._get_scheduler_version()
        # TODO: Possible idea: keep a temporary data struct of sshare info and a timestamp of the last pull. This way,
        # if looking up a single user or group, we can consult the struct if it was pulled less than x seconds ago...
        #self._tmp_sshare = {}
        #self._last_pull = None

    def _get_scheduler_version(self):
        cmd = "sinfo -V"
        out = run(cmd)
        try:
            version = out.split(' ')[1]
        except Exception as e:
            print(e)
            raise DataGathererError
        return version



    def _get_gres_used(self):
        jobs = self.get_queue(state="running", filters=['%b'])
        gres = []
        for job in jobs:
            for v in job.values():
                if 'null' in v:
                    continue
                gres.append(v)
        return parse_gres(gres)

    def _get_sshare(self):
        """ gets long listing of sshare command for all users"""
        cmd = "sshare -al --parsable2"
        out = run(cmd)
        headings = out.split('\n')[0]
        headings = [h.lower() for h in headings.split('|')]
        # get the positions in the output where relevant info is located
        try:
            acct_idx = headings.index("account")
            user_idx = headings.index("user")
            fshare_idx = headings.index("fairshare")
            tres_idx = headings.index("tresrunmins")
        except ValueError as e:
            print(e)
            raise DataGathererError("`sshare -al --parsable2` output was not formatted as expected")
        data = out.split('\n')[1:]
        group_sshare = {}
        user_sshare = {}
        for line in data:
            line = line.split('|')
            if len(line) != len(headings):
                raise DataGathererError("the number of headings and columns of data don't match")
            if line[user_idx] == "":
                # this line has no user, so it must be an account/group
                acct = line[acct_idx].strip()
                if acct == "":
                    continue  # no user or account...this line is extraneous!
                group_sshare[acct] = {}  # create new group in our dict
                group_sshare[acct]["fairshare"] = float(line[fshare_idx])
                group_sshare[acct]["tresrunmins"] = self._parse_tres(line[tres_idx])
            else:
                user = line[user_idx].strip()
                if user in user_sshare.keys():
                    user_sshare[user].append({})
                    pos = len(user_sshare[user]) - 1
                else:
                    pos = 0
                    user_sshare[user] = [{}]
                user_sshare[user][pos]["account"] = line[acct_idx].strip()
                user_sshare[user][pos]["fairshare"] = float(line[fshare_idx])
                user_sshare[user][pos]["tresrunmins"] = self._parse_tres(line[tres_idx])

        return (group_sshare, user_sshare)

    def _parse_tres(self, data):
        tres = [d for d in data.split(',')]
        tres_dict = {}
        for t in tres:
            tmp = t.split('=')
            tres_dict[tmp[0]] = int(tmp[1])
        return tres_dict

    #### Public methods ####
    def get_num_cpus(self, force=False):
        if self._num_cpus is None or force:
            cmd = "sinfo -h -o %C"
            out = run(cmd)
            stats = out.split('/')
            if len(stats) != 4:
                raise DataGathererError("sinfo did not return A/I/O/T format")
            self._num_cpus = int(stats[3])
        return self._num_cpus

    def get_num_nodes(self, force=False):
        if self._num_nodes is None or force:
            cmd = "sinfo -h -o %F"
            out = run(cmd)
            stats = out.split('/')
            if len(stats) != 4:
                raise DataGathererError("sinfo did not return A/I/O/T format")
            self._num_nodes = int(stats[3])
        return self._num_nodes

    def get_total_mem(self, force=False):
        if self._total_mem is None or force:
            cmd = "sinfo -h --Node -o %m"  # This outputs FREE_MEM | MEMORY for every node
            out = run(cmd)
            results = out.split('\n')
            total_mem = 0
            for mem in results:
                mem.strip()
                try:
                    total_mem += int(mem)
                except ValueError as e:
                    print(e)
                    return -1
            self._total_mem = total_mem
        return self._total_mem

    def get_queue(self, state="all", filters=None):
        """
        Calls the `squeue` command and returns the output
 
        :param state: the jobs of a specific state you would like to pull from the queue
        :param filters: slurm squeue output formatting options (e.g. %b, %a, etc...)
        :return: list of dicts of squeue information
        """
        cmd = "squeue --state=%s" % state
        headings = []
        custom_headings = False

        if filters is not None:
            format = ""
            try:
                if type(filters) == list:
                    for f in filters:
                        format += f + "\|"  # This builds out a string we can send to the command line that is pipe-delimited
                    cmd += " --format=%s" % format[:-1]  # get rid of last bar
                elif type(filters) == dict:
                    custom_headings = True
                    for k, v in filters.items():
                        headings.append(k)
                        format += v + "\|"
                    cmd += " -h --format=%s" % format[:-1]  # no header
                else:
                    raise TypeError("filters must be a list or dict")
            except Exception as e:
                print(e)
                return
        else:
            cmd += " --format=%all"  # all fields available with no header in the output

        out = run(cmd)
        if not custom_headings:  # if filters was a list
            headings = out.split('\n')[0]
            headings = [h.lower() for h in headings.split('|')]
            data = out.split('\n')[1:]
        else:  # filters was a dict with custom headings
            data = out.split('\n')
        results = []

        # if queue is empty, data will be [""]
        if len(data) == 0 or data[0] == "":
            return []

        for d in data:
            tmp_list = d.split('|')
            tuples = []
            for i in range(len(tmp_list)):
                val = ""
                if headings[i] in ("cpus", "nodes"):
                    try:
                        val = int(tmp_list[i])
                    except ValueError as e:
                        print(e)
                elif headings[i] in ("priority"):
                    try:
                        val = float(tmp_list[i])
                    except ValueError:
                        try:
                            val = int(tmp_list[i])
                        except ValueError as e:
                            print(e)
                            val = tmp_list[i]
                else:
                    val = tmp_list[i]
                tuples.append((headings[i], val))

            tmp_dict = {k: v for k, v in tuples}
            results.append(tmp_dict)
        self._queue = results
        return results

    def get_total_jobs(self, state="all"):
        if state == "all":
            cmd = " squeue -h |wc -l"
        elif state == "running":
            cmd = " squeue -h -t R|wc -l"
        elif state == "pending":
            cmd = " squeue -h -t PD|wc -l"
        else:
            raise DataGathererError("state argument is not valid. Must be one of 'all', 'running', 'pending'.")

        out = run(cmd)
        try:
            total = int(out)
        except Exception as e:
            print(e)
            raise DataGathererError("output of `%s` couldn't be converted to integer" % cmd)
        return total

    def get_tres_totals(self, tres_data=None):
        """
        gets all the GrpTresRunMins numbers for all groups. This tells us how many total cpumins each group is allowed

        :param tres_data: String of tres data as | delimited output directly from slurm. This variable is added in case we want to
        pass in the data instead of call sacctmgr (mainly for testing purposes)

        :return: dict with group names as keys and cpu and mem totals as a values (also dicts)
        Example:
            {
                "group1": {
                    "cpu": 700000,
                    "mem": 28889928
                },
                "group2": {
                    ...
                }
            }
        """
        if tres_data is None:
            # only run the command to parse slurm if no data was passed into this method
            cmd = "sacctmgr show assoc --parsable2"
            out = run(cmd)
        else:
            out = tres_data
        # get all the headings as a list
        headings = out.split('\n')[0]
        headings = [h.lower() for h in headings.split('|')]
        # get all the data as a list of | separated strings
        data = out.split('\n')[1:]
        # get all the indices of the headings we care about
        acct_idx = headings.index("account")
        user_idx = headings.index("user")
        share_idx = headings.index("share")
        tres_idx = headings.index("grptresrunmins")
        tres_totals = {}
        for d in data:
            info = d.split('|')
            group = info[acct_idx]
            user = info[user_idx]
            is_parent = info[share_idx]
            # we only care about group information (i.e. those who are "parent" accounts)
            if is_parent != "parent" or user != "":
                continue
            tres_info = info[tres_idx]
            tres_info = tres_info.split(',')

            # a group can be 'parent' and yet have no tres info, so skip it
            if len(tres_info) == 0 or tres_info[0] == "":
                continue
            tmp = {}
            for tres in tres_info:
                t_type = tres.split('=')[0]
                t_value = tres.split('=')[1]
                t_value = ''.join(c for c in t_value if c.isdigit()) # remove any characters, e.g. M from the end of memory number
                tmp[t_type] = int(t_value)
            tres_totals[group] = tmp
        return tres_totals

    def get_usage(self, type="all"):
        """
        Gets cpu usage of the cluster as a percentage. This function assumes that
        cpus labeled "other" represents cpus that should be taken out of the total available pool.

        :param type: String representing the usage of interest. "all" is the default. Possible values are "cpu", "node",
        "gres", "all", and "mem"
        :return: float representing percent of cpus used, or -1 if there is no information available
        """

        if type == "all":
            #cmd = "sinfo -h -o %C\|%F\|%G"  # gets cpus|nodes|gres  # alternative idea: call  more at once and parse results

            # This is the quick and dirty method: call each command separately
            ud = {}
            ud["memory"] = self.get_mem_usage()
            ud["node"] = self.get_usage("node")
            ud["cpu"] = self.get_usage("cpu")
            ud["gres"] = self.get_usage("gres")
            ud["jobs_total"] = self.get_total_jobs()
            ud["jobs_running"] = self.get_total_jobs("running")
            ud["jobs_pending"] = self.get_total_jobs("pending")

            return ud

        elif type == "cpu":
            cmd = "sinfo -h -o %C"
        elif type == "node":
            cmd = "sinfo -h -o %F"
        elif type == "gres":
            cmd = "sinfo -h -o %G"
        elif type == "mem":
            return self.get_mem_usage()
        else:
            raise ValueError("SlurmDataGatherer.get_usage only allows 'cpu', 'gres', 'node', 'mem', and 'all' as options for the 'type' parameter")

        out = run(cmd)
        if type == "gres":
            gres_total_dict = parse_gres(out.split())
            gres_used_dict = self._get_gres_used()
            gres_pct = {}
            for k,v in gres_total_dict.items():
                try:
                    gres_pct[k] = {}
                    gres_pct[k]["total"] = v
                    gres_pct[k]["usage"] = round(gres_used_dict[k] / float(v), 4)
                except Exception as e:
                    print(e)
                    gres_pct[k] = {}
                    gres_pct[k]["total"] = v
                    gres_pct[k]["usage"] = 0.0
            return gres_pct

        # if we get here, then type was either cpu or node
        stats = out.split('/')
        if len(stats) != 4:
            raise DataGathererError("sinfo did not return A/I/O/T format")
        alloc = int(stats[0])
        other = int(stats[2])
        total = int(stats[3])
        if other > total:
            raise ValueError("'other' was greater than the total! Something is amiss...")
        total -= other
        try:
            pct = round(float(alloc) / float(total), 4)
        except ZeroDivisionError:
            pct = 0.0
        return pct

    def get_cpu_usage(self):
        return self.get_usage(type="cpu")

    def get_node_usage(self):
        """
        Gets node usage of entire cluster as a percentage. This function assumes that
        nodes labeled "other" represents ones that should be taken out of the total available pool.

        :return: float representing percent of nodes used
        """
        return self.get_usage(type="node")

    def get_mem_usage(self):
        """
        Gets the overall usage of memory over the entire cluster as a percentage
        :return: dictionary represent
        """
        cmd = "sinfo -h --Node -o %e\|%m"  # This outputs FREE_MEM | MEMORY for every node
        out = run(cmd)
        results = out.split('\n')
        free_mem = 0
        total_mem = 0

        try:
            for line in results:
                mem = line.split('|')
                free_mem += int(mem[0])
                total_mem += int(mem[1])
        except ValueError:
            return "NA"

        if total_mem < free_mem:
            raise ValueError("total memory was found to be less than free memory. Check your Slurm config!")
        used_mem = total_mem - free_mem
        if used_mem < 0:
            raise ValueError("used memory was found to be negative. I think someone goofed.")
        pct = round(float(used_mem) / float(total_mem), 4)
        return pct

    def get_groupshare(self, group=None):
        return self._get_sshare()[0]

    def get_usershare(self, user=None):
        return self._get_sshare()[1]

    def get_data(self):
        """ Gets all real-time data from the cluster"""
        data = {}
        data['cluster'] = self.get_cluster_name()
        data['scheduler'] = {}
        data['scheduler']['type'] = self.get_scheduler()
        data['scheduler']['version'] = self.get_scheduler_version()
        data['queue'] = self.get_queue(filters=self.queue_fields)
        sshare = self._get_sshare()
        data['group_share'] = sshare[0]
        data['user_share'] = sshare[1]
        data['usage'] = {}
        data['usage']['node'] = self.get_node_usage()
        data['usage']['cpu'] = self.get_cpu_usage()
        data['usage']['memory'] = self.get_mem_usage()
        data['usage']['gres'] = self.get_usage(type='gres')
        return data
