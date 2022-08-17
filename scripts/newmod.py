#!/usr/bin/env python3

# Creates files for a new module.
#
# To create a library module:
#   python3 scripts/newmod.py <module-name>
#
# To create a program module:
#   python3 scripts/newmod.py --program <module-name>

import argparse
import os
import sys


LIBRARY_TEMPLATES = {
    'src/{modname}/{modname}.c': '''\
#include "{modname}.h"

int {modname}_dosomething(int arg) {{
    return arg * 3;
}}
''',

    'src/{modname}/{modname}.h': '''\
/**
 * @file {modname}.h
 * @brief
 */

#ifndef {modname_upper}_H_
#define {modname_upper}_H_

int {modname}_dosomething(int arg);

#endif
''',

    'src/{modname}/module.cfg': '''\
[module]
library = {modname}
# deps =
''',

'tests/{modname}/test_{modname}.c': '''\
#include "{modname}/{modname}.h"
#include "unity.h"

void setUp(void) {{}}

void tearDown(void) {{}}

void test_{modname_title}DoSomething_Returns3x(void) {{
  TEST_ASSERT_EQUAL_MESSAGE(15, {modname}_dosomething(5), "Returns 3x the argument");
}}
''' # noqa
}

PROGRAM_TEMPLATES = {
    'src/{modname}/{modname}.c': '''\
int main(int argc, char **argv) {
    return 0;
}
''',

    'src/{modname}/module.cfg': '''\
[module]
program = {modname}
# deps =
'''
} # noqa


def main(args):
    parser = argparse.ArgumentParser(
        description='Creates files for a new module')
    parser.add_argument(
        '--program', action='store_true',
        help='Create this module as a program')
    parser.add_argument(
        '--root-dir', default='.', help='The project root directory')
    parser.add_argument('name')
    args = parser.parse_args(args)

    if os.path.exists(os.path.join(args.root_dir, 'src', args.name)):
        print(f'{args.name}: Module already exists, aborting')
        sys.exit(1)

    tmpls = LIBRARY_TEMPLATES
    if args.program:
        tmpls = PROGRAM_TEMPLATES

    tmpl_ctx = {
        'modname': args.name,
        'modname_upper': args.name.upper(),
        'modname_title': args.name.capitalize()
    }
    for pth_tmpl in tmpls:
        text_tmpl = tmpls[pth_tmpl]
        pth = os.path.join(args.root_dir, pth_tmpl.format(**tmpl_ctx))
        text = text_tmpl.format(**tmpl_ctx)
        print(pth)
        os.makedirs(os.path.dirname(pth), exist_ok=True)
        with open(pth, 'w') as fh:
            fh.write(text)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
