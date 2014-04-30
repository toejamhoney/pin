#include <stdio.h>

int main()
{
    int ret_val = 0;
    
    /* Open a file */
    FILE* test_file = fopen("helloworld.txt", "w+b");
    if(!test_file)
    {
        perror("fopen");
        ret_val = -1;
    }
   
    /* Close a file */
    if(ret_val == 0)
    {
        if(fclose(test_file) != 0)
        {
            perror("fclose");
            ret_val = -2;
        }
    }

    return ret_val;
}
