# -*- coding: utf-8 -*-


from threading import Thread

import simplejson
from os.path import getsize

from django.views.generic import create_update
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.core import validators

from nimbus.computers.models import Computer
from nimbus.shared.views import render_to_response
from nimbus.shared import utils
from nimbus.shared.forms import form
from nimbus.libs import offsite
from nimbus.libs.devicemanager import (StorageDeviceManager,
                                       MountError, UmountError)
import networkutils 
import systeminfo



def worker_thread(storage_manager):
    manager = offsite.LocalManager(origin=None,
                                  destination=storage_manager.mountpoint)
    manager.upload_all_volumes()
    storage_manager.umount()




@login_required
def network_tool(request, type="ping"):
    if type == "ping":
        title = u"Teste de ping"
    elif type == "traceroute":
        title = u"Teste de traceroute"
    elif type == "nslookup":
        title = u"Teste de ns lookup"
    
    extra_content = {'title': title, 'type': type}
    
    return render_to_response(request, "system_network_tool.html", extra_content)


@login_required
def create_or_view_network_tool(request):


    if request.method  == "POST":
    
        rtype = request.POST['type']
        ip = request.POST['ip']
        is_url = False

        try:
            try:
                validators.validate_ipv4_address(ip) # ip format x.x.x.x
            except ValidationError, error: # url format www.xxx.xxx
                value = ip
                if not '://' in value:
                    value = 'https://%s' % value
                urlvalidator = validators.URLValidator()
                urlvalidator(value)
                is_url  = True

            if rtype == "ping":
                rcode, output = networkutils.ping(ip)
            elif rtype == "traceroute":
                rcode, output = networkutils.traceroute(ip)
            elif rtype == "nslookup":
                if is_url:
                    output = networkutils.resolve_name(ip)
                else:
                    output = networkutils.resolve_addr(ip)

        except ValidationError, error:
            output = "\n".join(error.messages)
        

        response = simplejson.dumps({'msg': output})
        return HttpResponse(response, mimetype="text/plain")


@login_required
def stat(request):
    memory = systeminfo.get_memory_usage()
    memory_free = 100 - memory
    extra_content = { 
        'title': u"Estatística do sistema",
        'cpu' : systeminfo.get_cpu_usage(),
        'memory' : memory,
        'memory_free' : memory_free
    }

    return render_to_response(request, "stat.html", extra_content)



@login_required
def umount(request):
    if request.method == "GET":
        devices = offsite.list_disk_labels()
        title = u'Remover dispositivo externo com segurança'
        return render_to_response(request, "umount_storage.html", locals())

    if request.method == "POST":
        device = request.POST.get("device")

        try:
            manager = StorageDeviceManager(device)
            manager.umount()
        except UmountError, e:
            error = e
            messages.error(request, u"Erro ao remover unidade")

        messages.success(request, u"Unidade removida corretamente.")
        return redirect('nimbus.base.views.home')


# SECURITY COPY


@login_required
def security_copy(request):
    title = u"Cópia de segurança"
    return render_to_response(request, "system_security_copy.html", locals())


@login_required
def select_storage(request):
    devices = offsite.list_disk_labels()
    title = u'Cópia de segurança'
    return render_to_response(request, "system_select_storage.html", locals())


@login_required
def copy_files(request):

    if request.method == "POST":
        error = None
        device = request.POST.get("device")

        if not device:
            raise Http404()

        try:
            manager = StorageDeviceManager(device)
            manager.mount()
        except MountError, e:
            error = e

        sizes = [ getsize( dev) for dev in offsite.get_all_bacula_volumes() ]
        required_size = sum( sizes )


        if required_size <  manager.available_size:
            thread = Thread(target=worker_thread, args=(manager,))
            thread.start()
            messages.success(request, u"O processo foi iniciado com sucesso.")
            return redirect('nimbus.offsite.views.list_uploadrequest')
        else:
            required_size = utils.bytes_to_mb(required_size)
            available_size = utils.bytes_to_mb(manager.available_size)
            manager.umount()
            error = u"Espaço necessário é de %.3fMB, somente %.3fMB disponível em %s" %\
                    (required_size, available_size, device)

        if error:
            return render_to_response(request, "bkp/offsite/mounterror.html",
                    {"error" : error } )


@login_required
def pid_history(request):
    from nimbus.offsite.models import UploadRequest, DownloadRequest
    from datetime import datetime
    
    #downloads_requests = DownloadRequest.objects.all()
    class Pid(object):
        pass
    
    pid1 = Pid()
    pid1.pid = 123
    pid1.status = 'Inativo'
    pid1.name = 'Upload de arquivos'
    pid1.created_at = datetime.now()
    
    pid2 = Pid()
    pid2.pid = 183
    pid2.status = 'Ativo'
    pid2.name = u'Cópia de Segurança'
    pid2.created_at = datetime.now()
    
    pid_requests = [pid1, pid2]

    if 'ajax' in request.POST:
        l = []
        for down in pid_requests:
            d = {}
            d['pk'] = down.pid
            d['fields'] = {}
            d['fields']['pid'] = down.pid
            d['fields']['created_at'] = datetime.strftime(down.created_at, "%d/%m/%Y %H:%M")
            d['fields']['name'] = down.name
            d['fields']['status'] = down.status
            l.append(d)
        # response = serializers.serialize("json", downloads_requests)
        response = simplejson.dumps(l)
        return HttpResponse(response, mimetype="text/plain")

    return render_to_response( request, 
                               "pid_history.html", 
                               {"object_list": pid_requests,
                                "list_type": "Downloads",
                                "title": u"Processos"})