#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
from backup_corporativo.bkp import utils
from backup_corporativo.bkp.network_utils import NetworkInfo
from backup_corporativo.bkp.bacula import Bacula
from backup_corporativo.bkp.models import *


### Constants ###
DAYS_OF_THE_WEEK = (
    'sunday','monday','tuesday',
    'wednesday','thursday','friday',
    'saturday',
)


###
###   Main Definitions
###



def create_pools(sender, instance, signal, *args, **kwargs):
    """create associated pools to the procedure."""
    if 'created' in kwargs:
        if kwargs['created']:   # instance was just created
            fpool = Pool(procedure=instance)
            fpool.save()

def update_files(sender, instance, signal, *args, **kwargs):
    """entry point for update files"""
    from backup_corporativo.bkp.bacula import Bacula
    
    if sender == FileSet:
        update_fileset_file(instance.procedure)
    elif sender == Computer:
        update_computer_file(instance)
    elif sender == Procedure:
        update_procedure_file(instance)
        update_fileset_file(instance)
        update_schedule_file(instance)        
    elif sender == Pool:
        update_pool_file(instance.procedure)
    elif sender == Schedule:
        update_schedule_file(instance.procedure)
    elif sender == WeeklyTrigger:
        update_schedule_file(instance.schedule.procedure)
    elif sender == MonthlyTrigger:
        update_schedule_file(instance.schedule.procedure)
    elif sender == Storage:
        update_storage_file(instance)
    elif sender == NetworkInterface:
        from backup_corporativo.settings import DEBUG
        if DEBUG:
            pass
        else: 
        	update_iftab_file(instance)
        	update_interfaces_file(instance)
        	update_dns_file(instance)
    elif sender == GlobalConfig:
        update_config_file(instance)
        update_device_file(instance)     
        update_console_file(instance)
        update_offsite_file(instance)
    else:
        raise # Oops!
    #Bacula.reload()

def remove_files(sender, instance, signal, *args, **kwargs):
    """entry point for remove files"""
    if sender == Computer:
        remove_computer_file(instance)
    elif sender == Procedure:
        remove_procedure_file(instance)
        remove_fileset_file(instance)
        remove_schedule_file(instance)
    elif sender == Pool:
        remove_pool_file(instance.procedure)
    elif sender == Storage:
        remove_storage_file(instance)
    elif sender == Schedule:
        pass
    else:
        raise # Oops!
    Bacula.reload()


### NetworkInterface ###
def update_iftab_file(instance):
	from SOAPpy import SOAPProxy
	server = SOAPProxy("http://127.0.0.1:8888")
	server.generate_iftab(instance.interface_name,instance.interface_mac)

def update_interfaces_file(instance):
	from SOAPpy import SOAPProxy
	server = SOAPProxy("http://127.0.0.1:8888")
	server.generate_interfaces(instance.interface_name, instance.interface_address, instance.interface_netmask, instance.interface_broadcast, instance.interface_network, instance.interface_gateway)

	
def update_dns_file(instance):
	from SOAPpy import SOAPProxy
	server = SOAPProxy("http://127.0.0.1:8888")
	server.generate_dns(instance.interface_dns1, instance.interface_dns2)
	
### Global Config ###

def update_config_file(gconf):
    """Config update file"""
    dir_dict = config_dir_dict(gconf.director_bacula_name(), gconf.director_port, gconf.director_password)
    sto_list = []
    for sto in Storage.objects.all():
        sto_list.append(config_sto_dict(sto.storage_bacula_name(), sto.storage_ip, sto.storage_port, sto.storage_password))
    cat_dict = config_cat_dict("MyCatalog",gconf.bacula_database_name(), gconf.bacula_database_user(), gconf.bacula_database_password())
    smsg_dict = config_msg_dict("Standard",gconf.admin_mail())
    dmsg_dict = config_msg_dict("Daemon",gconf.admin_mail())    
    generate_config("bacula-dir.conf", dir_dict, sto_list, cat_dict, smsg_dict, dmsg_dict)

def config_dir_dict(dir_name, dir_port, dir_passwd):
    """generate config director attributes dict"""
    
    return {'Name':dir_name, 'DIRport':dir_port, 'QueryFile':'"/etc/bacula/query.sql"', 
    'WorkingDirectory':'"/var/bacula/working"','PidDirectory':'"/var/run"','Maximum Concurrent Jobs':'1',
    'Password':'"%s"' % dir_passwd, 'Messages':'Daemon' }

def config_sto_dict(name, ip, port, password):
    """generate config storage attributes dict"""
    
    return {'Name':name, 'Address':ip,'SDPort':port, 'Password':'"%s"' % password,
    'Device':'FileStorage','Media Type':'File'}

def config_cat_dict(cat_name, db_name, db_user, db_passwd):
    """generate config storage attributes dict"""
    
    return {'Name':cat_name, 'dbname':'"%s"' % db_name, 'dbuser':'"%s"' % db_user, 'dbpassword':'"%s"' % db_passwd}
    
def config_msg_dict(msg_name, admin_mail=None):
    """generate config message attributes dict"""
    admin_mail = admin_mail or "nimbus@linconet.com.br"
    if msg_name == 'Standard':
        return {'Name':msg_name, 
        'mailcommand':'"/sbin/bsmtp -h localhost -f \\"\(Bacula\) \<%r\>\\" -s \\"Bacula: %t %e of %c %l\\" %r"', 
        'operatorcommand':'"/sbin/bsmtp -h localhost -f \\"\(Bacula\) \<%r\>\\" -s \\"Bacula: Intervention needed for %j\\" %r"', 
        'mail':'%s = all, !skipped' % admin_mail, 'operator':'%s = mount' % admin_mail,
        'console':'all, !skipped, !saved', 'append':'"/var/bacula/working/log" = all, !skipped'}
    elif msg_name == 'Daemon':
        return {'Name':msg_name, 
        'mailcommand':'"/sbin/bsmtp -h localhost -f \\"\(Bacula\) \<%r\>\\" -s \\"Bacula daemon message\\" %r"',
        'mail':'%s = all, !skipped' % admin_mail, 'console':'all, !skipped, !saved', 
        'append':'"/var/bacula/working/log" = all, !skipped'}


    
def generate_config(filename,dir_dict, sto_list, cat_dict, smsg_dict, dmsg_dict):
    """generate config file"""
    f = utils.prepare_to_write(filename,'custom/config/')

    f.write("Director {\n")
    for k in dir_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':dir_dict[k]})
    f.write("}\n\n")

    # sto_dict is now sto_list.
    for sto in sto_list:
        f.write("Storage {\n")
        for k in sto.keys():
            f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':sto[k]})
        f.write("}\n\n")
    
    f.write("Catalog {\n")
    for k in cat_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':cat_dict[k]})
    f.write("}\n\n")
    
    f.write("Messages {\n")
    for k in smsg_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':smsg_dict[k]})
    f.write("}\n\n")

    f.write("Messages {\n")
    for k in dmsg_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':dmsg_dict[k]})
    f.write("}\n\n")
    
    folders = ['computers','filesets','jobs','pools','schedules']
    for folder in folders:
        import_dir = utils.absolute_dir_path("custom/%s/" % folder)
        f.write("@|\"sh -c 'for f in %s* ; do echo @${f} ; done'\"\n" % import_dir)

    f.close()

def update_offsite_file(gconf):
    if gconf.offsite_on:
        generate_offsite_file("offsite_job",gconf.offsite_hour)
    else:
        filepath = utils.absolute_file_path("offsite_job",'custom/jobs')
        utils.remove_or_leave(filepath)
        filepath = utils.absolute_file_path('offsite_sched', 'custom/schedules')
        utils.remove_or_leave(filepath)

def generate_offsite_file(filename, offsite_hour):
    f = utils.prepare_to_write(filename, 'custom/jobs')
    def_sto_name = Storage.default_storage().storage_name
    
    proc_dict = procedure_dict("Upload Offsite", False, "empty_client", "empty_fileset", "offsite_schedule", 'empty_pool', def_sto_name, 'Admin', None)
    
    del(proc_dict['Run After Job'])
    
    f.write("Job {\n")
    for k in proc_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':proc_dict[k]})
    f.write('''\tRun After Job = "/var/django/NimbusClient/NimbusClient.py -u"\n''')
    f.write("}\n\n")
    f.close()
    
    f = utils.prepare_to_write('offsite_sched', 'custom/schedules')
    
    f.write("Schedule {\n")
    f.write('''\tName = "%s"\n''' % 'offsite_sched')
    f.write('''\tRun = daily at %s\n''' %  offsite_hour)
    f.write("}\n")
    f.close()
    


### Device ###

def device_sto_dict(sto_name, sto_port):
    """generate device storage attributes dict"""
    
    return {'Name':sto_name, 'SDPort':sto_port, 'WorkingDirectory':'"/var/bacula/working"',
    'Pid Directory':'"/var/run"','Maximum Concurrent Jobs':'20'}

def device_dir_dict(dir_name, dir_passwd):
    """generate device director attributes dict"""
    
    return {'Name':dir_name, 'Password':'"%s"' % dir_passwd}

def device_dev_dict(dev_name):
    """generate device device attributes dict"""
    
    return {'Name':dev_name, 'Media Type':'File', 'Archive Device':'/var/backup', 'LabelMedia':'yes', 
    'Random Access':'yes', 'AutomaticMount':'yes', 'RemovableMedia':'no', 'AlwaysOpen':'no'}


def device_msg_dict(msg_name, dir_name):
    """generate device message attributes dict"""
    
    return {'Name':msg_name, 'Director':'%s = all' % dir_name}

    
def update_device_file(gconf):
    """Update Device File"""
    def_sto = Storage.default_storage()
    sto_dict = device_sto_dict(def_sto.storage_name, def_sto.storage_port)
    dir_dict = device_dir_dict(gconf.director_bacula_name(),def_sto.storage_password)
    dev_dict = device_dev_dict("FileStorage")
    msg_dict = device_msg_dict("Standard","%s" % gconf.director_bacula_name())
    generate_device("bacula-sd.conf", sto_dict, dir_dict, dev_dict, msg_dict)

def generate_device(filename,sto_dict, dir_dict, dev_dict, msg_dict):
    """generate config file"""
    f = utils.prepare_to_write(filename,'custom/config/')

    f.write("Storage {\n")
    for k in sto_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':sto_dict[k]})
    f.write("}\n\n")

    f.write("Director {\n")
    for k in dir_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':dir_dict[k]})
    f.write("}\n\n")
    
    f.write("Device {\n")
    for k in dev_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':dev_dict[k]})
    f.write("}\n\n")
    
    f.write("Messages {\n")
    for k in msg_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':msg_dict[k]})
    f.write("}\n\n")
    f.close()

### Console ###

def console_dir_dict(dir_name, dir_port, dir_passwd):
    """generate device message attributes dict"""
    
    return {'Name':dir_name, 'DIRPort':dir_port, 'Address':'127.0.0.1', 'Password':'"%s"' % dir_passwd}


def update_console_file(gconf):
    """Update Console File"""
    dir_dict = console_dir_dict("%s" % gconf.director_bacula_name(), gconf.director_port, gconf.director_password)
    generate_console("bconsole.conf", dir_dict)
    

def generate_console(filename,dir_dict):
    """generate console file"""
    f = utils.prepare_to_write(filename,'custom/config/')

    f.write("Director {\n")
    for k in dir_dict.keys():
        f.write('''\t%(key)s = %(value)s\n''' % {'key':k,'value':dir_dict[k]})
    f.write("}\n\n")


    
#### Procedure #####

def update_procedure_file(proc):
    """Procedure update file"""
    proc_name = proc.procedure_bacula_name()
    proc_offsite = proc.offsite_on
    restore_name = proc.restore_bacula_name()
    fset_name = proc.fileset_bacula_name()
    sched_name = proc.schedule_bacula_name()
    pool_name = proc.pool_bacula_name()
    comp_name = proc.computer.computer_bacula_name()
    sto_name = proc.storage.storage_bacula_name()
    jdict = procedure_dict(proc_name, proc_offsite, comp_name, fset_name, sched_name, pool_name, sto_name, type='Backup')
    generate_procedure(proc_name,jdict)

    
def procedure_dict(proc_name, proc_offsite, comp_name, fset_name, sched_name, pool_name, sto_name, type='Backup', where=None):
    """generate procedure attributes dict"""
    bootstrap = '/var/lib/bacula/%s.bsr' % (proc_name)
    run_after_job = proc_offsite and "/var/django/NimbusClient/NimbusClient.py -m %v" or None

    return  {'Name':proc_name, 'Client':comp_name, 'Level':'Incremental','FileSet':fset_name,
            'Schedule':sched_name, 'Storage':sto_name, 'Pool':pool_name,'Write Bootstrap':bootstrap,
            'Priority':'10', 'Messages':'Standard','Type':type,'Where':where, 'Run After Job':run_after_job,
            }

def generate_procedure(proc_name,attr_dict):
    """generate procedure file"""
    f = utils.prepare_to_write(proc_name,'custom/jobs')

    f.write("Job {\n")
    if attr_dict['Run After Job'] is None:
        del(attr_dict['Run After Job'])
    if attr_dict['Type'] == 'Backup':
        f.write('''\tWrite Bootstrap = "%s"\n''' % (attr_dict['Write Bootstrap']))
    elif attr_dict['Type'] == 'Restore':
        f.write('''\tWhere = "%s"\n''' % (attr_dict['Where']))
        del(attr_dict['Schedule'])
        del(attr_dict['Level'])    
    del(attr_dict['Where'])
    for k in attr_dict.keys():
        f.write('''\t%(key)s = "%(value)s"\n''' % {'key':k,'value':attr_dict[k]})
    f.write("}\n")
    f.close()

def remove_procedure_file(proc):
    """remove procedure file"""
    base_dir,filepath = utils.mount_path(proc.procedure_bacula_name(),'custom/jobs')
    utils.remove_or_leave(filepath)
    
#### Computer #####

def update_computer_file(comp):
    """Computer update file"""
    cdict = computer_dict(comp.computer_bacula_name(),comp.computer_ip,comp.computer_password)
    generate_computer_file(comp.computer_bacula_name(),cdict)

def computer_dict(name,ip,password):
    """generate computer attributes dict"""
    return {'Name':name, 'Address':ip, 'FDPort':'9102', 'Catalog':'MyCatalog',
    'password':password, 'AutoPrune':'yes'}

def generate_computer_file(name,attr_dict):
    """Computer generate file"""
    f = utils.prepare_to_write(name,'custom/computers')

    f.write("Client {\n")
    for k in attr_dict.keys():
        f.write('''\t%(key)s = "%(value)s"\n''' % {'key':k,'value':attr_dict[k]})
    f.write("}\n")
    f.close()

def remove_computer_file(comp):
    """Computer remove file"""
    base_dir,filepath = utils.mount_path(comp.computer_bacula_name(),'custom/computers')
    utils.remove_or_leave(filepath)
    
#### FileSet #####


def update_fileset_file(proc):
    """FileSet update filesets to a procedure instance"""
    fsets = proc.fileset_set.all()
    fset_name = proc.fileset_bacula_name()
    farray = generate_file_array(fsets)
    generate_fileset_file(fset_name,farray)

def generate_file_array(fsets):
    """generate file_array"""
    array = []
    for fset in fsets:
        array.append(fset.path)
    return array
    
def generate_fileset_file(name,file_array):
    """FileSet generate file"""
    f = utils.prepare_to_write(name,'custom/filesets')

    f.write("FileSet {\n")
    f.write('''\tName = "%s"\n''' % (name))
    f.write("\tInclude {\n")
    f.write("\t\tOptions{\n")
    f.write('''\t\t\tsignature = "MD5"\n''')
    f.write('''\t\t\tcompression = "GZIP"\n''')
    f.write("\t\t}\n")
    for k in file_array:
        f.write('''\t\tFile = "%s"\n''' % (k))
    f.write("\t}\n")
    f.write("}\n")
    f.close()

def remove_fileset_file(proc):
    """remove FileSet file"""
    name = proc.fileset_bacula_name()
    base_dir,filepath = utils.mount_path(name,'custom/filesets')
    utils.remove_or_leave(filepath)    

#### Pool #####

def update_pool_file(proc):
    """Pool update pool bacula file""" 
    pool_name = proc.pool_bacula_name()
    pdict = pool_dict(pool_name)
    generate_pool(pool_name,pdict)


def pool_dict(pool_name):
    """Generate pool attributes dict"""
    format = '%s-vol-' % (pool_name)
    return {'Name':pool_name, 'Pool Type':'Backup', 'Recycle':'yes', 'AutoPrune':'yes', 
    'Volume Retention':'31 days','Purge Oldest Volume':'yes','Maximum Volume Bytes':'1048576',
    'Recycle Oldest Volume':'yes','Label Format':format}

def generate_pool(name,attr_dict):        
    """generate pool bacula file"""
    f = utils.prepare_to_write(name,'custom/pools')
    
    f.write("Pool {\n")
    f.write("\tMaximum Volume Bytes = %s\n" % (attr_dict['Maximum Volume Bytes']))
    f.write("\tVolume Retention = %s\n" % (attr_dict['Volume Retention']))    
    del(attr_dict['Maximum Volume Bytes'])
    del(attr_dict['Volume Retention'])
    for k in attr_dict.keys():
        f.write('''\t%(key)s = "%(value)s"\n''' % {'key':k,'value':attr_dict[k]})
    f.write("}\n")
    f.close()

def remove_pool_file(proc):
    """pool remove file"""
    base_dir,filepath = utils.mount_path(proc.pool_bacula_name(),'custom/pools')
    utils.remove_or_leave(filepath)

### Schedule ###
# TODO: Otimizar codigo, remover if do schedule type (programaçao dinamica)
def run_dict(schedules_list):
    """build a dict with bacula run specification"""
    dict = {}
    for sched in schedules_list:
        trigg = sched.get_trigger()
        if trigg:
            if sched.type == 'Weekly':
                days = []
                for day in DAYS_OF_THE_WEEK:
                    if getattr(trigg, day, None):
                        key = "%s at %s" % (day,str(trigg.hour.strftime("%H:%M")))
                        dict[key] = trigg.level
            elif sched.type == 'Monthly':
                days = trigg.target_days.split(';')
                for day in days:
                    key = "monthly %s at %s" % (day,str(trigg.hour.strftime("%H:%M")))
                    dict[key] = trigg.level
        else:
            pass
    return dict


def update_schedule_file(proc):
    sched_name = proc.schedule_bacula_name()
    scheds = proc.schedule_set.all()
    rdict = run_dict(scheds)
    generate_schedule(sched_name,rdict)

def generate_schedule(schedule_name,run_dict):        
    f = utils.prepare_to_write(schedule_name,'custom/schedules')

    f.write("Schedule {\n")
    f.write('''\tName = "%s"\n''' % (schedule_name))
    for k in run_dict.keys():
        f.write('''\tRun = %(level)s %(date)s\n''' % {'date':k,'level':run_dict[k]})    
    f.write("}\n")
    f.close()

def remove_schedule_file(proc):
    base_dir,filepath = utils.mount_path(proc.schedule_bacula_name(),'custom/schedules')
    utils.remove_or_leave(filepath)
    


#### Storage #####
def update_storage_file(sto):
    """Storage update file."""
    sdict = storage_dict(sto.storage_bacula_name(),
                         sto.storage_ip,
                         sto.storage_port,
                         sto.storage_password)
    generate_storage_file(sto.storage_bacula_name(), sdict)

def storage_dict(name, ip, port, password):
    """Generate Storage attributes dict."""
    return {'Name': name, 'SDPort': port,
            'WorkingDirectory': '/var/lib/bacula',
            'Pid Directory': '/var/run',
            'Maximum Concurrent Jobs': 20}

def generate_storage_file(name, attr_dict):
    """Generate Storage file"""
    f = utils.prepare_to_write(name, 'custom/storages')

    f.write("Storage {\n")
    for k in attr_dict.keys():
        f.write('''\t%(key)s = "%(value)s"\n''' % {'key':k, 'value':attr_dict[k]})
    f.write("}\n")
    f.close()

def remove_storage_file(sto):
    """Remove Storage file"""
    base_dir,filepath = utils.mount_path(sto.storage_bacula_name(), 'custom/storages')
    utils.remove_or_leave(filepath)

   
###
###   Dispatcher Connection
###

#NetworkConfig
models.signals.post_save.connect(update_files, sender=NetworkInterface)
# GlobalConfig
models.signals.post_save.connect(update_files, sender=GlobalConfig)
# Computer
models.signals.post_save.connect(update_files, sender=Computer)
models.signals.post_delete.connect(remove_files, sender=Computer)
# Procedure    
models.signals.post_save.connect(create_pools, sender=Procedure)
models.signals.post_save.connect(update_files, sender=Procedure)
models.signals.post_delete.connect(remove_files, sender=Procedure)
# FileSet
models.signals.post_save.connect(update_files, sender=FileSet)
models.signals.post_delete.connect(update_files, sender=FileSet)
# Schedule
models.signals.post_save.connect(update_files, sender=Schedule)
models.signals.post_delete.connect(remove_files, sender=Schedule)
# Pool
models.signals.post_save.connect(update_files, sender=Pool)
models.signals.post_delete.connect(remove_files, sender=Pool)
# Storage
models.signals.post_save.connect(update_files, sender=Storage)
models.signals.post_delete.connect(remove_files, sender=Storage)
# Trigger
models.signals.post_save.connect(update_files, sender=WeeklyTrigger)
models.signals.post_delete.connect(update_files, sender=WeeklyTrigger)
models.signals.post_save.connect(update_files, sender=MonthlyTrigger)
models.signals.post_delete.connect(update_files, sender=MonthlyTrigger)
