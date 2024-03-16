import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
from contextlib import ExitStack
from tempfile import NamedTemporaryFile

from .log import edebug, edie, eerror, einfo


def get_etc_portage_tmp_file(directory_name, prefix):
    target_location = os.path.join(prefix + "/etc/portage", directory_name)

    if not os.path.isdir(target_location):
        edie(
            "The location {} needs to exist and be a directory".format(target_location)
        )

    handler = NamedTemporaryFile(
        mode="w", prefix="zzz_pkg_testing_tool_", dir=target_location
    )

    umask = os.umask(0)
    os.umask(umask)
    os.chmod(handler.name, 0o644 & ~umask)

    return handler
