ACLOCAL_AMFLAGS = -I m4

AM_CPPFLAGS = \
	-I$(top_srcdir) \
	-I$(top_srcdir)/src

bin_PROGRAMS = myapp

noinst_LTLIBRARIES = \
	libcfgfile.la \
	libexecutor.la \
	libreporter.la

libcfgfile_la_SOURCES = \
	src/cfgfile/cfgfile.c \
	src/cfgfile/cfgfile.h \
	src/cfgfile/cfgmap.c \
	src/cfgfile/cfgmap.h

libexecutor_la_SOURCES = \
	src/executor/executor.c \
	src/executor/executor.h \
	src/cfgfile/cfgfile.h
libexecutor_la_LIBADD = \
	libcfgfile.la

libreporter_la_SOURCES = \
	src/reporter/reporter.c \
	src/reporter/reporter.h \
	src/cfgfile/cfgfile.h
libreporter_la_LIBADD = \
	libcfgfile.la

myapp_SOURCES = \
	src/myapp/myapp.c \
	src/executor/executor.h \
	src/executor/reporter.h
myapp_LDADD = \
	libexecutor.la \
	libreporter.la

check_PROGRAMS = tests/runners/test_cfgfile
TESTS = $(check_PROGRAMS)

CLEANFILES = tests/runners/runner_test_*.c

tests/runners/runner_test_%.c:
	@test -n "$(RUBY)" || { echo "\nPlease install Ruby to run tests.\n"; exit 1; }
	$(RUBY) $(top_srcdir)/third-party/CMock/vendor/unity/auto/generate_test_runner.rb $< $@

tests/runners/runner_test_cfgfile.c: tests/cfgfile/test_cfgfile.c

tests_runners_test_cfgfile_SOURCES = \
    tests/runners/runner_test_cfgfile.c \
    tests/cfgfile/test_cfgfile.c \
    src/cfgfile/cfgfile.h \
    third-party/CMock/vendor/unity/src/unity.c \
    third-party/CMock/vendor/unity/src/unity.h \
    third-party/CMock/vendor/unity/src/unity_internals.h
tests_runners_test_cfgfile_LDADD = \
    libcfgfile.la
tests_runners_test_cfgfile_CPPFLAGS = \
    -I$(top_srcdir)/third-party/CMock/vendor/unity/src \
    -I$(top_srcdir)/third-party/CMock/src \
    -I$(top_srcdir)/src \
    -Isrc

tests/mocks/mock_%.c:
	@test -n "$(RUBY)" || { echo "\nPlease install Ruby to run tests.\n"; exit 1; }
	mkdir -p tests/mocks
	CMOCK_DIR=$(top_srcdir)/third-party/CMock \
	MOCK_OUT=tests/mocks \
	$(RUBY) $(top_srcdir)/third-party/CMock/scripts/create_mock.rb $<

tests/mocks/mock_cfgfile.c: src/cfgfile/cfgfile.h

check_LTLIBRARIES = libcfgfile_mock.la
libcfgfile_mock_la_SOURCES = \
    tests/mocks/mock_cfgfile.c
libcfgfile_mock_la_CPPFLAGS = \
    -I$(top_srcdir)/third-party/CMock/vendor/unity/src \
    -I$(top_srcdir)/third-party/CMock/src \
    -I$(top_srcdir)/src \
	-I$(top_srcdir)/src/cfgfile

CLEANFILES += tests/mocks/mock_cfgfile.c tests/mocks/mock_cfgfile.h
