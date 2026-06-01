#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(void) {
    char *password = "delabere";
    char tmp[24];
    printf("Please enter key: ");
    if (scanf("%23s", tmp) == 1){
        if (tmp[1] == '0')
        {
            if (tmp[0] == '0')
            {
                fflush(stdin);
                char str[9];
                memset(str, 0, 9);
                str[0] = 'd';
                int idx = 2;
                char letter[4];
                while (strlen(str) < 8 && idx < strlen(tmp))
                {
                    int i = 0;
                    while (i < 3) {
                        letter[i] = tmp[idx];
                        i++;
                        idx++;
                    }
                    letter[3] = '\0';
                    str[strlen(str)] = atoi(letter);
                }
                if (strcmp(password, str) == 0) {
                    printf("Good job.\n");
                    return (0);
                }
            }
        }
    }
    printf("Nope.\n");
    return (0);
}
