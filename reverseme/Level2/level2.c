#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(void) {
    const char *password = "delabere";
    char tmp[24];
    char str[9];
    int idx;
    int pos;

    printf("Please enter key: ");
    if (scanf("%23s", tmp) != 1 || tmp[1] != '0' || tmp[0] != '0'){
        printf("Nope.\n");
        return (0);
    }
    fflush(stdin);
    memset(str, 0, sizeof(str));
    str[0] = 'd';
    idx = 2;
    pos = 1;
    while (pos < 8 && idx + 3 <= (int)strlen(tmp))
    {
        str[pos++] = atoi((char[4]){ tmp[idx], tmp[idx+1], tmp[idx+2], '\0'});
        idx += 3;
    }
    printf("%s\n", strcmp(password, str) ? "Nope." : "Good job.");
    return (0);
}
