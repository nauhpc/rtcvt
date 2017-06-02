from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.utils.log import get_task_logger
from celery.signals import worker_init, beat_init, celeryd_init, celeryd_after_setup
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps

# TODO: Do we need to add an IP address to the clusters??
# TODO: What about the ingestor and datagatherer class?? -- this would mean changing the models too


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CVT.settings')

app = Celery('CVT')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

logger = get_task_logger(__name__)

"""
app.conf.CELERYBEAT_SCHEDULE = {
    'ingest_queue': {
        'task': 'main.tasks.task_ingest_queue',
        'schedule': 10,
        'args': ("Testing queue ingestion",)
    }
}
"""
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from .CVTConfig import (
        clusters,
        job_clear_timeout,
    )

    from main.tasks import (
        task_ingest_queue,
        task_ingest_usage,
        task_ingest_groupshare,
        task_ingest_usershare,
        task_ingest_gres,
        task_update_jobs,
        clear_old_jobs,
    )

    for cluster in clusters:
        name = cluster["name"]
        usage_int = cluster["polling"]["usage_interval"]
        q_int = cluster["polling"]["queue_interval"]
        user_int = cluster["polling"]["usershare_interval"]
        group_int = cluster["polling"]["groupshare_interval"]
        gres_int = cluster["polling"]["gres_interval"]
        sender.add_periodic_task(usage_int, task_ingest_usage.s(name), name="%s ingest usage" % name)
        sender.add_periodic_task(q_int, task_ingest_queue.s(name), name="%s ingest queue" % name)
        sender.add_periodic_task(group_int, task_ingest_groupshare.s(name), name="%s ingest groupshare" % name)
        sender.add_periodic_task(user_int, task_ingest_usershare.s(name), name="%s ingest usershare" % name)
        sender.add_periodic_task(gres_int, task_ingest_gres.s(name), name="%s ingest gres" % name)
        sender.add_periodic_task(q_int, task_update_jobs.s(name), name="%s update jobs" % name)
        sender.add_periodic_task(job_clear_timeout, clear_old_jobs.s(name), name="%s clear old tasks" % name)
        logger.debug("added periodic tasks for cluster '%s'" % name)


@app.task
def test(arg):
    print(arg)

if __name__ == '__main__':
    app.start()
