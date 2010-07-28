#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from os import path

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete


from nimbus.base.models import BaseModel
from nimbus.shared import utils, enums, signals
from nimbus.libs.template import render_to_file


OS = ( (os,os) for os in enums.operating_systems)


class ComputerLimitExceeded(Exception):
    pass

class UnableToGetFile(Exception):
    pass

class InvalidFileType(Exception):
    pass


class Computer(BaseModel):

    name = models.CharField( max_length=255, unique=True, 
                             blank=False, null=False)
    address = models.IPAddressField(blank=False, null=False)
    operation_system = models.CharField( max_length=255,
                                         blank=False, null=False,
                                         choices=OS )
    description = models.TextField( max_length=1024, blank=True)
    password = models.CharField( max_length=255,
                                 blank=False, null=False,
                                 editable=False,
                                 default=utils.random_password)



    def _get_crypt_file(self, filename):
        km = KeyManager()
        client_path = km.get_client_path(self.computer_name)
        path = os.path.join(client_path, file_name)
        try:
            file_content = open(file_path, 'r') 
            file_read = file_content.read()
            file_content.close()
            return file_read
        except IOError, e:
            raise UnableToGetFile("Original error was: %s" % e)      


    def get_pem(self):
        return self._get_crypt_file("client.pem")

    def get_config_file(self):
        
        fd_dict =   {
                    'Name': self.computer_bacula_name(),
                    #TODO: tratar porta do cliente
                    'FDport':'9102',
                    'Maximum Concurrent Jobs':'5',}
                    
        if self.computer_encryption:
            if self.computer_so == 'UNIX':
                fd_dict.update({
                    'PKI Signatures':'Yes',
                    'PKI Encryption':'Yes',
                    'PKI Keypair':'''"/etc/bacula/client.pem"''',
                    'PKI Master Key':'''"/etc/bacula/master.cert"''',})
            elif self.computer_so == 'WIN':
                fd_dict.update({
                    'PKI Signatures':'Yes',
                    'PKI Encryption':'Yes',
                    'PKI Keypair':'''"C:\\\\Nimbus\\\\client.pem"''',
                    'PKI Master Key':'''"C:\\\\Nimbus\\\\master.cert"''',})
            
        if self.computer_so == 'UNIX':
            fd_dict.update({
                'WorkingDirectory':'/var/bacula/working ',
                'Pid Directory':'/var/run ',})
        elif self.computer_so == 'WIN':
            fd_dict.update({
                'WorkingDirectory':'''"C:\\\\Nimbus"''',
                'Pid Directory':'''"C:\\\\Nimbus"''',})
        gconf = GlobalConfig.objects.get(pk=1)
        dir_dict =  {
            'Name':gconf.director_bacula_name(),
            'Password':'''"%s"''' % (self.computer_password),}
        msg_dict =  {
            'Name':'Standard',
            'director':'%s = all, !skipped, !restored' % \
                gconf.director_bacula_name(),}
        dump = []
    
        dump.append("#\n")
        # TODO: adicionar version stamp aqui
        dump.append("# Generated by Nimbus %s\n" % \
            time.strftime("%d-%m-%Y %H:%M:%S", time.localtime()))
        dump.append("#\n")
        dump.append("FileDaemon {\n")
        for k in fd_dict.keys():
            dump.append('''\t%(key)s = %(value)s\n''' % {
                'key':k,'value':fd_dict[k]})
        dump.append("}\n\n")
        dump.append("Director {\n")
        for k in dir_dict.keys():
            dump.append('''\t%(key)s = %(value)s\n''' % {
                'key':k,'value':dir_dict[k]})
        dump.append("}\n\n")
        dump.append("Messages {\n")
        for k in msg_dict.keys():
            dump.append('''\t%(key)s = %(value)s\n''' % {
                'key':k,'value':msg_dict[k]})
        dump.append("}\n\n")
        
        return dump

    def successful_jobs(self):
        successful_jobs_query = CLIENT_SUCCESSFUL_JOBS_RAW_QUERY % {
            'client_name':self.computer_bacula_name(),    
        }
        bacula = Bacula()
        successful_jobs_cursor = bacula.baculadb.execute(successful_jobs_query)
        return utils.dictfetch(successful_jobs_cursor)

    def unsuccessful_jobs(self):
        unsuccessful_jobs_query = CLIENT_UNSUCCESSFUL_JOBS_RAW_QUERY % {
            'client_name':self.computer_bacula_name(),    
        }
        bacula = Bacula()
        unsuccessful_jobs_cursor = bacula.baculadb.execute(unsuccessful_jobs_query)
        return utils.dictfetch(unsuccessful_jobs_cursor)

    def running_jobs(self):
        running_jobs_query = CLIENT_RUNNING_JOBS_RAW_QUERY % {
            'client_name':self.computer_bacula_name(),
        }
        bacula = Bacula()
        running_jobs_cursor = bacula.baculadb.execute(running_jobs_query)
        return utils.dictfetch(running_jobs_cursor)

    def last_jobs(self):
        last_jobs_query = CLIENT_LAST_JOBS_RAW_QUERY % {
            'client_name':self.computer_bacula_name(),}
        bacula = Bacula()
        last_jobs_cursor = bacula.baculadb.execute(last_jobs_query)
        return utils.dictfetch(last_jobs_cursor)

    def __unicode__(self):
       return "%s (%s)" % (self.name, self.address)


def update_computer_file(computer):
    """Computer update file"""

    name = computer.bacula_name()


    filename = path.join( settings.NIMBUS_COMPUTERS_PATH, 
                          name)

    render_to_file( filename,
                    "computer",
                    name=name,
                    ip=comp.computer_ip,
                    password=comp.computer_password)



def remove_computer_file(computer):
    """Computer remove file"""

    filename = path.join( settings.NIMBUS_COMPUTERS_PATH, 
                          computer.bacula_name())
    utils.remove_or_leave(filename)



signals.connect_on( update_computer_file, Computer, post_save)
signals.connect_on( remove_computer_file, Computer, post_delete)
