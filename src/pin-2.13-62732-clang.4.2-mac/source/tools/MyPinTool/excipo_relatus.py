"""

    Excipo ~ intercept  { -> }  Relatus ~ report 

This is our PIN TOOL for api tracing. (C) W.Casey, M.Appel

Usage: excipo_relatus X.cpp 


"""
import pprint
import sys
import getopt
import templates
import re

TEMPLATE_p1=templates.TEMPLATE_p1
TEMPLATE_p1a=templates.TEMPLATE_p1a
TEMPLATE_p2=templates.TEMPLATE_p2
TEMPLATE_p3=templates.TEMPLATE_p3

PREHOOK=templates.PREHOOK
POSTHOOK=templates.POSTHOOK

INJECT_INST_1=templates.INJECT_INST_1
INJECT_INST_2=templates.INJECT_INST_2
INJECT_INST_3=templates.INJECT_INST_3
INJECT_INST_4=templates.INJECT_INST_4

SEQ_APP=templates.SEQUENCE_APPENDIX

MAX_FLAG_LEN = 1

def study_c_declaration( input_file ):
    routine_data = [];
    fin = open( input_file );
    cur_routine=None;
    record = 0;
    for line in fin:
        dec_ret_type, ws, dec_func_name_args = line.rstrip().partition(' ')
        if dec_func_name_args:
            routine_data.append( [dec_ret_type, dec_func_name_args] )
        else:
            if 0 == 1:
                print "ODD LINE: %s"%line
    return routine_data;

def study_parameters( V ):
    retval = [];
    try:
        for v in V:
            function = v[1];
            function_stub, _, function_para = function.partition('(');
            retval.append( [ v[0], function_stub, function_para.replace( "(", "" ).replace(")","").replace(";","").split( "," ) ] );
    except TypeError:
        pass
    return retval;

def gen_hook_calls( W , extra=None):
    global MAX_FLAG_LEN
    retval = []; functions_matched = {}; GLOBALS = ''; functions_listed = {}; flag_check = {};
    for function_rv, function_stub, function_param in W:
        # TODO render args ...
        if not function_stub in functions_listed.keys():
            functions_listed[ function_stub ] =0 ;
        functions_listed[ function_stub ] += 1  ; # TODO error detection technqiue to be added (all values should be 1 ).
        param_ns = []; vals=[];
        NEWPRESTUFF = "";
        NEWPOSTSTUFF= "";
        GLOBALSTUFF ="";
        PREFLAG = 0
        POSTFLAG = 0
        PRE_SEQ_CODE = ""
        POST_SEQ_CODE = ""
        if extra and (function_stub in extra.keys()):
            if ( 'pre' in extra[function_stub].keys() ):
                NEWPRESTUFF = extra[function_stub]['pre']
            if ( 'post' in extra[function_stub].keys() ):
                NEWPOSTSTUFF = extra[function_stub]['post']
            if ( 'global' in extra[function_stub].keys() ):
                GLOBALSTUFF = extra[function_stub]['global'];
            preflag = extra[function_stub].get('preflag')
            postflag = extra[function_stub].get('postflag')
            if preflag and postflag:
                if preflag not in flag_check:
                    flag_check[preflag]=0
                else:
                    print>>sys.stderr, "Duplicate flag detected: " + str(preflag)
                if postflag not in flag_check:
                    flag_check[postflag]=0
                else:
                    print>>sys.stderr, "Duplicate flag detected: " + str(postflag)
                flag_check[preflag] += 1
                flag_check[postflag] += 1
                PREFLAG = str(preflag)
                PRE_SEQ_CODE = SEQ_APP.format(flag=PREFLAG, flag_len=MAX_FLAG_LEN)
                POSTFLAG = str(postflag)
                POST_SEQ_CODE = SEQ_APP.format(flag=POSTFLAG, flag_len=MAX_FLAG_LEN)
            functions_matched[function_stub] = 1;
        c = 0;
        for v in function_param:
            #param_ns.append( "%s X%s "%("WINDOWS::"+v.strip().split()[0],c));
            param_ns.append( "%s X%s "%("void *",c));
            vals.append( "X%s"%c );
            c=c+1;
        print_string = "hex " + "<< \",\"".join ( [ "<<%s"%v for v in vals] )
        pre_hook = PREHOOK%( function_stub, ",".join( param_ns ), function_stub, ",".join ( function_param ), print_string , NEWPRESTUFF, PRE_SEQ_CODE) 
        post_hook = POSTHOOK%(function_stub  , function_stub, ",".join ( function_param ), NEWPOSTSTUFF, POST_SEQ_CODE)
        inject_pre = INJECT_INST_1%(function_stub, function_stub, function_stub) + "".join( [ INJECT_INST_2%k for k in range( len( function_param ))] ) + INJECT_INST_3; 
        inject_post = INJECT_INST_4%(function_stub, function_stub, function_stub)
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

def get_regex(line):
    try:
        re.compile(line)
    except re.error:
        sys.stderr.write("Invalid regex in extras input.SEQUENCES: " + line + '\n')
        return ""
    else:
        return line

def get_suffix(line):
    if line.isdigit():
        return line
    else:
        sys.stderr.write("Invalid suffix length in extras input.SEQUENCES: " + line + '\n')
        return ""

def get_code(start, lines):
    stop = len(lines)
    code = ""
    for idx in range(start, stop):
        if lines[idx].lower().startswith('else:') or lines[idx].lower().startswith('sequence:'):
            return code
        code = '\n\t'.join( [code, lines[idx]] )
    return code

def create_sequences(seq_lines):
    global MAX_FLAG_LEN
    tuples = []
    template = templates.SEQ_SUFFIX_SEARCH
    state = 0
        
    for idx, line in enumerate(seq_lines):
        if line.startswith('//') or not line or line.startswith(' '):
            continue
        elif line.startswith('sequence:'):
            state = 1
        elif state == 1:
            re = get_regex(seq_lines[idx])
            tuples.append( [re, '', '', ''] )
            state = 2
        elif state == 2:
            suff_len = get_suffix(seq_lines[idx])
            tuples[-1][1] = str(int(suff_len) * MAX_FLAG_LEN)
            state = 3
        elif state == 3:
            true_code = get_code(idx, seq_lines)
            tuples[-1][2] = true_code
            state = 4
        elif line.startswith('else:'):
            if state == 4:
                false_code = get_code(idx+1, seq_lines)
                tuples[-1][3] = false_code
                state = 0
            else:
                sys.stderr.write('Dangling else in extras input SEQUENCES\n')
        
    result = ''
    for if_strings in tuples:
        result += template%tuple(if_strings)
        
    return result

def get_longest_flag(callouts):
    global MAX_FLAG_LEN
    for func_name in callouts:
        callout = callouts.get(func_name)
        longest = max( len(str(callout.get('preflag'))), len(str(callout.get('postflag'))) )
        if longest > MAX_FLAG_LEN:
            MAX_FLAG_LEN = longest
    MAX_FLAG_LEN += 1
    print MAX_FLAG_LEN

def process( arg, rtn=None, ins=None, img=None, extra=None, split_files=True ):
    global MAX_FLAG_LEN
    argstub = arg.partition('.')[0]
    X = None;
    if rtn:
        X = study_c_declaration( rtn );

    try:
        extras = __import__(extra)
    except ImportError as err:
        seq_checks = ""
        Y = None
        print repr(err)
    except TypeError as err:
        if not extra:
            seq_checks = ""
            Y = None
        else:
            print repr(err)
            sys.exit(1)
    else:
        Y = extras.CALLOUTS
        get_longest_flag(Y)
        if MAX_FLAG_LEN > 24:
            sys.stderr.write('Callout flag exceeds 24 character limit.\n')
            sys.exit(-1)
        try:
            seq_checks = create_sequences(extras.SEQUENCES.split('\n'))
        except AttributeError:
            seq_checks = ""

    V = study_parameters( X )
    # EGLOBALS inclues precompiler directives and compilable c code.
    W,EGLOBALS = gen_hook_calls( V , extra = Y );
    A=[]; B=[]; 
    for a,b,c,d in W:
        A.append( a + b );
        B.append( c + d );
    rtn_instrumentation = "".join( A );
    rtn_merge_code = "".join( B );
    target_code_file = TEMPLATE_p1%(str(MAX_FLAG_LEN), seq_checks) + EGLOBALS + TEMPLATE_p1a%argstub + "".join( A ) + TEMPLATE_p2 + "".join( B ) + TEMPLATE_p3;
    if ( split_files ):
        inst_file = argstub + "_rtn_inst.cpp"
        rtn_file = argstub + "_rtn_merge_code.cpp"
        fout = open( inst_file, "w" );
        fout.write( rtn_instrumentation );
        fout.close();
        print "wrote file: ",  inst_file
        fout = open( rtn_file, "w" );
        fout.write( rtn_merge_code );
        fout.close();
        print "wrote file: ",  rtn_file
        target_code_file = TEMPLATE_p1 + EGLOBALS + TEMPLATE_p1a%argstub + "#include \"%s_rtn_inst.cpp\""%argstub  + TEMPLATE_p2 + "#include \"%s_merge_code.cpp\""%argstub + TEMPLATE_p3;
    fout = open(argstub + ".cpp" , "w" );
    fout.write( target_code_file );
    fout.close();

def main():
    # parse command line options
    RTN_INPUT = None
    INS_INPUT = None
    IMAGE_INPUT = None
    EXTRA_INPUT = None
    SPLIT_FILES = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsR:I:M:e:", ["help", "split", "routine", "instructions", "image", "extra"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options 
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        if o in ("-R", "--routine"):
            # specify the rtn hooks.
            RTN_INPUT = a;
        if o in ("-I", "--instructions"):
            # specify the ins hooks.
            INS_INPUT = a;
        if o in ("-M", "--image"):
            # specify the image hooks.
            IMAGE_INPUT = a;
        if o in ("-e", "--extra"):
            # specify the rtn hooks.
            EXTRA_INPUT = a.partition('.')[0];
        if o in ("-s", "--split"):
            SPLIT_FILES = True
    # process arguments
    if ( len( args ) != 1 ):
        print __doc__
        sys.exit( 3 );
    process( args[0], rtn=RTN_INPUT, ins=INS_INPUT, img=IMAGE_INPUT, extra=EXTRA_INPUT, split_files = SPLIT_FILES );

if __name__ == "__main__":
    main()
