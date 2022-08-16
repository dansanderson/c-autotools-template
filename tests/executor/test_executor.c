#include "executor/executor.h"
#include "mock_cfgfile.h"
#include "unity.h"

void test_Square_UsesExampleTwo(void) {
  cfgfile_func_ExpectAndReturn(7, 49);
  int result = executor_doit(7);
  TEST_ASSERT_EQUAL_INT(49, result);
}
