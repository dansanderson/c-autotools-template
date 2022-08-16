#include "cfgfile/cfgfile.h"
#include "unity.h"

void setUp(void) {}

void tearDown(void) {}

void test_cfgfileFunc_ReturnsZero(void) {
  TEST_ASSERT_EQUAL_MESSAGE(0, cfgfile_func(999), "func returns 0");
}
