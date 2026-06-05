#include <stdio.h>
#include <string.h>
#include <stdlib.h>
void wt(){
  printf("********");
}
void nice(){
  printf("nice");
}
void try(){
  printf("try");
}

void but(){
  printf("but");
}

void this(){
  printf("this");
}

void it(){
  printf("it");
}

void not(){
  printf("not");
}

void that(){
  printf("that");
}

void easy(){
  printf("easy");
}

void ___syscall_malloc() {
    printf("Nope.");
}

void ____syscall_malloc() {
    printf("Good job.");
}

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
        case (-1):
        case (0):
            ____syscall_malloc();
            break;
        case (1):
        case (2):
        case (3):
        case (4):
        case (5):
        case (115):
        default:
            ___syscall_malloc();
    }
    return (0);
    
}

