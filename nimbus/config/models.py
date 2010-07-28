#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from django.db import models
from django.conf import settings
from django.db.models.signals import post_save


from nimbus.base.models import UUIDSingletonModel as BaseModel
from nimbus.shared import utils, signals
from nimbus.libs.template import render_to_file



class Config(BaseModel):
    name = models.CharField(max_length=255, blank=False, null=False)
    director_name = models.CharField(max_length=255, blank=False, null=False)
    director_password = models.CharField( max_length=255, 
                                          default=utils.random_password,
                                          blank=False, null=False)
    director_address = models.IPAddressField(null=False, blank=False,
                                             default="127.0.0.1")


    def save(self, *args, **kwargs):
        if not self.director_name:
            self.director_name = self.uuid.uuid_hex
        super(Config, self).save(*args, **kwargs)



def update_director_file(config):
    """Generate director file"""

    filename = settings.BACULADIR_CONF

    render_to_file( filename,
                    "bacula-dir",
                    director_name=config.director_bacula_name(), 
                    director_port=config.director_port, 
                    director_password=config.director_password,
                    db_name=config.bacula_database_name(), 
                    db_user=config.bacula_database_user(), 
                    db_password=config.bacula_database_password())


    logger = logging.getLogger(__name__)
    logger.info("Arquivo de configuracao do director gerado com sucesso")


def update_console_file(config):
    """Update bconsole file"""


    filename = settings.BCONSOLE_CONF


    render_to_file( filename,
                    "bconsole",
                     director_name=config.director_name,
                     director_address=config.director_address,
                     director_password=config.director_password,
                     director_port=9103)   

    logger = logging.getLogger(__name__)
    logger.info("Arquivo de configuracao do bconsole gerado com sucesso")




signals.connect_on( update_director_file, Config, post_save)
signals.connect_on( update_console_file, Config, post_save)
