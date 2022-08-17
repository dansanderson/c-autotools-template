# c-autotools-template

This is a template for new C projects using GNU Autotools, a tool-assisted
module system, and unit testing with Unity Test and CMock. It takes a simple
but opinionated view on module organization and unit testing. This repo
includes a few example modules illustrating module dependencies and unit tests.

Project maintainers need Python 3.x and Ruby 2.x installed. The source
distribution can be built on any POSIX-compliant system without Python or Ruby.

A project based on this template organizes its C code into modules, defined
below. You use a tool to generate the `Makefile.am` from the module layout and
configuration.

## C Modules

A _module_ is a self-contained collection of functionality, implemented as one
or more C source files. A module can define a _program_, or it can define a
_library_ used by other modules. A library module exposes a public interface
with a header file.

Each module has a name consisting of a letter followed by zero or more letters
and numbers. The module name is used for the module source directory, the
module's header file and primary source file, the module tests directory, and
when declaring dependencies from other modules.

The following example files are included in the template under `src/` and
`tests/`. They define three library modules (cfgfile, executor, reporter) and
one program module (myapp):

```text
src/
  cfgfile/
    cfgfile.c
    cfgfile.h
    cfgmap.c
    cfgmap.h
    module.cfg
  executor/
    executor.c
    executor.h
    module.cfg
  reporter/
    reporter.c
    reporter.h
    module.cfg
  myapp/
    myapp.c
    module.cfg
tests/
  cfgfile/
    test_cfgfile.c
  executor/
    test_executor.c
  reporter/
    test_reporter.c
```

Each `module.cfg` file describes the module, including whether it is a library
or a program, and on which other modules (if any) it depends. For example,
`executor/module.cfg` looks like this:

```ini
[module]
library = executor
deps = cfgfile
```

`myapp/module.cfg` looks like this:

```ini
[module]
program = myapp
deps = executor reporter
```

## Module source files

The module source directory `src/{module}/` must contain a `{module}.h` header
file that declares the module's public interface and a `{module}.c` that
implements it. The directory can optionally contain additional source files
that are compiled and linked with the module.

A source file can `#include` any internal header by its name. To `#include` the
public interface of a dependency, use the path from `src/`:

```c
#include "executor.h"
#include "cfgfile/cfgfile.h"
```

When a program module is built, it is linked statically with all of its
dependencies (and all of their dependencies, and so on). It is recommended to
use C-style name prefixes for all non-`static` symbols. Specifically:

* Module public symbols should begin with the module name and an underscore:
  `executor_do_something()`
* Module internal symbols shared across files should begin with an underscore,
  the module name, and another underscore: `_executor_private()`
* Symbols internal to a single source file should be declared `static`. No
  prefix is needed for `static` symbols.
* The header guard `#define` for the module public header should be named after
  the module: `EXECUTOR_H_`
* The header guard `#define` for a module private header should use a prefix of
  an underscore, the module name, and an underscore: `_EXECUTOR_PRIVATE_H_`

A program module must define `int main(int argc, char **argv)`. A library
module must not.

## Module unit tests and mocks

Each source file under `tests/{module}/` named `test_{suite}.c` is a [Unity
Test](http://www.throwtheswitch.org/unity) test suite. A test suite should
`#include` the header of the module under test with its `src/` relative path.
It must also `#include "unity.h"`.

Each function with a name beginning with `test_` is a unit test in the suite.
It should have a `void` parameter specification and a `void` return type. It is
recommended to include the name of the function under test, the condition of
the test, and the expected result in the name of the `test_...()` function,
spelled CamelCase and delimited by underscores.

The test function contains code for the test and Unity Test assertions. See the
[Unity Assertions
Reference](https://github.com/ThrowTheSwitch/Unity/blob/master/docs/UnityAssertionsReference.md).

A test suite can optionally define `void setUp(void)` and
`void tearDown(void)`, to be called before and after each test, respectively.

Each test suite is linked with the module under test, along with _mock modules_
for each dependency of the module under test, generated with
[CMock](http://www.throwtheswitch.org/cmock). Every call that the function
under test makes to a dependency module must be declared with a [CMock
expectation](https://github.com/ThrowTheSwitch/CMock/blob/master/docs/CMock_Summary.md).
The actual dependency function is not called.

```c
#include "executor/executor.h"
#include "mock_cfgfile.h"
#include "unity.h"

void test_Square_UsesExampleTwo(void) {
  cfgfile_func_ExpectAndReturn(7, 49);
  int result = executor_doit(7);
  TEST_ASSERT_EQUAL_INT(49, result);
}
```

A module can have more than one test suite. Suite names must be unique across
the project, so a suite not named after the module under test should use the
module name as a prefix. It is recommended that each library module have at
least one test suite named after the module.

## Generating the Makefile.am

GNU Autotools uses `configure.ac` and `Makefile.am` to generate build scripts.
This template further uses a script to generate `Makefile.am` from the module
source layout and configuration files. To generate `Makefile.am`:

```text
python3 scripts/makemake.py
```

This script is intentionally not invoked from either `configure.ac` or
`Makefile.am`. A project maintainer must run it directly when module source
files are added or deleted, or when `module.cfg` files are modified. It is
recommended to commit the generated `Makefile.am` to the project repo.

## Building the project and running Autotools targets

After the `Makefile.am` file is generated, you can use GNU Autotools as normal:

```text
autoreconf --install
./configure
make
```

To build and run all unit tests:

```text
make check
```

To make and validate the source distribution:

```text
make distcheck
```

## Running and debugging a unit test

Each test suite is built to a "runner" program, then run as part of
`make check`. The runner programs are created under `tests/runners/`, and named
after the test suite source file.

To build all unit tests and run a specific test suite:

```text
make check TESTS='tests/runners/test_cfgfile'
```

To build just one test suite runner:

```text
make tests/runners/test_cfgfile
```

To run a test suite runner after it is built, simply run the program:

```text
./tests/runners/test_cfgfile
```

You can attach a debugger to a test runner and set breakpoints in the module
under test. I have included [Visual Studio
Code](https://code.visualstudio.com/) project configuration (in `.vscode/`) for
a "Debug a test" configuration. Select a test suite file, then run this
configuration to build and run the test in the VSCode debugger interface.

## Cleaning up build output

GNU Autotools generates Makefile targets to clean up build output:

* `make clean` : deletes files created by `make`
* `make distclean` : deletes additional files created by `./configure`

Neither target deletes files created by `autoreconf --install`.

Because it is sometimes useful to completely restore the project directory to
the way it was, I have included a script, `scripts/superclean.py`, that deletes
all files ignored by Git and `.gitignore`, and deletes all untracked files in
Git submodules (such as the provided `third-party/CMock`). Use the `--dry-run`
option to cause it to print everything that will be deleted without actually
deleting it.

```text
python3 scripts/superclean.py --dry-run

python3 scripts/superclean.py
```

`Makefile.am` is not deleted by `superclean.py` because it is not in
`.gitignore`. `Makefile.am` is safe to delete, if necessary. You can recreate
it with `scripts/makemake.py`.

## Still to do

Right now, the entire `Makefile.am` is created by `scripts/makemake.py`. If you
want to create custom rules or definitions, you must modify this script. I'd
like to extend this to read customizations from another file.

It might be useful to write larger (non-unit) test programs that use a
combination of real (non-mock) modules and mocks. It'd be nice to support a
`test.cfg` file that could request a linkage combination for a given
test suite, without the need for custom rules.

The name prefix best practices are important enough that it'd be good to have a
script that validates that they are followed.

Modules are easy enough to create by hand, but it'd be even easier if there
were a script that can create new modules from a template.

It's not obvious how to mock third-party libraries. It may be sufficient to run
the CMock generator tool on a third-party library header file. This is not yet
a built-in facility of `makemake.py`.

## License

This template and related tools are released under [The
Unlicense](https://unlicense.org). See [LICENSE](./LICENSE) for complete text.
You are _not_ required to use this license for your project.

## Note from the author

I started this thinking it'd just be a demonstration of novice best practices
for organizing a GNU Autotools project. I tried to avoid writing a module
management tool, but I couldn't get the `Makefile.am` boilerplate for tests and
mocks succinct enough to my satisfaction. I concluded that writing my own tool
would be better for my projects than trying to reuse other module management
systems like
[gnulib-tool](https://www.gnu.org/software/gnulib/manual/html_node/Invoking-gnulib_002dtool.html).

Feedback is welcome! If you have ideas for how this can be improved,
fixed, or made more generally useful, please [file an
issue](https://github.com/dansanderson/c-autotools-template/issues). [Pull
requests](https://github.com/dansanderson/c-autotools-template/pulls) are also
welcome, though please pardon me if I take a while to respond.

Thanks!

— Dan ([contact@dansanderson.com])
