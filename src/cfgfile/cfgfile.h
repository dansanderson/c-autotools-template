/**
 * @file cfgfile.h
 * @brief An example of a module.
 */

#ifndef CFGFILE_H_
#define CFGFILE_H_

#include <stdbool.h>
#include <stdio.h>

/**
 * @brief Configuration for the program.
 */
typedef struct {
    char *logfile_path;
    // ...
} cfgfile_config_t;

/**
 * @brief Parses the text of a configuration file.
 *
 * @param filetext The full text of the file, as a null-terminated string.
 * @param result Output ptr to the config structure to populate.
 * @return true Success
 * @return false Failure
 */
bool cfgfile_parse(char *filetext, cfgfile_config_t **result);

void cfgfile_print_message(void);

int cfgfile_func(int x);

#endif