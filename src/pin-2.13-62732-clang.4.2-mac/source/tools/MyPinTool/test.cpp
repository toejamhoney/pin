#include <stdlib.h>
#include <stdio.h>
#ifdef _WIN32
    #include <io.h>
#else
    #include <unistd.h>
    #include <sys/wait.h>
#endif

int add2( int x , int y ){
    return x + y ; }


int main(){
    printf( "\ngood day\n" );
    int r = add2( 2, 3 );
    printf( "address of r=%p\n" , &r );
    printf( "x+y=%i\n", r );
    printf( "good by\n" );

    #ifdef _WIN32
        FILE * F = fopen("test_fopen.txt", "w");
        fprintf(F, "line written by test.cpp\n");
        fclose(F);
        printf("Closed file\n");
    #else
        int wait_status;
        int pid = fork();
        if(pid==0)
        {
            printf("Child lives\n");
            FILE * F = fopen("testchild.txt", "w");
            fprintf(F, "line written by test.cpp child\n");
            fclose(F);
            printf("Child done\n");
        }
        else
        {
            FILE * F = fopen( "testparent.txt", "w");
            fprintf(F, "line written by test.cpp parent\n");
            fclose( F );
            printf("Parent Waits...");
            wait(&wait_status);
            printf("Parent done\n");
        }
    #endif
}
    
