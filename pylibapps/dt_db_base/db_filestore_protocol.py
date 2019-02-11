import os
import time
import shutil
import paramiko
import hashlib
import smbc
from shutil import copyfile


def get_hash_folders(filename):
    hash_md5 = hashlib.md5()
    hash_md5.update(filename)
    h = hash_md5.hexdigest()
    return [ h[n:n+2] for n in range(0, 8, 2) ]


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


class sftp_connection(object):
    def __init__(self, file_store_host):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(file_store_host)
        self.ssh = ssh
        self.sftp_con = ssh.open_sftp()

    def put(self, filepath, remote_file):
        self.sftp_con.put(filepath, remote_file)

    def get(self, remote_file, filepath):
        self.sftp_con.get(remote_file, filepath)

    def exists(self, path):
        try:
            self.sftp_con.stat(path)
            return True
        except:
            return False

    def mkdir(self, path):
        self.sftp_con.mkdir(path)


class local_connection(object):

    def put(self, filepath, remote_file):
        shutil.copy(filepath, remote_file)

    def get(self, remote_file, filepath):
        shutil.copy(remote_file, filepath)

    def exists(self, path):
        return os.path.exists(path)

    def mkdir(self, path):
        os.mkdir(path)


class sftp_transferer(object):
    protocol_id=1
    def __init__(self):
        self._con = None
        self._base_folder = None
        self._cache_con = {}

    def open(self, file_store_host, file_store_folder):
        cache_key = (file_store_host, file_store_folder)
        cache_entry = self._cache_con.get(cache_key, None)

        if cache_entry:
            now = time.time()
            if cache_entry[1] - now < 60 * 5:
                cache_entry[1] = now
                self._con = cache_entry[0]
                self._base_folder = file_store_folder
                return
            else:
                self._cache_con.pop(cache_key)

        self._base_folder = file_store_folder

        if file_store_host.lower() == "localhost":
            self._con = local_connection()
        else:
            self._con = sftp_connection(file_store_host)
        self._cache_con[cache_key] = [self._con, time.time()]

    def _get_remote_name(self, filepath, file_id, upload=False):
        filename = os.path.basename(filepath)
        remote_filename = "%i.%s" % (file_id, filename)
        folders = get_hash_folders(remote_filename)
        path = self._base_folder
        for folder in folders:
            path = os.path.join(path, folder)
            if not self._con.exists(path):
                if upload:
                    self._con.mkdir(path)
        remote_filepath = os.path.join(path, remote_filename)
        return remote_filepath

    def clean(self):
        pass

    def upload(self, filepath, file_id):
        remote_filepath = self._get_remote_name(filepath, file_id, True)
        shutil.copy(filepath, remote_filepath)
        self._con.put(filepath, remote_filepath)
        print "upload", remote_filepath

    def download(self, filepath, file_id, mod_time):
        # Look flat first
        filename = os.path.basename(filepath)
        remote_filepath = os.path.join(self._base_folder, "%i.%s" % (file_id, filename))
        if not self._con.exists(remote_filepath):
            print "No", remote_filepath
            remote_filepath = self._get_remote_name(filepath, file_id)
        else:
            print "found", remote_filepath
        self._con.get(remote_filepath, filepath)
        os.utime(filepath, (mod_time, mod_time))
