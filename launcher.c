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

        // Construct command to run the script
        char command[PATH_MAX + 50];
        snprintf(command, sizeof(command), "\"%s/run_updater.sh\"", dir);
        
        // Use system() to run the script
        // We use the absolute path we found just to be safe
        int ret = system(command);
        return WEXITSTATUS(ret);
    } else {
        perror("readlink failed");
        return 1;
    }
}
