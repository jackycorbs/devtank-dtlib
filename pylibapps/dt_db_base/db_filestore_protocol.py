import os
import time
import shutil
import paramiko
import smbc
from shutil import copyfile


class smb_transferer(object):
    protocol_id=2
    def __init__(self):
        print "Using smbc for smb transfer"
        self._ctx = None
        self._host = None
        self._base_folder = None
        self._cache_con = {}

    def _get_smb_username(self):
        return None

    def _get_smb_password(self):
        return None

    def _get_smb_domain(self):
        return None

    def _do_auth(self, svr, shr, wg, un, pw):
        r = (self._get_smb_domain(),
                self._get_smb_username(),
                self._get_smb_password())
        return r

    def open(self, file_store_host, file_store_folder):
        cache_key = (file_store_host, file_store_folder)
        cache_entry = self._cache_con.get(cache_key, None)

        if cache_entry:
            now = time.time()
            if cache_entry[1] - now < 60 * 5:
                cache_entry[1] = now
                self._ctx = cache_entry[0]
                self._host = file_store_host
                self._base_folder = file_store_folder
                return
            else:
                self._cache_con.pop(cache_key)

        self._ctx = smbc.Context(auth_fn=self._do_auth)
        self._host = file_store_host
        self._base_folder = file_store_folder

        self._cache_con[cache_key] = [self._ctx, time.time()]

    def clean(self):
        self._ctx = None
        self._host = None
        self._base_folder = None
        self._cache_con = {}

    def _safe_name(self, filename):
        filename = "".join(
            map(lambda x: "_" if x in ':*/\?<>"|' else x, filename))
        return urllib.pathname2url(filename) # Spaces are safe like this

    def upload(self, filepath, file_id):
        filename = os.path.basename(filepath)
        remote_uri = "smb://%s/%s/%i.%s" % (self._host,
                                            self._base_folder,
                                            file_id,
                                            self._safe_name(filename))
        f = self._ctx.open(remote_uri, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0644)

        with open(filepath) as f2:
            shutil.copyfileobj(f2, f)

    def download(self, filepath, file_id, mod_time):
        filename = os.path.basename(filepath)
        remote_uri = "smb://%s/%s/%i.%s" % (self._host,
                                            self._base_folder,
                                            file_id,
                                            self._safe_name(filename))
        f = self._ctx.open(remote_uri, os.O_RDONLY)

        with open(filepath, "w") as f2:
            shutil.copyfileobj(f, f2)

        os.utime(filepath, (mod_time, mod_time))



class _localsftp(object):
    def put(self, filepath, remote_file):
        shutil.copy(filepath, remote_file)

    def get(self, remote_file, filepath):
        shutil.copy(remote_file, filepath)


class sftp_transferer(object):
    protocol_id=1
    def __init__(self):
        self._ssh = None
        self._sftp = None
        self._base_folder = None
        self._cache_con = {}

    def open(self, file_store_host, file_store_folder):
        cache_key = (file_store_host, file_store_folder)
        cache_entry = self._cache_con.get(cache_key, None)

        if cache_entry:
            now = time.time()
            if cache_entry[2] - now < 60 * 5:
                cache_entry[2] = now
                self._ssh = cache_entry[0]
                self._sftp = cache_entry[1]
                self._base_folder = file_store_folder
                return
            else:
                self._cache_con.pop(cache_key)

        self._base_folder = file_store_folder

        if file_store_host.lower() == "localhost":
            self._ssh = None
            self._sftp = _localsftp()
        else:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(file_store_host)
            self._ssh = ssh
            self._sftp = ssh.open_sftp()
        self._cache_con[cache_key] = [self._ssh, self._sftp, time.time()]

    def clean(self):
        pass

    def upload(self, filepath, file_id):
        filename = os.path.basename(filepath)
        remote_file = os.path.join(self._base_folder, "%i.%s" % (file_id, filename))
        self._sftp.put(filepath, remote_file)

    def download(self, filepath, file_id, mod_time):
        filename = os.path.basename(filepath)
        remote_file = os.path.join(self._base_folder,
                                   "%i.%s" % (file_id, filename))
        self._sftp.get(remote_file, filepath)
        os.utime(filepath, (mod_time, mod_time))
