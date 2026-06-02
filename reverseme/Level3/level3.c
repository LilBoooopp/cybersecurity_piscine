#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(void)
{
    const char *password = "42********";
    char str[9];
    char tmp[24];
    int idx;
    int pos;
    printf("Please enter key: ");
    if (scanf("%23s", tmp) != 1 || tmp[1] != '2' || tmp[0] != '4') {
        printf("Nope.");
        return (0);
    }
    fflush(stdin);
    memset(str, 0, sizeof(str));
    str[0] = '*';
    idx = 2;
    pos = 1;
    while (pos < 8 && idx + 3 <= (int)strlen(tmp))
    {
        str[pos++] = atoi((char[4]){ tmp[idx], tmp[idx+1], tmp[idx+2], '\0'});
        idx += 3;
    }
    switch (strcmp(password, str)) {
        case (-2):
            printf("Nope.");
            break;
        case (-1):
            printf("Nope.");
            break;
        case (0):
            printf("Good job.");
            break;
        case (1):
            printf("Nope.");
            break;
        case (2):
            printf("Nope.");
            break;
        case (3):
            printf("Nope.");
            break;
        case (4):
            printf("Nope.");
            break;
        case (5):
            printf("Nope.");
            break;
        case (115):
            printf("Nope.");
            break;
        default:
            printf("Nope.");
    }
    return (0);
    
}

