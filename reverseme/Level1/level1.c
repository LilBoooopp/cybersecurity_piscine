#include <stdio.h>
#include <string.h>

int main(void)
{
    const char *password = "__stack_check";
    char tmp[100];
    printf("Please enter key: ");
    scanf("%s", tmp);
    if (strcmp(tmp, password) == 0) {
        printf("Good job.\n");
    } else {
        printf("Nope.\n");
    }
    return (0);
}
