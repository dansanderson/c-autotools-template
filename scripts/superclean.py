#!/usr/bin/env python3

# Cleans all git-ignored files and empty directories out of the project.
#
# Use --dry-run to print what would be deleted without actually deleting.
#   python3 superclean.py --dry-run
#
# Unlike the Autotools clean targets (clean, distclean, maintainer-clean), this
# script makes an aggressive attempt at reducing the source directory to just
# the files that are—or would be—committed to git. This requires re-running the
# full Autotools set-up to return to a buildable state:
#    autoreconf --install
#    ./configure
#    make distcheck
#
# This shouldn't be necessary *if the Makefiles are written correctly,* but I
# found it too easy for an error in a Makefile to generate a file and not
# remember to clean it up normally, causing builds to fail or succeed when they
# shouldn't. Once Makefiles are stable, Autotools does a good job of detecting
# changes and re-generating files consistently.
#
# https://www.gnu.org/software/automake/manual/html_node/Clean.html

import argparse
import collections
import os.path
import re
import shutil
import subprocess
import sys


def error(msg):
    """Prints an error message then exits the program.

    Args:
        msg: The message to print.
    """
    sys.stderr.write(msg + '\n')
    sys.exit(1)


def get_untracked_files(root_dir=None, only_ignored=True):
    """Gets files to delete from current git module and submodules.

    This reports *all* untracked files from submodules, even if only_ignored is
    specified for the top-level repo. This is how this is intended to be used:
    report ignored files from the top repo, and all untracked files from
    submodules, under the assumption that you are not intending to create files
    in submodules as part of the project.

    Args:
        root_dir: Path to the root directory for the git repo.
        only_ignored: Only include gitignored files for this repo.

    Returns:
        (results, errcode). If success, results is a list of files to delete
        relative to the original root directory. On failure, results is None
        and errcode contains the most recent shell error code returned by a git
        command.
    """
    cwd = os.getcwd()
    root_dir = os.path.abspath(root_dir or cwd)
    os.chdir(root_dir)

    # git does not support --recurse-submodules with --others. I know, it looks
    # tempting, but it doesn't work. We do our own submodule recursion.
    ls_files_cmd = ['git', 'ls-files', '--others', '--exclude-standard']
    if only_ignored:
        ls_files_cmd.insert(2, '--ignored')
    result = subprocess.run(ls_files_cmd, capture_output=True)
    if result.returncode:
        return (None, result.returncode)

    untracked_files = []
    submodule_paths = []
    if os.path.exists('.gitmodules'):
        with open('.gitmodules') as fh:
            for line in fh:
                m = re.match(r'\s*path = (.*)', line)
                if m:
                    submodule_paths.append(m.group(1))
    for p in submodule_paths:
        submod_files, err = get_untracked_files(
            root_dir=os.path.join(root_dir, p), only_ignored=False)
        if err:
            os.chdir(cwd)
            return (None, err)
        untracked_files.extend(submod_files)

    untracked_files.extend([
        os.path.join(root_dir, p.strip())
        for p in str(result.stdout, encoding='utf-8').split('\n')
        if p.strip()])

    os.chdir(cwd)
    return (untracked_files, None)


def get_empty_directories(root_dir=None, assume_deleted=None):
    """Locates all subdirectories that contain zero files.

    Directory names are returned in reverse sorted order, which is the order to
    delete nested empty directories.

    This only reports directories that contain no files at the time the
    function is called. It does not calculate which directories would be empty
    if all unwanted files were to be deleted. (It'd be fun to pass the result
    of get_untracked_files to this to subtract them in a dry-run. Maybe another
    day.)

    Args:
        root_dir: The root directory to search, or None for the current working
            directory.
        assume_deleted: A list of file paths to assume are not present for the
            purposes of determining if a directory is empty. (Used for a dry
            run of a process that deletes files before deleting empty
            directories.)

    Returns:
        A list of empty directories under root_dir.
    """
    if root_dir is None:
        root_dir = os.getcwd()

    fcounts: collections.defaultdict[str, int] = collections.defaultdict(int)
    for (dname, dnames, fnames) in os.walk(root_dir):
        if dname == '.git' or '/.git/' in dname:
            continue
        dname = dname[len(root_dir):]
        dparts = dname.split(os.path.sep)
        for i in range(1, len(dparts)+1):
            if i > 1:
                partial = os.path.join(*dparts[:i])
            else:
                partial = dparts[0]
            fcounts[partial] += len(fnames)

    if assume_deleted is not None:
        for p in assume_deleted:
            dname = os.path.dirname(p)
            if not os.path.exists(dname):
                continue
            if dname.startswith(root_dir):
                dname = dname[len(root_dir):]
            dparts = dname.split(os.path.sep)
            for i in range(1, len(dparts)+1):
                if i > 1:
                    partial = os.path.join(*dparts[:i])
                else:
                    partial = dparts[0]
                fcounts[partial] -= 1

    empty_dirs = [p for p in fcounts if fcounts[p] == 0]
    empty_dirs.sort(reverse=True)
    empty_dirs_full = [os.path.join(root_dir, p) for p in empty_dirs]
    return empty_dirs_full


def main(args):
    parser = argparse.ArgumentParser(
        description='Deletes all build artifacts from the project.',
        epilog="""This deletes all files ignored by git from the main project,
               then deletes *all* untracked files in subdirectories,
               recursively. Do not use this if you intend to make changes to
               submodules!
               """)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Do not delete anything, only report what would be deleted')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print all files and directories being deleted')
    parser.add_argument(
        '--root-dir',
        help='The project root directory; by default, uses current working '
        'directory')
    args = parser.parse_args(args)

    if not args.root_dir and not os.path.exists('.git'):
        error('Please run this from the project root directory, or specify '
              '--root-dir.')

    if not shutil.which('git'):
        error('Cannot find git. Is it on the command path?')

    files_to_delete, err = get_untracked_files(root_dir=args.root_dir)
    if err:
        error(f'git ls-files returned an error code ({err}), aborting')
    dirs_to_delete = get_empty_directories(
        root_dir=args.root_dir,
        assume_deleted=files_to_delete)

    if args.dry_run:
        print(
            '\nThe following files and directories would be deleted if the\n'
            '--dry-run option were not specified:\n')

    for fpath in files_to_delete:
        if args.dry_run or args.verbose:
            print(fpath)
        if not args.dry_run:
            os.remove(fpath)

    for dpath in dirs_to_delete:
        if args.dry_run or args.verbose:
            print(dpath)
        if not args.dry_run:
            os.rmdir(dpath)

    if args.dry_run:
        print(
            f'\nFiles to delete: {len(files_to_delete)}\n'
            f'Directories to delete: {len(dirs_to_delete)}\n\n'
            'To actually delete these files, omit the --dry-run option.\n')
    elif args.verbose:
        sys.stderr.write(
            f'\nFiles deleted: {len(files_to_delete)}\n'
            f'Directories deleted: {len(dirs_to_delete)}\n\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
