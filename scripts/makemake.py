#!/usr/bin/env python3

# Generates a Makefile.am based on a description of C modules.
#
# You can run this manually to prodice Makefile.am, or you can add this line to
# configure.ac to run it automatically during autoreconf. Either way, only the
# final Makefile.am is included in the source distribution, so Python is not
# required to build the project.
#
# Make sure these lines are in configure.ac:
#
#   AC_PROG_CC
#   AM_PROG_AR
#   AC_PATH_PROG([RUBY], [ruby])
#   LT_INIT
#   AC_CONFIG_COMMANDS_PRE([python3 scripts/makemake.py])
#
# The tool assumes that each subdirectory of the source path that contains a
# "module.cfg" file is a module, and a similarly named subdirectory of the
# tests path contains Unity Test test suites for the module. The "module.cfg"
# file declares the module as either a library or a program, and lists the
# modules it depends on.
#
# Example of module.cfg for a program:
#
#   [module]
#   program = myapp
#   deps = executor reporter
#
# Example of module.cfg for a library:
#
#   [module]
#   library = executor
#   deps = cfgfile
#
# The file is in Python configparser format.
# (https://docs.python.org/3/library/configparser.html)
#
# The tool sets up Unity Test and CMock, and assumes CMock is installed as a
# submodule in third-party/. Ruby must be installed to run tests (but not to
# build). https://github.com/ThrowTheSwitch/CMock

import argparse
import configparser
from dataclasses import dataclass
import os
import sys
from typing import Optional


MODULE_CONFIG_FNAME = 'module.cfg'


MAKEFILE_PREAMBLE = '''### GENERATED BY scripts/makemake.py - DO NOT EDIT

ACLOCAL_AMFLAGS = -I m4

AM_CPPFLAGS = \\
    -I$(top_srcdir) \\
    -I$(top_srcdir)/src

if BUILD_LINUX
AM_CPPFLAGS += -DLINUX
endif
if BUILD_WINDOWS
AM_CPPFLAGS += -DWINDOWS
endif
if BUILD_APPLE
AM_CPPFLAGS += -DAPPLE
endif

AM_LDFLAGS = -pthread

CMOCK_CPPFLAGS = \\
    -I$(top_srcdir)/third-party/CMock/vendor/unity/src \\
    -I$(top_srcdir)/third-party/CMock/src \\
    -Itests/mocks

bin_PROGRAMS =
noinst_LTLIBRARIES =
check_PROGRAMS =
check_LTLIBRARIES =
CLEANFILES =
BUILT_SOURCES =

check_LTLIBRARIES += libcmock.la
libcmock_la_SOURCES = \\
    third-party/CMock/src/cmock.c \\
    third-party/CMock/src/cmock.h \\
    third-party/CMock/src/cmock_internals.h \\
    third-party/CMock/vendor/unity/src/unity.c \\
    third-party/CMock/vendor/unity/src/unity.h \\
    third-party/CMock/vendor/unity/src/unity_internals.h
libcmock_la_CPPFLAGS = $(CMOCK_CPPFLAGS)

CLEANFILES += tests/runners/runner_test_*.c

''' # noqa

RUNNER_GENERATION_CMDS = '''\
\t@test -n "$(RUBY)" || { echo "\\nPlease install Ruby to run tests.\\n"; exit 1; }
\t$(RUBY) $(top_srcdir)/third-party/CMock/vendor/unity/auto/generate_test_runner.rb $< $@
''' # noqa

MOCK_GENERATION_CMDS = '''\
\t@test -n "$(RUBY)" || { echo "\\nPlease install Ruby to run tests.\\n"; exit 1; }
\tmkdir -p tests/mocks
\tCMOCK_DIR=$(top_srcdir)/third-party/CMock \\
\tMOCK_OUT=tests/mocks \\
\t$(RUBY) $(top_srcdir)/third-party/CMock/scripts/create_mock.rb $<
''' # noqa

# EXTRA_DIST: The list of third-party/CMock files is selected to avoid
# accidentally including previous build output in a source distribution, which
# can potentially break the dist build.
MAKEFILE_POSTABLE = '''TESTS = $(check_PROGRAMS)

EXTRA_DIST = \\
    README.md \\
    third-party/CMock/LICENSE.txt \\
    third-party/CMock/README.md \\
    third-party/CMock/config \\
    third-party/CMock/lib \\
    third-party/CMock/scripts \\
    third-party/CMock/src/cmock.c \\
    third-party/CMock/src/cmock.h \\
    third-party/CMock/src/cmock_internals.h \\
    third-party/CMock/test \\
    third-party/CMock/vendor/unity/LICENSE.txt \\
    third-party/CMock/vendor/unity/README.md \\
    third-party/CMock/vendor/unity/auto \\
    third-party/CMock/vendor/unity/src/unity.c \\
    third-party/CMock/vendor/unity/src/unity.h \\
    third-party/CMock/vendor/unity/src/unity_internals.h
''' # noqa


def file_error(fname, message):
    print(f'{fname}: {message}')
    sys.exit(1)


def get_module_config(src_dir):
    modcfg = {}
    for item in os.listdir(src_dir):
        pth = os.path.join(src_dir, item, MODULE_CONFIG_FNAME)
        if not os.path.isfile(pth):
            continue
        cfg = configparser.ConfigParser()
        try:
            with open(pth) as fh:
                cfg.read_file(fh, source=pth)
        except configparser.Error as e:
            file_error(pth, f'Invalid configuration file: {e.message}')

        try:
            program = cfg.get('module', 'program', fallback=None)
            library = cfg.get('module', 'library', fallback=None)
            if program is None and library is None:
                file_error(pth, 'Must specify either program or library')
        except configparser.NoSectionError:
            file_error(pth, 'Must have [module] section')

        modcfg[item] = cfg
    return modcfg


def get_module_sources(src_dir, modname):
    items = os.listdir(os.path.join(src_dir, modname))
    sources = [
        item for item in items
        if item.endswith('.c') or item.endswith('.h')]
    return sources


def get_module_tests(tests_dir, modname):
    if not os.path.isdir(os.path.join(tests_dir, modname)):
        return []
    items = os.listdir(os.path.join(tests_dir, modname))
    tests = [
        item for item in items
        if item.startswith('test_') and item.endswith('.c')]
    return tests


@dataclass
class Module:
    cfgpath: str
    name: str
    deps: list
    source_dir: str
    sources: list
    tests_dir: str
    tests: list
    program: Optional[str] = None
    library: Optional[str] = None


def build_modules(modcfg, src_dir, tests_dir):
    mods = {}
    for modname in modcfg:
        cfgpath = os.path.join(src_dir, modname, MODULE_CONFIG_FNAME)

        deps = []
        try:
            deps_str = modcfg[modname].get('module', 'deps')
            deps = deps_str.split(' ')
        except configparser.NoOptionError:
            pass

        program = modcfg[modname].get('module', 'program', fallback=None)
        library = modcfg[modname].get('module', 'library', fallback=None)

        sources = get_module_sources(src_dir, modname)
        tests = get_module_tests(tests_dir, modname)

        m = Module(
            cfgpath=cfgpath,
            name=modname,
            deps=deps,
            source_dir=os.path.join(src_dir, modname),
            sources=sources,
            tests_dir=os.path.join(tests_dir, modname),
            tests=tests,
            program=program,
            library=library)
        mods[modname] = m

    for mk in mods:
        if mods[mk].deps:
            for d in mods[mk].deps:
                if d not in mods:
                    file_error(m.cfgpath, f'dep is not a module: {d}')
                if mods[d].library is None:
                    file_error(m.cfgpath, f'dep is not a library: {d}')

    return mods


def render_listvar(name, vals, is_concat=False):
    if len(vals) == 0:
        return ''
    op = '+=' if is_concat else '='
    if len(vals) == 1:
        return f'{name} {op} {vals[0]}\n'
    return f'{name} {op} \\\n    ' + ' \\\n    '.join(vals) + '\n'


def render_module_sources(mod):
    src_pths = [os.path.join(mod.source_dir, src) for src in mod.sources]

    # TODO: add dep module headers?

    if mod.program:
        return render_listvar(mod.program + '_SOURCES', src_pths)
    return render_listvar('lib' + mod.library + '_la_SOURCES', src_pths)


def render_module_deps(mod):
    dep_pths = [f'lib{dep}.la' for dep in mod.deps]
    if mod.program:
        return render_listvar(mod.program + '_LDADD', dep_pths)
    return render_listvar('lib' + mod.library + '_la_LIBADD', dep_pths)


def render_mock(mod):
    if mod.program:
        return ''

    parts = [f'tests/mocks/mock_{mod.name}.c tests/mocks/mock_{mod.name}.h: '
             f'{mod.source_dir}/{mod.name}.h\n' +
             MOCK_GENERATION_CMDS]
    parts.append(render_listvar(
        'check_LTLIBRARIES', [f'lib{mod.library}_mock.la'], is_concat=True))
    parts.append(render_listvar(
        f'lib{mod.library}_mock_la_SOURCES',
        [f'tests/mocks/mock_{mod.name}.c']))
    parts.append(render_listvar(
        f'lib{mod.library}_mock_la_CPPFLAGS',
        ['$(CMOCK_CPPFLAGS)', '$(AM_CPPFLAGS)',
         f'-I$(top_srcdir)/src/{mod.name}']))
    parts.append(render_listvar(
        f'lib{mod.library}_mock_la_LIBADD',
        ['libcmock.la']))

    parts.append(render_listvar(
        'CLEANFILES',
        [f'tests/mocks/mock_{mod.library}.c',
         f'tests/mocks/mock_{mod.library}.h'],
        is_concat=True))
    parts.append(render_listvar(
        'BUILT_SOURCES',
        [f'tests/mocks/mock_{mod.library}.c',
         f'tests/mocks/mock_{mod.library}.h'],
        is_concat=True))

    parts = [p for p in parts if p]
    return '\n'.join(parts)


def render_tests(mod):
    if mod.program:
        return ''

    parts = []

    for test_src in mod.tests:
        test_base = test_src[:-2]

        parts.append(render_listvar(
            'check_PROGRAMS', [f'tests/runners/{test_base}'], is_concat=True))

        parts.append(
            f'tests/runners/runner_{test_base}.c: '
            f'{mod.tests_dir}/{test_base}.c\n' +
            RUNNER_GENERATION_CMDS)

        test_srcs = [
            f'tests/runners/runner_{test_base}.c',
            f'{mod.tests_dir}/{test_base}.c',
            f'{mod.source_dir}/{mod.library}.h']
        parts.append(render_listvar(
            f'tests_runners_{test_base}_SOURCES', test_srcs))

        built_sources = (
            [f'tests/mocks/mock_{d}.c' for d in mod.deps] +
            [f'tests/mocks/mock_{d}.h' for d in mod.deps])
        if built_sources:
            parts.append(render_listvar(
                f'nodist_tests_runners_{test_base}_SOURCES', built_sources))
            parts.append(
                f'tests/runners/{test_base}-runner_{test_base}' +
                '.$(OBJEXT): \\\n    ' +
                ' \\\n    '.join(built_sources) +
                '\n')

        deplibs = [f'libcmock.la lib{mod.library}.la']
        for d in mod.deps:
            deplibs.append(f'lib{d}_mock.la')
        parts.append(render_listvar(
            f'tests_runners_{test_base}_LDADD', deplibs))

        depcppflags = [f'-I$(top_srcdir)/src/{d}' for d in mod.deps]
        parts.append(render_listvar(
            f'tests_runners_{test_base}_CPPFLAGS',
            ['$(CMOCK_CPPFLAGS)', '$(AM_CPPFLAGS)'] + depcppflags))

    parts = [p for p in parts if p]
    return '\n'.join(parts)


def render_module(mod):
    parts = ['### ' + mod.name + '\n']
    if mod.program:
        parts.append(render_listvar(
            'bin_PROGRAMS', [mod.program], is_concat=True))
    else:
        parts.append(render_listvar(
            'noinst_LTLIBRARIES', [f'lib{mod.library}.la'], is_concat=True))
    parts.append(render_module_sources(mod))
    parts.append(render_module_deps(mod))
    parts.append(render_mock(mod))
    parts.append(render_tests(mod))

    parts = [p for p in parts if p]
    return '\n'.join(parts) + '\n'


def render_makefile(root_dir, mods):
    parts = [MAKEFILE_PREAMBLE]
    for m in sorted(mods.keys()):
        parts.append(render_module(mods[m]))
    parts.append(MAKEFILE_POSTABLE)

    if os.path.exists(os.path.join(root_dir, 'project.mk')):
        with open(os.path.join(root_dir, 'project.mk')) as fh:
            parts.append(fh.read())

    parts = [p for p in parts if p]
    return '\n'.join(parts)


def main(args):
    parser = argparse.ArgumentParser(
        description='Generates Makefile.am from a source tree and module.cfg '
                    'files')
    parser.add_argument(
        '--root-dir', default='.', help='The project root directory')
    args = parser.parse_args(args)

    src_dir = os.path.join(args.root_dir, 'src')
    tests_dir = os.path.join(args.root_dir, 'tests')
    modcfg = get_module_config(src_dir)
    mods = build_modules(modcfg, src_dir, tests_dir)
    makefile_txt = render_makefile(args.root_dir, mods)

    makefile_pth = os.path.join(args.root_dir, 'Makefile.am')
    if os.path.exists(makefile_pth):
        if os.path.exists(makefile_pth + '~'):
            os.remove(makefile_pth + '~')
        os.rename(makefile_pth, makefile_pth + '~')
    with open(makefile_pth, 'w') as fh:
        fh.write(makefile_txt)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
