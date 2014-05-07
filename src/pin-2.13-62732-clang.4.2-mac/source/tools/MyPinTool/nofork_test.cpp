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

int main(int argc, char** argv){
    
    printf( "\ngood day\n" );
    int r = add2( 2, 3 );
    printf( "address of r=%p\n" , &r );
    printf( "x+y=%i\n", r );
    printf( "good by\n" );

    FILE * F = fopen( "testparent.txt", "w");
    printf("Parent opens");
    fprintf(F, "line written by test.cpp parent\n");
    fclose( F );

    return 0;
}
    
