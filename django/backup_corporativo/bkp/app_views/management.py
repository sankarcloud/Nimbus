#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404

from backup_corporativo.bkp import utils
from backup_corporativo.bkp.models import Storage
from backup_corporativo.bkp.views import global_vars, authentication_required

from keymanager import KeyManager

@authentication_required
def main_management(request):
    vars_dict, forms_dict = global_vars(request)

    if request.method == 'GET':
        return_dict = utils.merge_dicts(forms_dict, vars_dict)
        return render_to_response(
            'bkp/management/main_management.html',
            return_dict,
            context_instance=RequestContext(request))

@authentication_required
def list_computers(request):
    vars_dict, forms_dict = global_vars(request)

    if request.method == 'GET':
        # Reaproveitar lista de computadores declarada em global_vars()
        vars_dict['comp_list'] = vars_dict['comps']
        return_dict = utils.merge_dicts(forms_dict, vars_dict)
        return render_to_response(
            'bkp/management/list_computers.html',
            return_dict, context_instance=RequestContext(request))

@authentication_required
def list_storages(request):
    vars_dict, forms_dict = global_vars(request)

    if request.method == 'GET':
        vars_dict['sto_list'] = Storage.objects.all()
        return_dict = utils.merge_dicts(forms_dict, vars_dict)
        return render_to_response(
            'bkp/management/list_storages.html',
            return_dict,
            context_instance=RequestContext(request))

@authentication_required
def manage_strongbox(request):
    vars_dict, forms_dict = global_vars(request)
    
    if request.method == 'GET':
        return render_to_response(
            'bkp/management/manage_strongbox.html',
            return_dict,
            context_instance=RequestContext(request))

def create_strongbox(request):
    if request.method == 'POST':
        km = KeyManager()
        km
        
        
