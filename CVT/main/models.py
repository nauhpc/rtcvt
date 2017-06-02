from django.db import models
from django.contrib.auth.models import User


class Scheduler(models.Model):
    TYPES = (
        ('slm', 'slurm'),
        ('trq', 'torque'),
        ('lsf', 'lsf'),
        ('pbs', 'pbs'),
    )

    notes = models.TextField(null=True, blank=True, max_length=255)
    type = models.CharField(max_length=3, choices=TYPES, default='slm')
    version = models.CharField(null=True, blank=True, max_length=20)

    class Meta:
        unique_together = (("type", "version"),)

    def __str__(self):
        return self.type


class Cluster(models.Model):
    OS = (
        ('COS', 'CentOS'),
        ('RHEL', 'Red Hat Enterprise Linux'),
        ('FED', 'Fedora'),
    )

    core_usage = models.FloatField(null=True, blank=True)  # decimal
    gres = models.ManyToManyField('Gres', through='GresClusterLink', through_fields=('cluster', 'gres'))
    jobs_pending = models.PositiveIntegerField(null=True, blank=True)
    jobs_running = models.PositiveIntegerField(null=True, blank=True)
    jobs_total = models.PositiveIntegerField(null=True, blank=True)
    mem_total = models.PositiveIntegerField()  # bytes
    mem_usage = models.FloatField(null=True, blank=True)  # decimal
    name = models.CharField(max_length=50, unique=True)
    node_usage = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True, max_length=255)
    num_cores = models.PositiveIntegerField()
    num_nodes = models.PositiveIntegerField()
    os = models.CharField(null=True, blank=True, max_length=4, choices=OS)
    os_version = models.CharField(null=True, blank=True, max_length=30)
    scheduler = models.ForeignKey('Scheduler', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Gres(models.Model):
    """ Generic Resource """
    type = models.CharField(max_length=25)
    total = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(null=True, blank=True, max_length=255)

    class Meta:
        unique_together = (("type", "total"),)

    def __str__(self):
        return self.type + ":" + str(self.total)


class Job(models.Model):
    STATES = (
        ('NF', 'node_failure'),
        ('F', 'failed'),
        ('TO', 'timeout'),
        ('SE', 'special_exit'),
        ('R', 'running'),
        ('PD', 'pending'),
        ('CG', 'completing'),
        ('CD', 'completed'),
        ('CA', 'cancelled'),
        ('CF', 'configuring'),
    )

    # TODO: change times to BigInteger
    cluster = models.ForeignKey('Cluster', on_delete=models.CASCADE)
    command = models.CharField(null=True, blank=True, max_length=255)
    elapsed_time = models.FloatField(default=0, blank=True)
    exec_end_time = models.FloatField(null=True, blank=True, default=0)
    exec_start_time = models.FloatField(null=True, blank=True, default=0)
    exp_start_time = models.FloatField(null=True, blank=True, default=0)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    licenses = models.CharField(null=True, blank=True, max_length=25)
    mem_usage = models.CharField(null=True, blank=True, max_length=50)
    name = models.CharField(max_length=255)
    notes = models.TextField(null=True, blank=True, max_length=255)
    opt_score = models.FloatField(null=True, blank=True)
    partition = models.CharField(max_length=50)  # in Slurm this is "partition", but in others it is called "queue"
    pending_time = models.FloatField(null=True, blank=True, default=0)
    reason_pending = models.CharField(null=True, blank=True, max_length=255)
    req_cores = models.PositiveIntegerField()
    req_mem = models.CharField(null=True, blank=True, max_length=25)
    req_nodes = models.PositiveIntegerField()
    sched_jobid = models.CharField(max_length=50)
    state = models.CharField(max_length=200, choices=STATES)
    submitted_time = models.FloatField()
    time_limit = models.FloatField(null=True, blank=True, default=0)
    tres_run_mins = models.CharField(max_length=100, null=True, blank=True)
    time_left = models.FloatField(null=True, blank=True, default=0)
    user = models.ForeignKey('CVTUser', on_delete=models.CASCADE)
    qos = models.CharField(null=True, blank=True, max_length=50)
    work_dir = models.CharField(null=True, blank=True, max_length=255)

    def fin(self):
        return self.state in ['NF', 'F', 'TO', 'SE', 'CD', 'CA']


class Group(models.Model):
    """ This represents an 'account' or 'group' in the scheduler that has a many-to-many relationship
        with the scheduler users """
    # TODO: Do we need group account manager as a field? i.e. the person in charge of the group
    name = models.CharField(max_length=50)
    memory = models.BigIntegerField(null=True, blank=True, default=0)
    node = models.BigIntegerField(null=True, blank=True, default=0)
    energy = models.BigIntegerField(null=True, blank=True, default=0)
    cpu = models.BigIntegerField(null=True, blank=True, default=0)
    total_memory = models.BigIntegerField(null=True, blank=True)
    total_node = models.BigIntegerField(null=True, blank=True)
    total_energy = models.BigIntegerField(null=True, blank=True)
    total_cpu = models.BigIntegerField(null=True, blank=True)

    fairshare = models.FloatField(null=True, blank=True)
    users = models.ManyToManyField('CVTUser', through='UserGroupLink', through_fields=('group', 'user'))
    gres = models.ManyToManyField(Gres, through='GresGroupLink', through_fields=('group', 'gres'))
    cluster = models.ForeignKey('Cluster', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class UserGroupLink(models.Model):
    user = models.ForeignKey('CVTUser')
    group = models.ForeignKey('Group')
    memory = models.BigIntegerField(null=True, blank=True, default=0)
    node = models.BigIntegerField(null=True, blank=True, default=0)
    energy = models.BigIntegerField(null=True, blank=True, default=0)
    cpu = models.BigIntegerField(null=True, blank=True, default=0)
    fairshare = models.FloatField(null=True, blank=True)
    gres = models.ManyToManyField(Gres, through='GresUserGroupLinkLink', through_fields=('ugl', 'gres'))

    def __str__(self):
        return "user: " + str(self.user) + ", group: " + str(self.group)


class GresClusterLink(models.Model):
    cluster = models.ForeignKey('Cluster', on_delete=models.CASCADE)
    gres = models.ForeignKey('Gres', on_delete=models.CASCADE)
    usage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return "cluster: " + self.cluster.name + " " + str(self.gres)

class GresGroupLink(models.Model):
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    gres = models.ForeignKey('Gres', on_delete=models.CASCADE)
    usage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return "group: " + self.group.name + " " + str(self.gres)

class GresUserGroupLinkLink(models.Model):
    ugl = models.ForeignKey('UserGroupLink', on_delete=models.CASCADE)
    gres = models.ForeignKey('Gres', on_delete=models.CASCADE)
    usage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return "user: " + str(self.ugl.user) + " group: " + str(self.ugl.group)

class GresCVTUserLink(models.Model):
    user = models.ForeignKey('CVTUser', on_delete=models.CASCADE)
    gres = models.ForeignKey('Gres', on_delete=models.CASCADE)
    usage = models.FloatField(blank=True, null=True)

    def __str__(self):
        return "user: " + str(self.user) + " " + str(self.gres)

class CVTUser(models.Model):
    user = models.OneToOneField(User)
    memory = models.BigIntegerField(null=True, blank=True, default=0)
    node = models.BigIntegerField(null=True, blank=True, default=0)
    energy = models.BigIntegerField(null=True, blank=True, default=0)
    cpu = models.BigIntegerField(null=True, blank=True, default=0)
    notes = models.TextField(max_length=255, blank=True, null=True)
    groups = models.ManyToManyField(Group, through='UserGroupLink', through_fields=('user', 'group'))
    gres = models.ManyToManyField(Gres, through='GresCVTUserLink', through_fields=('user', 'gres'))

    def __str__(self):
        return self.user.username
