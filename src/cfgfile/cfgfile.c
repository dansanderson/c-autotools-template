#include "cfgfile.h"
#include <stdbool.h>
#include <stdlib.h>
#include "cfgfile.h"
#include "cfgmap.h"

char cfgfile_publicbuf[1024];

static char tempbuf[1024];

static void handle_token(char *token, int len) {
    // ...
}

bool cfgfile_parse(char *filetext, cfgfile_config_t **result) {
    // ...

    _cfgfile_cfgmap_map *map;
    map = _cfgfile_cfgmap_create_map();
    if (map == NULL)
        return false;

    return true;
}

void cfgfile_print_message(void) {
    puts("cfgfile message");
}

int cfgfile_func(int x) {
    return 0;
}
