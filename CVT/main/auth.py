from django_cas_ng.backends import CASBackend
import pamela
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NAUCASBackend(CASBackend):
    """
    authentication backend that checks against NAU CAS server
    """
    def user_can_authenticate(self, user):
        try:
            logger.debug("USER AUTHENTICATED: %s" % user.username)
            # if no exception is raised, the user exists in PAM LDAP on this system
            pamela.check_account(user.username)
        except Exception:
            logger.error("PROBLEM WITH LOGIN: %s" % user.username + ". Deleting user.")
            user.delete()
            return False
        return True
