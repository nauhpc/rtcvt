from enum import Enum
from .DataGatherer import DataGatherer 
from .ingestor import Ingestor as SlurmIngestor 
from .SlurmDataGatherer import SlurmDataGatherer 

clusters = [
    {
        "name": "wavefront",
        "scheduler": "slm",
        "polling": {
            "queue_interval": 5,
            "usage_interval": 10,
            "groupshare_interval": 8,
            "usershare_interval": 12,
            "gres_interval": 11,
        },
    }
]


# UI_COLORCODING is an array of tuples. The tuples contains a percentage threshold and a color, in that order comma-seperated.
UI_COLORCODING = [
    (.8,"#bf4133"),
    (.5,"#cece2b"),
]

# Timeout for completed jobs to be deleted from the database in number of seconds. For example:
# 24 hours is 86400 seconds
# 3 days is 259200 seconds
# 7 days is 604800 seconds
# 30 days is 2592000 seconds
job_clear_timeout = 86400


class Modules(Enum):
    SLURM = (SlurmIngestor, SlurmDataGatherer)

    def __init__(self, ingestor, datagatherer):
        self.datagatherer = datagatherer
        self.ingestor = ingestor

    def ingestor(self):
        return self.ingestor
    def datagatherer(self):
        return self.datagatherer

########## VARIABLE DEFINITION CHECKER(DO NOT MODIFY) ##########
for cluster in clusters:
    if not 'name' in cluster:
        raise Exception('A Cluster is missing the name Field.')
    if not 'scheduler' in cluster:
        raise Exception(cluster['name']+' is missing the scheduler Field.')
    if not 'polling' in cluster:
        raise Exception(cluster['name']+' is missing the polling Field.')
    if not 'queue_interval' in cluster['polling']:
        raise Exception(cluster['name']+'\'s Polling is missing the queue_interval Field.')
    if not 'usage_interval' in cluster['polling']:
        raise Exception(cluster['name']+'\'s Polling is missing the usage_interval Field.')
    if not 'groupshare_interval' in cluster['polling']:
        raise Exception(cluster['name']+'\'s Polling is missing the groupshare_interval Field.')
    if not 'usershare_interval' in cluster['polling']:
        raise Exception(cluster['name']+'\'s Polling is missing the usershare_interval Field.')
    if not 'gres_interval' in cluster['polling']:
        raise Exception(cluster['name']+'\'s Polling is missing the gres_interval Field.')

if not isinstance(job_clear_timeout, int):
    raise Exception("job_clear_timeout must be an integer, not %s" % type(job_clear_timeout))

for colorCode in UI_COLORCODING:
    if not isinstance(colorCode, tuple):
        raise Exception('UI_COLORCODING should be an ARRAY of TUPLES.')
UI_COLORCODING=sorted(UI_COLORCODING,key=(lambda item: item[0])) #sort by first entry in tuple

################################################################