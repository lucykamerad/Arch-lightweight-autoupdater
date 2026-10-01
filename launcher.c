#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libgen.h>
#include <limits.h>

int main() {
    char exe_path[PATH_MAX];
    ssize_t len = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
    
    if (len != -1) {
        exe_path[len] = '\0';
        char *dir = dirname(exe_path);
        
        // Change working directory to where the executable is
        if (chdir(dir) != 0) {
            perror("chdir failed");
            return 1;
        }

        // Run the script directly (no shell) so that unusual characters in the
        // install path cannot be interpreted as shell syntax
        char script[PATH_MAX + 20];
        snprintf(script, sizeof(script), "%s/run_updater.sh", dir);
        execl(script, script, (char *)NULL);
        perror("exec failed");
        return 1;
    } else {
        perror("readlink failed");
        return 1;
    }
}
