#!/usr/bin/env python2
import random
import subprocess
import sys

from cfme.utils import conf


def main():
    key_list = [key[-9:].replace(' ', '') for key in conf['gpg']['allowed_keys']]
    servers = conf['gpg']['servers']

    for _ in range(3):
        server = random.choice(servers)
        proc = subprocess.Popen(
            ['gpg', '--recv-keys', '--keyserver', server] + key_list)
        proc.wait()
        if proc.returncode == 0:
            sys.exit(proc.returncode)
        else:
            print("keyserver: {s} not available. exit code: {c}".format(s=server,
                                                                        c=proc.returncode))


if __name__ == "__main__":
    main()
