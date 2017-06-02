# Create your tasks here
from __future__ import absolute_import, unicode_literals
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from celery.signals import celeryd_after_setup
from datetime import timedelta

from CVT.celery import logger, app
#import CVT.CVTConfig.Scheduler.SLURM.ingestor as ingestor
#import CVT.CVTConfig.Scheduler.SLURM.datagatherer as SDG
from main.models import (Cluster, Scheduler, Job, Group, CVTUser, UserGroupLink)
from CVT.CVTConfig import Modules

ingestor = Modules.SLURM.ingestor()
SDG = Modules.SLURM.datagatherer

def get_cluster_sdg(cluster_name):
    try:
        c = Cluster.objects.get(name=cluster_name)
        s = c.scheduler.type
        sdg = SDG(s, c)
        return (c, sdg)
    except ObjectDoesNotExist:
        print("Error: cluster with name '%s' does not exist" % cluster_name)
        return None

def _create_clusters(c):
    """
    Should be run at celery worker init, so it checks if all the clusters are created properly
    before running any other tasks.
    :param: c - list of all the cluster configs. These should each be dictionaries
    """
    if c is None:
        logger.info("no clusters were passed to create_clusters")
    for cluster in c:
        try:
            cl = Cluster.objects.get(name=cluster["name"])
            logger.info("found cluster '%s'" % cl.name)
        except ObjectDoesNotExist:
            sdg = SDG(cluster["scheduler"], cluster["name"])
            mem = sdg.get_total_mem()
            nodes = sdg.get_num_nodes()
            cpus = sdg.get_num_cpus()
            s = Scheduler.objects.create(type=cluster["scheduler"])
            cl = Cluster.objects.create(
                name=cluster["name"],
                scheduler=s,
                mem_total=mem,
                num_nodes=nodes,
                num_cores=cpus
            )
            logger.info("cluster '%s' created" % cluster["name"])


@app.task
def task_ingest_queue(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        q = sdg.get_queue(filters=sdg.queue_fields)
        ingestor.ingest_queue(cluster, q)
    else:
        logger.error("couldn't create DataGatherer object for ingest_queue")
    

@app.task
def task_ingest_usage(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        usage = sdg.get_usage()
        ingestor.ingest_usage(cluster, usage)

@app.task
def task_ingest_groupshare(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        groupshare = sdg.get_groupshare()
        ingestor.ingest_groupshare(cluster, groupshare)

@app.task
def task_ingest_usershare(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        usershare = sdg.get_usershare()
        ingestor.ingest_usershare(cluster, usershare)

@app.task
def task_ingest_gres(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        gres_totals = sdg.get_usage(type="gres")
        ingestor.ingest_gres(cluster, gres_totals)

@app.task
def task_update_jobs(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        ingestor.update_jobs(cluster)

@app.task
def clear_old_jobs(cluster_name):
    cluster, sdg = get_cluster_sdg(cluster_name)
    if sdg is not None:
        # We only want jobs which were submitted more than `jct` seconds ago, so we 
        cutoff_time = current_time.timestamp() - 60
        to_filter = Job.objects.all().filter(submitted_time < cutoff_time)
        to_filter = [x for x in to_filter if x.fin()]
        to_filter.delete()


#### Tasks to perform one time at system start ####
@celeryd_after_setup.connect
def initial_setup(sender, instance, **kwargs):
    from CVT.CVTConfig import clusters
    
    logger.info("performing cluster setup")
    #q_name = '{0}'.format(sender)  # hostname of the worker (sender)
    #logger.info(q_name)
    _create_clusters(clusters)
    logger.info("determining tres totals for each group")
    for cluster in Cluster.objects.all():
        sdg = SDG(cluster.scheduler.type, cluster.name)
        tres = sdg.get_tres_totals()
        ingestor.ingest_tres_totals(cluster, tres)


