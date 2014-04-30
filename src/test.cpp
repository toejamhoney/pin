#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int add2( int x , int y ){
    return x + y ; }


int main(){
    printf( "\ngood day\n" );
    int r = add2( 2, 3 );
    printf( "address of r=%p\n" , &r );
    printf( "x+y=%i\n", r );
    printf( "good by\n" );

    int wait_status;
    int pid = fork();
    if(pid==0)
    {
        printf("Child lives\n");
        FILE * F = fopen("testchild.out", "w");
        fclose(F);
    }
    else
    {
        FILE * F = fopen( "test.out", "w");
        fclose( F );
        printf("Parent Waits...");
        wait(&wait_status);
        printf("Parent done\n");
    }
}
    
