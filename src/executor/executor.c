#include "executor.h"

#include <stdio.h>

#include "cfgfile/cfgfile.h"

void executor_print_message(void) {
    puts("executor message");
    cfgfile_print_message();
}

int executor_doit(int arg) {
    return cfgfile_func(arg);
}
