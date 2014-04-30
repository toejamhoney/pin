"""

API PIN TOOL

"""
import pprint
import sys
import getopt


def study_wine_declaration( input_file ):
    routine_data = [];
    fin = open( input_file );
    cur_routine=None;
    record = 0;
    for line in fin:
        V = line.split();
        if ( len( V ) > 3 ):
            routine_data.append( [ V[2], " ".join(V[4:]) ] );
        else:
            if 0 == 1:
                print "ODD LINE: %s"%line
    return routine_data;

def study_parameters( V ):
    retval = [];
    for v in V:
        function = v[1];
        function_stub, _, function_para = function.partition('(');
        retval.append( [ v[0], function_stub, function_para.replace( "(", "" ).replace(")","").replace(";","").split( "," ) ] );
    return retval;


PREHOOK="""
VOID Before_%s(CHAR * name, %s) 
{

    /* 
       
       MBMC - Tracer PRE-HOOK (C) CMU SEI 2013 Will Casey, Jeff Gennari, Jose Morales. 
       Fuction: %s 
       Input parameters: %s

     */

    int j; 
    TraceFile << setw(3) << call_stack_depth << ":";
    for ( j = 0 ; j < call_stack_depth ; j ++ ){
        TraceFile << " ";}
//    call_stack_depth++;
    TraceFile << "IN: " << name << " (" << %s << ")" << dec << endl;
    %s
}
"""
POSTHOOK="""
VOID After_%s(CHAR * name, ADDRINT ret)
{

    /* 

       MBMC - Tracer POST-HOOK (C) CMU SEI 2013: Will Casey, Jeff Gennari, Jose Morales, Evan Wright, Jono Spring. 
                                   NYU CIMS 2013: Bud Mishra, Thomson Nguyen
       Fuction: %s 
       Input parameters: %s

     */

    int j; 
    TraceFile << setw(3) << call_stack_depth << ":";
    for ( j = 0 ; j < call_stack_depth ; j ++ ){
        TraceFile << " ";}
//    call_stack_depth--;
    %s
    TraceFile << "OUT: " << name << "\t" << hex << ret << dec << endl;
}
"""

INJECT_INST_1="""
                RTN_InsertCall(allocRtn, IPOINT_BEFORE, (AFUNPTR)Before_%s,
                               IARG_ADDRINT, "%s","""

INJECT_INST_2="""
                               IARG_FUNCARG_ENTRYPOINT_VALUE, %i,"""
INJECT_INST_3="""
                               IARG_END);
"""
INJECT_INST_4="""
                RTN_InsertCall(allocRtn, IPOINT_AFTER, (AFUNPTR)After_%s,
                               IARG_ADDRINT, "%s", 
                               IARG_FUNCRET_EXITPOINT_VALUE,
                               IARG_END);
"""

def gen_hook_calls( W , extra=None):
    retval = []; functions_matched = {}; GLOBALS = ''; functions_listed = {};
    for function_rv, function_stub, function_param in W:
        # TODO render args ...
        if not function_stub in functions_listed.keys():
            functions_listed[ function_stub ] =0 ;
        functions_listed[ function_stub ] += 1  ; # TODO error detection technqiue to be added (all values should be 1 ).
        param_ns = []; vals=[];
        NEWPRESTUFF = "";
        NEWPOSTSTUFF= "";
        GLOBALSTUFF ="";
        if extra and (function_stub in extra.keys()):
            if ( 'pre' in extra[function_stub].keys() ):
                NEWPRESTUFF = extra[function_stub]['pre']
            if ( 'post' in extra[function_stub].keys() ):
                NEWPOSTSTUFF = extra[function_stub]['post']
            if ( 'global' in extra[function_stub].keys() ):
                GLOBALSTUFF = extra[function_stub]['global'];
            functions_matched[function_stub ] = 1;
        c = 0;
        for v in function_param:
            #param_ns.append( "%s X%s "%("WINDOWS::"+v.strip().split()[0],c));
            param_ns.append( "%s X%s "%("void *",c));
            vals.append( "X%s"%c );
            c=c+1;
        print_string = "hex " + "<< \",\"".join ( [ "<<%s"%v for v in vals] )
        pre_hook = PREHOOK%( function_stub, ",".join( param_ns ), function_stub, ",".join ( function_param ), print_string , NEWPRESTUFF ) 
        post_hook = POSTHOOK%(function_stub  , function_stub, ",".join ( function_param ), NEWPOSTSTUFF )
        inject_pre = INJECT_INST_1%(function_stub, function_stub) + "".join( [ INJECT_INST_2%k for k in range( len( function_param ))] ) + INJECT_INST_3; 
        inject_post = INJECT_INST_4%(function_stub, function_stub)
        retval.append( [ pre_hook, post_hook, inject_pre, inject_post ] );
        GLOBALS += GLOBALSTUFF;
    return [retval, GLOBALS];

def study_enhancments( file_path ):
    RV = {};
    f = open( file_path, "r" );
    T = f.read();
    RV = eval( T );
    f.close();
    return RV;

def process( arg , extra=None ):
    X = study_wine_declaration( arg );
    Y = None;
    if ( extra  ):
        Y = study_enhancments ( extra );
    V = study_parameters( X )
    # EGLOBALS inclues precompiler directives and compilable c code.
    W,EGLOBALS = gen_hook_calls( V , extra = Y );
    A=[]; B=[]; 
    for a,b,c,d in W:
        A.append( a + b );
        B.append( c + d );
    print TEMPLATE_p1 + EGLOBALS + TEMPLATE_p1a + "".join( A ) + TEMPLATE_p2 + "".join( B ) + TEMPLATE_p3;
    #pprint.pprint ( V );

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options 
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    # process arguments
    if ( len( args ) == 1 ):
        process(args[0]) # process() is defined elsewhere
    elif ( len( args ) == 2 ):
        process( args[0], extra=args[1] );
    else:
        print "pass with one or two args" 
        sys.exti( 4 );
        


from RTN_byname_target import *;


if __name__ == "__main__":
    main()
