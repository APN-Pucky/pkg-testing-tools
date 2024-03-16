import sys


def eerror(msg):
    print("[ERROR] >>> {}".format(msg))


def einfo(msg):
    print("[INFO] >>> {}".format(msg))


def edebug(msg):
    print("[DEBUG] >>> {}".format(msg))


def edie(msg):
    eerror(msg)
    sys.exit(1)
