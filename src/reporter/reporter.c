#include "reporter.h"
#include <stdio.h>
#include "cfgfile/cfgfile.h"

void reporter_print_message(void) {
    puts("reporter message");
    cfgfile_print_message();
    puts("reporter message END");
}
