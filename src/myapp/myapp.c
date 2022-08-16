#include <stdio.h>

#include "executor/executor.h"
#include "reporter/reporter.h"
#include "config.h"


int main(int argc, char **argv) {
    puts(PACKAGE_STRING);
    executor_print_message();
    reporter_print_message();
}
