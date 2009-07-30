#!/usr/bin/python
# -*- coding: utf-8 -*-

# Application
from backup_corporativo.bkp.utils import *
from backup_corporativo.bkp.views import global_vars, require_authentication, authentication_required
from backup_corporativo.bkp.models import Computer
from backup_corporativo.bkp.models import Procedure
# Misc
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404

@authentication_required
def tmp_restore(request, computer_id, procedure_id, job_id):
    vars_dict, forms_dict, return_dict = global_vars(request)
    vars_dict['comp'] = get_object_or_404(Computer, pk=computer_id)
    vars_dict['proc'] = get_object_or_404(Procedure, pk=procedure_id)
    vars_dict['job_id'] = job_id

    if request.method == 'GET':
        vars_dict, forms_dict, return_dict = global_vars(request)
        vars_dict['comp'] = get_object_or_404(Computer, pk=computer_id)
        if not 'fset' in request.GET:
            raise Exception('JobID parameter is missing.')
        if not 'dt' in request.GET:
            raise Exception('Date parameter is missing.')
        if not 'src' in request.GET:
            raise Exception('ClientName parameter is missing.')

        vars_dict['src_client'] = request.GET['src']
        vars_dict['target_dt'] = request.GET['dt']
        vars_dict['fileset_name'] = request.GET['fset']
        vars_dict['comp_id'] = computer_id
        forms_dict['restore_form'] = RestoreForm()

        # Load forms and vars
        vars_dict['file_count'],vars_dict['file_tree'] = vars_dict['proc'].get_file_tree(job_id)
        return_dict = merge_dicts(return_dict, forms_dict, vars_dict)
        return render_to_response('bkp/tmp/new_tmp_restore.html', return_dict, context_instance=RequestContext(request))


@authentication_required
def view_procedure(request, computer_id, procedure_id):
    vars_dict, forms_dict, return_dict = global_vars(request)
    vars_dict['comp'] = get_object_or_404(Computer, pk=computer_id)
    vars_dict['proc'] = get_object_or_404(Procedure, pk=procedure_id)

    if request.method == 'GET':
        # Load forms and vars
        vars_dict['restore_jobs'] = vars_dict['proc'].restore_jobs()
        return_dict = merge_dicts(return_dict, forms_dict, vars_dict)
        return render_to_response('bkp/tmp/view_procedure.html', return_dict, context_instance=RequestContext(request))


@authentication_required
def restore_files(request, computer_id, procedure_id, job_id):
    from backup_corporativo.bkp.bacula import Bacula
    vars_dict, forms_dict, return_dict = global_vars(request)
    vars_dict['comp'] = get_object_or_404(Computer, pk=computer_id)
    vars_dict['proc'] = get_object_or_404(Procedure, pk=procedure_id)
    
    if request.method == 'POST':
        Bacula.restore_files(request.POST)
        