from django.conf.urls.defaults import *

urlpatterns = patterns('nimbus.wizard.views',
    (r'^network/$', 'network'),
    (r'^finish/$', 'finish'),
    (r'^license/$', 'license'),
    (r'^password/$', 'password'),
    (r'^timezone/$', 'timezone'),
)
