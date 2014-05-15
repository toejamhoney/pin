#include <stdio.h>

int main(int argc, char** argv){
    const char* X = "STARTGLOBAL\n";
    printf("START");
    printf("%s", X);
    printf("STARTN\n");
    printf("START\nS");
    printf("%p\n", X);
    return 0;
}
