import os
import time
import shutil
import paramiko
from shutil import copyfile

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject

_SMB_AUTO_UMOUNT = 60 * 5 # Seconds until a unused mount is umounted.



class smb_transferer(object):
    protocol_id=2
    def __init__(self):
        self._mounts = {}
        self._mnt_path = None

    def _get_smb_username(self):
        return None

    def _get_smb_password(self):
        return None

    def _get_smb_domain(self):
        return None

    def open(self, file_store, file_store_folder):

        def mount_done_cb(obj, res, mount_finished):
            mount_finished['res'] = \
                obj.mount_enclosing_volume_finish(res)

        def ask_password_cb(op, message, default_user, default_domain, flags):
            username = self._get_smb_username()
            password = self._get_smb_password()
            domain  = self._get_smb_domain()
            username = username if username else default_user
            domain = domain if domain else default_domain
            if username and password and domain:
                op.set_username(username)
                op.set_domain(domain)
                op.set_password(password)
                op.set_password_save(Gio.PasswordSave.FOR_SESSION)
            else:
                op.set_anonymous(True)
            op.reply(Gio.MountOperationResult.HANDLED)

        uri='smb://%s/%s' % (file_store, file_store_folder)

        gvfs=Gio.Vfs.get_default()
        f = gvfs.get_file_for_uri(uri)
        r = f.get_path()

        if not r or not os.path.exists(r):
            op = Gio.MountOperation()
            op.connect('ask-password', ask_password_cb)
            mount_finished={}
            cancelable = Gio.Cancellable()
            f.mount_enclosing_volume(Gio.MountMountFlags.NONE, op, cancelable, mount_done_cb, mount_finished)
            loop = GObject.MainLoop()
            context = loop.get_context()
            f = gvfs.get_file_for_uri(uri)
            r = f.get_path()
            start = time.time()
            while not len(mount_finished):
                if (time.time() - start) > 10:
                    cancelable.cancel()
                    break
                context.iteration(True)

            f = gvfs.get_file_for_uri(uri)
            r = f.get_path()
            if not r:
                raise Exception('SMB mount "%s" failed.' % file_store_folder)

        self._mnt_path = r
        self._mounts[uri] = time.time()


    def clean(self):
        def _unmount_complete(obj, res, results) :
            results['res'] = obj.unmount_finish(res)

        stale_mounts = []

        for uri, last_used in self._mounts.iteritems():
            delta = time.time() - last_used
            if delta > _SMB_AUTO_UMOUNT:
                stale_mounts += [uri]

        gvfs=Gio.Vfs.get_default()

        for uri in stale_mounts:
            f = gvfs.get_file_for_uri(uri)
            if f:
                mnt = f.find_enclosing_mount()
                if mnt and mnt.can_unmount():
                    results = {}
                    cancelable = Gio.Cancellable()
                    mnt.unmount(Gio.MountUnmountFlags.NONE,
                                cancelable,
                                _unmount_complete,
                                results)
                    start = time.time()
                    loop = GObject.MainLoop()
                    context = loop.get_context()
                    while not len(results):
                        if (time.time() - start) > 10:
                            cancelable.cancel()
                            break
                        context.iteration(True)

                    f = gvfs.get_file_for_uri(uri)
                    if not f.get_path():
                        self._mounts.pop(uri)

    def _get_remote_name(self, filepath, file_id):
        filename = os.path.basename(filepath)
        bad = '\/:*?"<>|'
        filename = "".join(['_' if c in bad else c for c in filename])
        remote_file = os.path.join(self._mnt_path, "%i.%s" % (file_id, filename))
        return remote_file

    def upload(self, filepath, file_id):
        remote_file = self._get_remote_name(filepath, file_id)
        copyfile(filepath, remote_file)

    def download(self, filepath, file_id, mod_time):
        remote_file = self._get_remote_name(filepath, file_id)
        copyfile(remote_file, filepath)
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
