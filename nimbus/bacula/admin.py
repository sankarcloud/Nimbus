#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from django.conf import settings
from django.contrib import admin

from nimbus.bacula import models

# admin.site.register(models.Profile)
admin.site.register(models.Job)
admin.site.register(models.JobMedia)
admin.site.register(models.Media)
admin.site.register(models.File)

