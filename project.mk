# project.mk gets appended to Makefile.am by scripts/makemake.py. It can
# contain additional Automake definitions, as well as Makefile rules in
# Automake-compatible syntax.
#
# The generated Makefile.am creates these Automake list variables, which can be
# extended by project.mk with the += operator:
#
# ACLOCAL_AMFLAGS +=
# AM_CPPFLAGS +=
# bin_PROGRAMS +=
# noinst_LTLIBRARIES +=
# check_PROGRAMS +=
# check_LTLIBRARIES +=
# CLEANFILES +=
# BUILT_SOURCES +=
# TESTS +=
# EXTRA_DIST +=
