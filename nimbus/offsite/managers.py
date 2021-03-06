#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import bz2
import stat
import time
import logging
import tempfile
import subprocess
from pwd import getpwnam

from datetime import datetime
from os.path import join, exists, isfile, isabs


from django.conf import settings

from nimbus.shared import utils
from nimbus.offsite import utils as outils
from nimbus.procedures.models import Procedure
from nimbus.storages.models import Device
from nimbus.offsite.models import Offsite
from nimbus.offsite.models import (Volume,
                                   UploadRequest,
                                   RemoteUploadRequest,
                                   LocalUploadRequest,
                                   DownloadRequest,
                                   UploadTransferredData,
                                   DownloadTransferredData,
                                   DeleteRequest)





NIMBUS_DUMP = "/var/nimbus/nimbus-sql.bz2"
BACULA_DUMP = "/var/nimbus/bacula-sql.bz2"


def _compress_file(src, dst):
    with file(src) as src_file:
        try:
            bzipped = bz2.BZ2File(dst, compresslevel=9, mode="wb")
            for line in src_file:
                bzipped.write(line)
        finally:
            bzipped.close()



def _generate_db_dump(db_name, dest):
    env = os.environ.copy()
    db_data = settings.DATABASES[db_name]
    tmp_filename = tempfile.mktemp()
    env['PGPASSWORD'] = db_data['PASSWORD']
    cmd = subprocess.Popen(["/usr/lib/postgresql/8.4/bin/pg_dump",
                            db_data['NAME'],
                            "-U",db_data['USER'],
                            "-f",tmp_filename,
                            "-h",db_data['HOST']],
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            env=env)
    stdout, stderr = cmd.communicate()
    if cmd.returncode != 0:
        logger = logging.getLogger('dump data base')
        logger.error(stdout)
        logger.error(stderr)
    _compress_file(tmp_filename, dest)


def _generate_nimbus_dump():
    return _generate_db_dump('default',NIMBUS_DUMP)

def _generate_bacula_dump():
    return _generate_db_dump('bacula',BACULA_DUMP)



def find_archive_devices():
    archives = [dev.archive for dev in Device.objects.all() if dev.is_local]
    return archives

def get_volume_abspath(volume, archives):
    for archive in archives:
        abspath = join(archive, volume)
        if exists(abspath) and isfile(abspath):
            return abspath

def get_volumes_abspath(volumes):
    archives = find_archive_devices()
    return [get_volume_abspath(volume, archives) for volume in volumes]

def get_all_bacula_volumes():
    archives = find_archive_devices()
    volumes = []
    for arc in archives:
        files = os.listdir(arc)
        for filename in files:
            fullpath = join(arc, filename)
            if isfile(fullpath):
                volumes.append(fullpath)
    return volumes

def register_transferred_data(request, initialbytes):
    bytes = request.transferred_bytes - initialbytes
    if isinstance(request, (RemoteUploadRequest, LocalUploadRequest)):
        UploadTransferredData.objects.create(bytes=bytes)
    else:
        DownloadTransferredData.objects.create(bytes=bytes)

def filename_is_volumename(filename):
    parts = filename.split("_")
    if len(parts) == 1:
        return False
    procedure_name = parts[0]
    try:
        procedure = Procedure.objects.get(uuid__uuid_hex=procedure_name)
        name = procedure.uuid.uuid_hex + "_procedure_pool-vol-"
        return filename.startswith(name)
    except Procedure.DoesNotExist, error:
        return False


class File(object):

    def __init__(self, filename, mode, callback):
        self.fileobj = file(filename, mode)
        self.callback = callback
        self.filesize = os.path.getsize(filename)
        self.read_bytes = 0
        self.written_bytes = 0


    def read(self, size):
        r =  self.fileobj.read(size)
        self.read_bytes += size
        self.progress_upload( )
        return r

    def write(self, content):
        size = len(content)
        r = self.fileobj.write(content)
        self.written_bytes += size
        self.progress_download( )
        return r

    def progress_download(self):
        if self.callback:
            self.callback( self.written_bytes, self.filesize )


    def progress_upload(self):
        if self.callback:
            self.callback( self.read_bytes, self.filesize )

    def close(self):
        self.fileobj.close()



class BaseManager(object):

    UploadRequestClass = RemoteUploadRequest
    DownloadRequestClass = DownloadRequest

    def get_volume(self, volume_path):
        volume, created = Volume.objects.get_or_create(path=volume_path)
        return volume

    def get_volumes(self, volumes_path=None):
        if volumes_path:
            for path in volumes_path:
                self.get_volume(path)
        return Volume.objects.all()

    def create_upload_request(self, volume_path ):
        volume = self.get_volume(volume_path=volume_path)
        request, created = self.UploadRequestClass\
                            .objects.get_or_create(volume=volume)
        return request

    def create_download_request(self, volume_path):
        volume = self.get_volume(volume_path=volume_path)
        request, created = self.DownloadRequestClass\
                            .objects.get_or_create(volume=volume)
        return request

    def get_upload_requests(self):
        return self.UploadRequestClass.objects.all().order_by('-created_at')

    def get_download_requests(self):
        return self.DownloadRequestClass.objects.all()

    def upload_all_volumes(self):
        volumes = get_all_bacula_volumes()
        self.upload_volumes(volumes)

    def upload_volumes(self, volumes):
        volumes = get_volumes_abspath(volumes)
        for vol in volumes:
            self.create_upload_request(vol)
        self.generate_database_dump_upload_request()
        self.process_pending_upload_requests()

    def generate_database_dump_upload_request(self):
        _generate_nimbus_dump()
        _generate_bacula_dump()
        if exists(NIMBUS_DUMP):
            self.create_upload_request(NIMBUS_DUMP)
        if exists(BACULA_DUMP):
            self.create_upload_request(BACULA_DUMP)

    def download_all_volumes(self):
        volumes = self.get_remote_volumes_list()
        self.download_volumes(volumes)

    def download_volumes(self, volumes):
        for vol in volumes:
            self.create_download_request(vol)
        self.process_pending_download_requests()

    def create_delete_request(self, volume_path ):
        volume = self.get_volume(volume_path=volume_path)
        request, created = DeleteRequest\
                            .objects.get_or_create(volume=volume)
        return request

    def create_deletes_request(self, volumes):
        for volume in volumes:
            self.create_delete_request(volume)


    def download_volume(self, volume):
        raise AttributeError("method not implemented")

    def upload_volume(self, volume):
        raise AttributeError("method not implemented")

    def delete_volume(self, volume):
        raise AttributeError("method not implemented")

    def delete_volumes(self, volumes):
        for volume in volumes:
            self.delete_volume(volume)

    def process_pending_delete_requests(self):
        for delete_request in DeleteRequest.objects.all():
            self.delete_volume(delete_request.volume.path)

    def finish(self):
        # WTF
        pass




def process_request(request, process_function, max_retry=3):
    logger = logging.getLogger(__name__)
    request.last_attempt = datetime.now()
    retry = 0
    while True:
        try:
            request.attempts += 1
            request.last_update = time.time()

            if isinstance(request, UploadRequest): # no resume
                request.reset_transferred_bytes()

            initialbytes = request.transferred_bytes
            request.save()
            process_function(request.volume.path, request.volume.filename,
                             callback=request.update, userdata=request)
            request.finish()
            logger.info("%s processado com sucesso" % request)
            break
        except IOError, e:
            retry += 1
            register_transferred_data(request, initialbytes)
            if retry >= max_retry:
                logger.error("Erro ao processar %s" % request)
                raise
            logger.error("Erro ao processar %s. Tentando novamente..." % request)




class RemoteManager(BaseManager):

    MAX_RETRY = 3

    def __init__(self):
        self.s3 = Offsite.get_s3_interface()


    def process_pending_upload_requests(self):
        requests = self.get_upload_requests()
        self.process_requests(requests, self._upload_file)


    def get_remote_volumes_list(self):
        return [ f.name for f in self.get_remote_volumes() ]

    def get_remote_volumes(self):
        return [ f for f in self.s3.list_files() if filename_is_volumename(f.name) ]

    def _upload_file(self, filename, dest, callback=None, userdata=None):
        self.s3.multipart_status_callbacks.add_callback( userdata.increment_part )
        self.s3.upload_file(filename, dest, part=userdata.part, callback=callback)
        self.s3.multipart_status_callbacks.remove_callback( userdata.increment_part )


    def upload_volume(self, request):
        process_request(request, self._upload_file, self.MAX_RETRY)


    def download_volume(self, request):
        process_request(request, self._download_file, self.MAX_RETRY)


    def _download_file(self, filename, dest, callback=None, userdata=None):

        if isabs(filename):
            destfilename = filename
        else:
            destfilename = join(settings.NIMBUS_DEFAULT_ARCHIVE, filename)

        self.s3.download_file( filename, destfilename, callback=callback)

        os.chmod( destfilename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
        os.chown( destfilename, getpwnam("nimbus").pw_uid, getpwnam("bacula").pw_gid)


    def process_pending_download_requests(self):
        requests = self.get_download_requests()
        self.process_requests( requests, self._download_file,
                               self.MAX_RETRY)


    def process_requests(self, requests, process_function, ratelimit=None):

        for request in requests:
            process_request(request, process_function, self.MAX_RETRY)


    def delete_volume(self, volume):
        self.s3.delete_file(volume)
        DeleteRequest.objects.filter(volume__path=volume).delete()



class LocalManager(BaseManager):
    SIZE_512KB = 512 * 1024
    UploadRequestClass = LocalUploadRequest

    def __init__(self, device_manager, destination):
        self.device_manager = device_manager
        self.origin = self.device_manager.mountpoint
        self.destination = destination

    def create_download_request(self, volume_path):
        volume_path = join(self.origin, volume_path)
        return super(LocalManager, self).create_download_request(volume_path)

    def get_remote_volumes_list(self):
        allfiles = os.listdir(self.origin)
        volume_files = [f for f in allfiles if filename_is_volumename(f)]
        files = [join(self.origin, f) for f in volume_files]
        return filter(os.path.isfile, files)

    def process_pending_upload_requests(self):
        requests = self.get_upload_requests()
        self.process_requests(requests)

    def process_pending_download_requests(self):
        requests = self.get_download_requests()
        self.process_requests(requests)

    def process_requests(self, requests):
        for req in requests:
            self._process_request(req)


    def _process_request(self, request):
        logger = logging.getLogger(__name__)
        request.last_attempt = datetime.now()
        request.attempts += 1
        request.save()
        try:
            self._copy( request.volume.path, join(self.destination,
                                              request.volume.filename),
                                              request.update)
            request.finish()
            logger.info("%s processado com sucesso" % request)
        except Exception, e:
            logger.exception("Erro ao processar %s" % request)


    def upload_volume(self, request):
        self._process_request(request)


    def download_volume(self, request):
        self._process_request(request)



    def _copy(self, origin, destination, callback):
        ori = File(origin, "rb", callback)
        dest = file(destination, "wb")
        while True:
            data = ori.read(self.SIZE_512KB)
            if not data:
                break
            dest.write(data)
        
        ori.close()
        dest.close()

        try:
            os.chmod(destination, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
            os.chown(destination, getpwnam("nimbus").pw_uid, getpwnam("bacula").pw_gid)
        except (OSError, IOError), error:
            pass #FIX

        if outils.md5_for_large_file(destination) != outils.md5_for_large_file(origin):
            raise outils.Md5CheckError("md5 mismatch")

    def finish(self):
        self.device_manager.umount()



def check_integrity():
    s3 = Offsite.get_s3_interface()
    offsite_keys = s3.list_files()

    for key in offsite_keys:
        filename = key.name
        filename_on_disk = os.path.join(settings.NIMBUS_DEFAULT_ARCHIVE,
                                        filename)
        if os.path.exists(filename_on_disk):
            print "Checking",filename,"...",
            s3_md5 = key.metadata.get('nimbus-md5', None)
            local_md5 = outils.md5_for_large_file(filename_on_disk)

            is_ok = True
            if s3_md5:
                if s3_md5 != local_md5:
                    is_ok = False
            else:
                if not '-' in key.etag:
                    s3_md5 = key.etag.strip('"\'')
                    if local_md5 != s3_md5:
                        is_ok = False
                else:
                    size = os.path.getsize(filename_on_disk)
                    if size != key.size:
                        is_ok = False

            if is_ok:
                print "Ok"
            else:
                print "Error"
                f = utils.filesizeformat
                size = os.path.getsize(filename_on_disk)
                print "Local file size: {0}. Remote file size: {1}".format(f(size), f(f.size))
                print "Local file md5: {0}. Remote file md5: {1}".format(local_md5, s3_md5)
