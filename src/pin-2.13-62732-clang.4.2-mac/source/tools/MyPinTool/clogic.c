/*
  
  Here is an implementation that seems to work based on our discussions this a.m.  think of the cnode structure as sort of a smart bookmark that advances when the next transition arises and goes away when expires.  Some improvements to the code should be easy for you.  To make things simple we imagine the following:  all transitions are tucked into a single array called 'normal_form' in addition there is a 'exp_start' array that give start positions in 'normal_form' where subsequences starts and goes to the entry '-1' the expression is satistified if the smart book-mark advances to index in 'exp_sats' array.  'exp_gp' and 'exp_var' encode the Pattern number and variant number used for output.

  todo:  Write a python function that takes as input a list of temporal subsequences organized by pattern and variant and creates the five variables: 'normal_form', 'exp_start', 'exp_sats', 'exp_gp', and 'exp_var'.

  todo:  Write a python function that takes as input a list of temporal subsequences and produces a 'fast_push_code' function (as below).  
  
  todo:  Below I coded an test comparing the push_code function with the fast_push_code but for this example there is no distinguishable difference.  Determine the type of sparsity conditions for sub-sequence matching for which "fast_push_code" out performs "push_code" and present in a graph of runtime performance.

 */

#include "stdlib.h"
#include "stdio.h"
#include <sys/time.h>


struct cnode {
    int step;
    int clock;
    struct cnode * next ;
    };

struct cnode * new_clause ( int clock ){
    struct cnode * X = (struct cnode *)malloc( sizeof( struct cnode  ));
    X->clock = clock;
    X->step=0;
    X->next = NULL;
    return X;}

void delete_clause( struct cnode * x ){
    free( x );}

struct cnode * get_tail( struct cnode * Y ){
    struct cnode * rv = Y;
    while ( rv->next ){
        rv = rv->next;
    }
    return rv;
}

struct cnode ** initalize_cnode_array( int size ){
    int k;
    struct cnode ** RV = (struct cnode **)malloc( sizeof( struct cnode * )*size );
    for ( k = 0; k < size ; k ++ ){
	*(RV + k ) = NULL;}
    return RV;}

/* 
   suppose that the sub-sequences of interest are :
   Pattern 1 variant 1:  1->2->3      
   Pattern 1 variant 2:  1->5->3
   Pattern 2 variant 1:  2->1->7->9
   Pattern 2 variant 2:  2->2->7

   int v0_0[3] = {1,2,3};
   int v0_1[3] = {1,5,3};
   int * v0[2] = {v0_0, v0_1};
   int v1_0[4] = {2,1,7,9};
   int v1_1[3] = {2,2,7};
   int * v1[2] = {v1_0, v1_1};
   int ** standing_logic_queries[2] = {v0, v1};

*/

int normal_form[17] = {1,2,3,-1,1,5,3,-1,2,1,7,9,-1,2,2,7,-1};
int exp_start[4] = {0,4,8,13};
int exp_sats[4] = {3,7,12,16};
int exp_gp[4] = {1,1,2,2};
int exp_var[4] = {1,2,1,2};


int push_code( int clock, int code, struct cnode ** SAT, int num, int window_size, int * normal_form, int * exp_start, int * exp_sats, int * exp_gp , int * exp_var, int * data){
    struct cnode * t;
    /* phase one: remove expired queries */
    int k = 0;
    for (k = 0; k < num ; k++){
	while (( SAT[k] ) && ( ((SAT[k]->clock + window_size)< clock ) || (*(exp_start + k) + SAT[k]->step) >= *(exp_sats + k ))){
	    t = SAT[k]->next;	    
	    delete_clause( SAT[k] );
	    SAT[k] = t;}}
    /* phase two: add new queries */
    int e = 0;
    for ( k = 0 ; k < num ; k++ )
    {
	    if ( code == *(normal_form + *(exp_start + k)))
        {
            if (!SAT[k] )
            {
                 SAT[k] = new_clause( clock );
            }
            else
            {
                get_tail( SAT[k] )->next = new_clause( clock );
            }
        }
	    t = SAT[k];
        while( t )
        {
            if (*(normal_form + *(exp_start + k) + t->step) == code )
            {
                t->step += 1;
            }
            if ( (*(exp_start + k) + t->step) == *(exp_sats + k ))
            {
                printf( "Pattern [%i] variant [%i] is satisfied in [ %i, %i ]", *(exp_gp + k), *(exp_var + k ), clock-window_size , clock +1  );
                printf( " data@%i:", clock-window_size + 1 );
                for ( e = 0 ; e < window_size +1; e ++ )
                {
                    printf( " %i", data[clock-window_size + e ] );
                }
                printf( "\n" );
            }
            t = t->next ; 
        }
    }
}


/* 
   suppose that the sub-sequences of interest are :
   Pattern 1 variant 1:  1->2->3      
   Pattern 1 variant 2:  1->5->3
   Pattern 2 variant 1:  2->1->7->9
   Pattern 2 variant 2:  2->2->7
*/

#define REPORT(K) if((*(exp_start+K)+t->step)==*(exp_sats+K)){printf("Pattern [%i] variant [%i] is satisfied in [ %i, %i ]",*(exp_gp+K),*(exp_var+K),clock-window_size,clock+1);printf(" data@%i:",clock-window_size+1);int e;for(e=0;e<window_size+1;e++){printf(" %i",data[clock-window_size+e]);}printf( "\n" );}
#define PUSH2(K, T) if(SAT[K]){get_tail(SAT[K])->next=new_clause(T);get_tail(SAT[K])->step+=1;}else{SAT[K]=new_clause(T);SAT[K]->step+=1;}
#define TRANS(K, S) if(SAT[K]){t=SAT[K];while(t){if(t->step==S){t->step+=1;}REPORT(K) t=t->next;}}


int fast_push_code ( int clock, int code, struct cnode ** SAT, int num, int window_size, int * normal_form, int * exp_start, int * exp_sats, int * exp_gp , int * exp_var, int * data){
    /*

      A fast version would only compute the needed steps (rather then iterating over the num of entries in the normal form.
      In order to do so you will need to invert the map of symbols to updates needed, this is sketched below.
      
     */

    struct cnode * t;
    /* phase one: remove expired queries - no differnet from function above. */
    int k = 0;
    for (k = 0; k < num ; k++){
        while (( SAT[k] ) && ( ((SAT[k]->clock + window_size)< clock ) || (*(exp_start + k) + SAT[k]->step) >= *(exp_sats + k ))){
            t = SAT[k]->next;	    
            delete_clause( SAT[k] );
            SAT[k] = t;}
    }
    
    /* phase two:  takes advantage of sparse transitions (if they are sparse) */
    switch ( code ){
    case 1:
        /* address v0_0 */
        k = 0;
        if ( SAT[k] ){
            get_tail(SAT[k])->next = new_clause( clock );
            get_tail(SAT[k])->step += 1;}
        else{
            SAT[k] = new_clause( clock );
            SAT[k]->step += 1;} // from now on this pattern will be encoded by PUSH2 macro
        /* address v0_1 */	//k = 1;
        PUSH2(1,clock);
        /* address v2_1 */
        TRANS(2,1);
        /* address v2_2 */
        break;;
    case 2:
        /* address v0_0 */
        TRANS(0,1);
        /* address v0_1 */
        /* address v2_1 */
        PUSH2(2,clock);
        /* address v2_2 */ //	k = 3;
        TRANS(3,1);
        PUSH2(3,clock);
        break;;
    case 3:
        TRANS(0,2);
        TRANS(1,2);	    
        break;;
    case 5:
        TRANS(1,1);
        break;;
    case 7:
        TRANS(2,2);
        TRANS(3,2);
        break;;	
    case 9:
        TRANS(2,3);
        break;;
    default :
        break;
    }
	
}

int stream_query( int * data, int data_size ,int test ){
    int k ; // counter
    int window_size = 4;
    int cur = -1;

    struct cnode ** SAT;
    if (test == 0 )
    {
	    SAT = initalize_cnode_array( 4 );
        printf( "stream query approach one\n" );
        for ( k = 0; k < data_size ; k ++ ){
            cur = data[k] ;
            push_code( k, cur, SAT, 4, window_size-1,  normal_form, exp_start, exp_sats, exp_gp, exp_var, data);
        }
        free( SAT);
    }

    if (test == 1 )
    {
        SAT = initalize_cnode_array( 4 );    
        printf( "stream query approach two - way more optimized \n" );
        for ( k = 0; k < data_size ; k ++ ){
            cur = data[k] ;
            fast_push_code( k, cur, SAT, 4, window_size-1,  normal_form, exp_start, exp_sats, exp_gp, exp_var, data);
        }
        free( SAT );
    }
}


int main(){
    printf( "starting code\n" ); 
    int test = 1;
    int data[2048] = {1,6,2,5,5,9,5,6,2,3,6,4,6,3,1,0,3,3,7,9,8,3,7,2,4,0,1,2,3,7,0,7,4,7,4,3,8,3,8,1,5,4,7,1,4,9,9,0,4,3,1,6,4,9,2,2,8,3,3,1,5,7,6,2,9,4,0,8,1,2,3,9,6,0,9,4,4,8,4,8,2,7,0,0,1,5,5,3,3,7,8,9,0,7,3,6,9,2,1,6,0,1,3,7,1,6,2,7,3,7,3,3,6,4,3,8,2,7,0,3,5,1,4,7,1,8,0,4,6,6,0,4,6,6,9,4,1,4,3,2,1,4,4,3,1,6,3,0,2,1,3,7,0,1,0,3,4,1,8,3,9,2,8,0,6,9,6,1,7,5,9,1,6,1,9,8,7,5,7,7,1,4,4,0,3,6,8,1,6,9,4,9,7,8,5,6,8,6,2,2,8,8,0,8,4,9,6,4,8,8,5,4,7,4,8,1,2,6,4,7,5,1,9,2,3,0,6,1,4,5,6,2,3,0,1,0,3,5,6,5,3,2,7,8,6,7,9,1,2,3,5,7,5,1,9,3,8,4,2,9,2,9,2,9,0,2,1,5,0,1,8,3,1,4,2,8,7,3,0,3,5,5,9,8,3,1,3,7,7,1,8,0,9,0,2,8,2,1,0,9,9,7,6,2,0,3,0,3,6,2,0,8,4,5,4,8,1,7,7,9,3,4,8,1,5,3,9,8,2,5,3,9,8,2,0,0,9,6,1,0,7,2,9,9,5,9,0,4,8,6,0,1,3,3,9,8,4,1,4,3,2,5,1,6,5,4,3,2,9,1,5,3,6,2,3,9,8,6,6,5,4,4,1,3,2,3,4,0,5,6,1,0,7,2,7,1,4,2,4,9,1,3,4,3,8,6,1,8,5,0,9,4,5,9,9,6,2,0,6,5,5,9,2,0,7,6,9,1,0,7,4,7,2,5,0,9,5,8,1,2,9,3,9,7,0,4,9,5,2,5,1,2,7,9,0,7,6,5,5,9,5,0,8,0,3,4,4,9,8,4,4,4,0,3,4,6,6,6,9,5,0,9,6,8,5,8,5,7,2,4,4,7,9,5,6,6,4,1,3,3,4,0,1,7,0,8,0,5,5,9,5,8,4,3,2,7,2,2,6,0,4,7,3,1,3,9,5,3,9,1,3,0,8,4,2,6,3,5,7,2,1,4,6,8,1,6,6,1,7,4,2,3,8,9,9,4,4,6,6,3,2,9,0,3,4,6,2,4,9,3,0,2,1,1,1,4,6,6,3,3,8,7,6,0,2,3,2,6,5,8,6,8,4,7,4,9,7,3,8,6,1,4,5,1,4,5,5,6,6,5,8,5,6,8,2,2,2,2,3,8,5,5,8,2,3,4,1,4,2,5,3,4,4,3,1,8,5,8,5,1,2,0,5,4,8,8,5,2,1,6,9,9,4,2,7,1,1,3,3,3,8,4,6,3,6,9,6,1,2,4,5,1,2,5,6,5,8,0,0,1,1,4,5,5,4,4,0,8,6,6,8,3,7,0,1,7,7,0,2,9,7,7,4,1,9,2,9,8,7,6,1,1,2,3,5,1,0,9,3,2,5,6,6,1,1,5,0,8,3,0,0,5,3,1,7,8,6,6,3,1,2,6,1,1,4,9,2,1,2,5,1,1,5,9,2,9,8,7,7,9,0,1,3,7,5,3,6,4,5,4,5,1,7,3,9,4,1,2,4,2,4,6,1,5,9,6,1,4,5,3,4,7,6,3,0,1,6,9,5,8,4,0,8,3,6,8,1,0,3,2,1,3,1,0,4,1,4,2,8,0,7,2,7,9,8,0,7,2,0,6,1,3,6,8,7,9,5,3,5,3,1,7,4,6,7,6,0,3,6,1,9,2,8,3,3,4,4,3,8,1,4,8,4,1,5,2,5,9,0,3,0,9,6,4,5,3,3,3,6,1,7,3,1,3,2,6,1,7,4,0,2,8,3,9,0,2,1,5,3,1,6,7,6,9,8,7,6,7,5,6,8,7,0,3,2,6,2,1,2,8,0,2,4,9,3,5,8,5,6,1,4,6,2,3,7,4,7,6,9,7,5,7,1,0,6,3,8,8,0,8,7,6,4,8,4,0,1,7,0,4,1,1,0,6,5,9,3,9,6,2,1,7,3,2,0,7,4,4,6,6,5,5,4,1,7,2,9,8,2,4,7,8,5,1,6,4,8,9,7,3,2,6,2,2,1,1,5,8,4,0,4,5,3,8,5,2,2,2,0,5,9,6,7,0,6,0,9,0,1,5,1,1,4,5,2,3,5,2,0,9,3,4,5,3,4,1,0,9,1,2,0,7,8,5,3,6,7,4,5,1,3,8,0,1,1,4,7,9,9,7,9,3,9,5,8,2,5,9,8,7,2,2,7,6,9,3,3,9,1,9,8,9,9,2,6,5,3,8,1,6,2,8,4,6,6,6,7,6,6,4,2,8,8,0,8,2,3,7,4,7,2,3,3,0,3,0,4,6,6,9,4,9,7,7,0,8,4,2,7,2,6,3,5,3,0,4,5,4,5,3,6,9,5,2,3,8,9,8,9,1,0,9,3,6,3,2,8,2,6,0,1,7,1,5,2,5,2,6,4,8,0,7,4,0,7,8,1,4,0,0,4,6,3,0,3,7,7,8,4,2,2,3,5,4,3,0,0,7,7,0,3,0,0,1,7,6,2,6,2,6,3,0,8,4,6,9,4,3,3,1,5,1,1,2,2,8,2,4,1,7,7,7,3,9,9,1,3,3,0,1,2,8,1,1,6,1,0,0,7,9,5,6,4,7,6,8,9,7,7,7,0,4,6,0,1,6,3,3,6,8,5,7,4,4,3,2,6,9,4,0,5,4,7,0,5,5,0,2,4,3,2,2,3,7,0,9,2,9,4,9,6,5,7,1,9,3,4,4,2,7,7,5,1,1,2,5,7,1,6,7,8,9,9,5,9,1,4,6,0,0,1,7,0,7,7,3,9,2,6,5,6,6,8,2,6,7,1,2,4,0,6,5,6,1,0,1,6,6,7,6,8,8,8,3,3,3,9,2,0,1,0,4,3,8,3,9,1,7,4,9,2,0,5,8,4,6,6,2,7,4,6,7,6,8,5,3,3,0,4,5,5,5,4,4,8,5,6,0,7,4,7,3,6,7,9,8,3,3,1,3,7,5,0,5,4,0,8,3,2,9,4,2,6,2,8,4,1,7,8,8,9,5,0,5,8,5,5,1,1,2,3,7,8,6,4,8,1,3,3,9,6,3,4,9,7,3,3,0,3,9,3,3,5,1,0,2,7,8,5,5,7,0,2,6,5,0,7,1,9,9,0,9,5,7,4,5,7,3,4,0,5,8,5,1,2,8,7,2,7,4,5,8,8,0,4,2,2,1,8,6,4,0,4,5,6,9,2,2,6,5,8,9,8,0,3,4,7,2,2,6,4,5,6,2,9,8,5,7,7,2,8,6,6,1,2,4,4,5,3,6,5,3,9,4,8,0,4,4,5,4,5,2,3,5,0,3,4,6,3,8,5,3,5,6,3,8,1,9,4,2,2,1,3,9,0,6,9,9,0,4,4,6,4,2,7,0,1,2,5,1,9,6,9,8,1,0,1,5,9,0,1,7,7,6,6,2,8,9,9,3,8,9,6,5,1,4,0,0,1,6,8,8,9,5,1,3,3,8,1,9,2,0,5,3,1,8,3,8,5,5,7,5,0,8,7,1,7,2,4,7,6,0,2,2,2,9,7,5,7,5,2,5,6,3,6,4,8,0,9,4,5,1,3,3,4,5,7,4,6,5,3,4,5,4,5,7,1,9,5,6,1,8,0,9,6,2,4,7,6,8,6,2,6,3,1,6,1,8,2,8,3,4,2,7,2,9,5,7,1,4,4,9,7,6,1,1,2,1,9,7,2,8,3,5,7,7,8,1,2,9,9,0,8,9,1,3,0,0,2,2,9,1,1,5,4,8,1,1,0,7,7,7,1,3,9,5,2,8,5,7,8,8,6,8,8,6,9,1,2,9,1,1,7,8,5,0,3,9,7,6,6,3,7,3,2,9,8,3,3,8,2,3,3,7,4,6,6,4,0,0,4,6,1,1,3,3,8,7,0,4,9,5,6,2,1,7,0,4,5,4,4,1,0,6,0,7,0,6,7,1,9,1,2,3,9,0,2,2,5,1,8,2,3,4,5,7,7,8,2,2,6,2,7,5,3,8,2,3,2,7,7,9,6,0,4,5,8,9,5,4,2,9,0,1,2,7,2,8,6,9,6,0,7,5,4,4,3,8,1,0,9,5,2,3,5,7,8,6,3,3,7,6,4,9,9,4,7,5,8,2,6,7,4,3,3,3,0,6,8,5,4,4,7,0,7,8,1,3,9,6,5,6,1,5,7,5,8,8,5,9,9,5,4,7,8,1,9,0,6,8,7,5,5,7,4,9,8,9,0,2,3,9,5,1,0,9,6,4,2,8,6,7,2,8,3,8,0,7,8,3,3,5,0,2,3,9,1,6,8,9,6,4,2,1,3,3,7,7,3,3,6,6,1,0,7,7,0};

    struct timeval startA, startB, finA, finB;
    int k = 0;
    int LIM = 1;
    gettimeofday(&startA, NULL);
    for ( k = 0; k < LIM ; k++ ){
        stream_query( data, 2048, test ); 
    }
    gettimeofday(&finA, NULL);
    long long elapsedA = (finA.tv_sec - startA.tv_sec) * 1000000LL + finA.tv_usec - startA.tv_usec;
    printf( "c fast: %lld\n",elapsedA);
}
	
	
