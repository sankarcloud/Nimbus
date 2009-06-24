#!/usr/bin/python
# -*- coding: utf-8 -*-

# Application
from backup_corporativo.bkp.utils import *
from backup_corporativo.bkp.models import ExternalDevice
from backup_corporativo.bkp.forms import ExternalDeviceForm
from backup_corporativo.bkp.views import global_vars, require_authentication, authentication_required
# Misc
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404

### Device ###
@authentication_required
def new_device(request):
    vars_dict, forms_dict, return_dict = global_vars(request)

    if request.method == 'GET':
        forms_dict['devform'] = ExternalDeviceForm()
        return_dict = merge_dicts(return_dict, forms_dict, vars_dict)
        return render_to_response('bkp/new_device.html', return_dict, context_instance=RequestContext(request))


@authentication_required
def create_device(request):
    vars_dict, forms_dict, return_dict = global_vars(request)

    if request.method == 'POST':
        forms_dict['devform'] = ExternalDeviceForm(request.POST)
        if forms_dict['devform'].is_valid():
            forms_dict['devform'].save()
            request.user.message_set.create(message="Device adicionado com sucesso.")            
            return HttpResponseRedirect(root_path(request))
        else:
            return_dict = merge_dicts(return_dict, forms_dict, vars_dict)
            return render_to_response('bkp/new_device.html', return_dict, context_instance=RequestContext(request))