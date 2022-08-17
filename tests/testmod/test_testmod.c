#include "testmod/testmod.h"
#include "unity.h"

void setUp(void) {}

void tearDown(void) {}

void test_TestmodDoSomething_Returns3x(void) {
  TEST_ASSERT_EQUAL_MESSAGE(15, testmod_dosomething(5), "Returns 3x the argument");
}
