# This file is part of rudd.
#
# rudd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rudd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rudd.  If not, see <http://www.gnu.org/licenses/>.

import sys
import subprocess
import argparse
import config


DEFAULT_CONFIG = "/etc/rudd.conf"
VERSION = (0, 2, 0)


def prog_name():
    return sys.argv[0]


def print_version():
    v = "{}.{}.{}".format(*VERSION)
    print("{} {}".format(prog_name(), v))


def die(fmt, *args, **kwargs):
    msg = fmt.format(*args, **kwargs)
    print("{}: {}".format(prog_name(), msg), file=sys.stderr)
    sys.exit(1)


def rooted(path):
    return "/" + path.strip("/")


def shell_exec(cmd, cwd):
    p = subprocess.run(cmd, shell=True, cwd=cwd,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return p.returncode, str(p.stderr, "utf-8")


def sync_entry(src, dest, filters, rsync_opts):
    args = ["rsync", "--archive", "--delete", "--prune-empty-dirs"]
    for f in filters:
        args.append("--{}={}".format(*f))
    args.extend(rsync_opts)
    args.extend([rooted(src), dest])
    p = subprocess.run(args, cwd=src, stderr=subprocess.PIPE)

    return p.returncode, str(p.stderr, "utf-8")


def parse_args():
    ap = argparse.ArgumentParser(prog="rudd",
                                 description="Backup files using rsync")
    ap.add_argument(dest="dest", metavar="DEST")
    ap.add_argument("-c", "--config", default=DEFAULT_CONFIG,
                    help="configuration file name")
    ap.add_argument("--dry-run", action="store_true",
                    help="perform a trial run with no changes made")
    ap.add_argument("--rsync-verbose", action="store_true",
                    help="ask rsync to increase verbosity")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="increase verbosity")
    ap.add_argument("-V", "--version", action="store_true",
                    help="output version information and exit")

    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.version:
        print_version()
        sys.exit(0)

    try:
        cfg = config.parse_file(args.config)
    except Exception as e:
        die("Failed to read configuration file: " + str(e))


    for c in cfg:
        for o in c.options:
            if o.name == "exec":
                if args.verbose:
                    print("Executing '{}'.".format(o.value))
                code, stderr = shell_exec(o.value, c.path)
                if code or stderr:
                    die("failed: {}: {}", code, stderr)

        filters = []
        for o in c.options:
            if o.name in ["include", "exclude"]:
                filters.append((o.name, o.value))

        if args.verbose:
            print("Synchronizing {}...".format(c.path))
        opts = []
        if args.rsync_verbose:
            opts.append("--verbose")
        if args.dry_run:
            opts.append("--dry-run")
        code, stderr = sync_entry(c.path, args.dest, filters, opts)
        if code or stderr:
            die("rsync failed: {}: {}", code, stderr)
