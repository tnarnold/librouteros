from time import sleep
from os import devnull
from subprocess import Popen, check_call
from tempfile import NamedTemporaryFile
import socket

import pytest
import py.path

import librouteros


DEV_NULL = open(devnull, 'w')


def api_session():
    for x in range(10):
        try:
            sock = socket.create_connection(('127.0.0.1', 8728))
            return librouteros.login(username='admin', password='', sock=sock)
        except (librouteros.ConnectionError, socket.error, socket.timeout):
            sleep(1)
    else:
        raise librouteros.ConnectionError('could not connect to device')


@pytest.fixture(scope='session')
def disk_image(request):
    """Create a temporary disk image backed by original one."""
    img = NamedTemporaryFile()
    request.addfinalizer(img.close)
    cmd = [
        'qemu-img', 'create',
        '-f', 'qcow2',
        # Path to backing file must be absolute or relative to new image
        '-b', str(py.path.local().join('images/routeros_6.33.3.qcow2')),
        img.name,
    ]
    check_call(cmd, stdout=DEV_NULL)
    return img.name


@pytest.fixture(scope='session')
def routeros(request, disk_image):
    cmd = [
        'qemu-system-i386',
        '-m', '64',
        '-display', 'none',
        '-hda', disk_image,
        '-net', 'user,hostfwd=tcp::8728-:8728',
        '-net', 'nic,model=e1000',
    ]
    proc = Popen(cmd, stdout=DEV_NULL, close_fds=True)
    request.addfinalizer(proc.kill)
    return api_session()
