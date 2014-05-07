"""

    Excipo ~ intercept  { -> }  Relatus ~ report 

This is our PIN TOOL for api tracing. (C) W.Casey, M.Appel


"""
import pprint
import sys
import argparse
import templates
from datetime import datetime
from collections import OrderedDict

extras = None
CALLOUTS = {}
SEQUENCES = None
PREHOOK = None
POSTHOOK = None
TOOL_TEMPLATE = None
SEQ_TEMPLATE = None
INJECT_INST = None
INJECT_FUNCARG_VAL = None
INJECT_FUNCARG_REF = None
GENERATED_HDR = "/* Begin generated code by ER python module {date}*/".format(date=datetime.now().strftime("%A, %d. %B %Y %I:%M%p"))
GENERATED_FTR = "/* End generated code by ER python module */"
PUSH_MACRO = "PUSH({0})"
TRANS_MACRO = "TRANS({0}, {1})"


class Sequences(object):

    def __init__(self, conf_map):
        self.flags = set()
        self.accept_states = set()
        self.seqs = []
        for key, val in conf_map.items():
            seq = Sequence(key, val)
            self.seqs.append(seq)
            self.flags.update(seq.flags)
        self.p_num = len(self.seqs)
        self.DFA = SwitchCases(self.flags)

        print '-'*79
        print 'Found Sequence Patterns:'
        for idx, seq in enumerate(self.seqs):
            print idx,':',seq.seq
        print '-'*79

    def init_DFA(self):
        self.update_pushes()
        self.update_transitions()
        self.DFA.finalize()
        print str(self.DFA)

    def init_accepts(self):
        for seq in self.seqs:
            self.accept_states.add(seq.seq[-1])

    def accepts(self, flag):
        return flag in self.accept_states

    def update_pushes(self):
        accept_last = []
        for p_idx, seq in enumerate(self.seqs):
            if seq.length == 1:
                self.DFA.add_last_line(seq.start_state, "return {0};".format(p_idx))
            else:
                self.DFA.add_line(seq.start_state, PUSH_MACRO.format(p_idx))

    def update_transitions(self):
        for p_idx, seq in enumerate(self.seqs):
            for seq_step, flag in enumerate(seq.seq[1:]):
                self.DFA.add_line(flag, TRANS_MACRO.format(p_idx, seq_step))

    def get_lengths(self):
        lens = '{'
        for p_idx, seq in enumerate(self.seqs):
            lens += str(seq.length)
            if p_idx < len(self.seqs) - 1:
                lens += ', '
        lens += '}'
        return lens

    def get_windows(self):
        windows = '{'
        for p_idx, seq in enumerate(self.seqs):
            windows += str(seq.window)
            if p_idx < len(self.seqs) - 1:
                windows += ', '
        windows += '}'
        return windows

    def get_dfa(self):
        return str(self.DFA)

    def get_user_code(self, flag):
        src_code = []
        for p_idx, seq in enumerate(self.seqs):
            if flag == seq.accept_state:
                src_code.append(seq.inject_code)
        return src_code

    def get_accept_code(self, flag):
        src_code = SwitchCases()
        for p_idx, seq in enumerate(self.seqs):
            if flag == seq.accept_state:
                src_code.add_case(p_idx)
                src_code.add_line(p_idx, seq.inject_code)
        src_code.finalize()
        return str(src_code)



class Sequence(object):
    
    def __init__(self, seq_tuple, seq_settings):
        self.flags = set()
        self.code_id = seq_settings[0]
        self.window = seq_settings[1]
        self.seq = seq_tuple
        self.start_state = seq_tuple[0]
        self.accept_state = seq_tuple[-1]
        self.inject_code = getattr(extras, self.code_id)
        self.length = len(seq_tuple)
        for flag in self.seq:
            self.flags.add(flag)

    def __str__(self):
        return self.inject_code


class SwitchCases(object):

    def __init__(self, flag_set=[]):
        self.cases = OrderedDict(zip(flag_set, [ [] for flag in flag_set]))
        self.last_lines = {}

    def add_case(self, case_id):
        self.cases[case_id] = []

    def add_line(self, case_id, line):
        self.cases.get(case_id).append(line)

    def add_last_line(self, case_id, line):
        self.last_lines[case_id] = line

    def finalize(self):
        for idx,src in self.cases.items():
            goes_last = self.last_lines.get(idx)
            if goes_last:
                src.append(goes_last)
            src.append('break;')

    def __str__(self):
        s = ''
        for key, val in self.cases.items():
            s += '    case {k}:\n'.format(k=key)
            for line in val:
                s += '        {src}\n'.format(src=line)
        s += '    default:\n        break;'
        return s

class Hook(object):
    
    def __init__(self, name, params):
        self.func_name = name
        self.doc_params = ",".join(params)
        self.formals = self.formalize_params(params)
        self.baseline = self.create_baseline(params)

    def formalize_params(self, params):
        formals_list = []
        for idx, param in enumerate(params):
            if self.func_name == 'fopen':
                formals_list.append("%s X%s " % ("void **", idx))
            else:
                formals_list.append("%s X%s " % ("void *", idx))
        return ', '.join(formals_list)

    def create_baseline(self, params):
        baseline = 'hex'
        for cnt in range(len(params)):
            baseline += ' << X{par_count} << ", " '.format(par_count = cnt)
        return baseline


class CallOut(object):

    def __init__(self, name):
        self.name = name
        self.pre_code = ''
        self.post_code = ''
        self.global_code = ''
        self.pre_flag = '0'
        self.post_flag = '0'
        self.pre_seq_code = ''
        self.post_seq_code = ''

    def initialize(self, dic):
        if 'preflag' in dic:
            self.pre_flag = dic.get('preflag')
            if self.pre_flag in SEQUENCES.flags:
                self.pre_seq_code = self.gen_seq_code(self.pre_flag)
        if 'postflag' in dic:
            self.post_flag = dic.get('postflag')
            if self.post_flag in SEQUENCES.flags:
                self.post_seq_code = self.gen_seq_code(self.post_flag)
        if 'global' in dic:
            self.global_code = dic.get('global')
        if 'pre' in dic:
            self.pre_code = dic.get('pre')
        if 'post' in dic:
            self.post_code = dic.get('post')

    def gen_seq_code(self, flag):
        src_code = []
        if SEQUENCES.accepts(flag):
            src_code.append('int retval = fast_push_code({0});'.format(flag))
            src_code.append('    switch(retval)')
            src_code.append('    {')
            src_code.append(SEQUENCES.get_accept_code(flag))
            src_code.append('    }')
        else:
            src_code.append('fast_push_code({0});'.format(flag))
        return '\n'.join(src_code)

def get_func_signatures(input_file):
    routine_data = []
    with open(input_file) as fin:
        cur_routine=None
        record = 0
        for line in fin:
            dec_ret_type, ws, dec_func_name_args = line.rstrip().partition(' ')
            if dec_func_name_args:
                routine_data.append( [dec_ret_type, dec_func_name_args] )
            else:
                if 0 == 1:
                    print "ODD LINE: %s"%line
    return routine_data

def split_signatures(func_sigs):
    retval = []
    try:
        for signature in func_sigs:
            func = signature[1]
            func_stub, _, func_para = func.partition('(')
            retval.append( [ signature[0], func_stub, func_para.replace( "(", "" ).replace(")","").replace("","").split( "," ) ] )
    except TypeError:
        pass
    return retval

def gen_callout(func_stub):
    callout = CallOut(func_stub)
    cout_conf = CALLOUTS.get(func_stub)
    if cout_conf:
        callout.initialize(cout_conf)
    return callout

def gen_hook_code(hook, callout):
    h_code = PREHOOK.format(func_name = hook.func_name,
                params = hook.formals,
                doc_params = hook.doc_params,
                baseline = hook.baseline,
                callout_code = callout.pre_code,
                sequence_code = callout.pre_seq_code)
    h_code += POSTHOOK.format(func_name = hook.func_name,
                doc_params = hook.doc_params,
                callout_code = callout.post_code,
                sequence_code = callout.post_seq_code)
    return h_code

def gen_analysis(func_sigs):
    hook_conditions = []

    hook_conditions.append(GENERATED_HDR)

    for func_rv, func_stub, func_params in func_sigs:
        if(func_stub == 'fopen'):
            inject_args = "".join( [ INJECT_FUNCARG_REF.format(count=cnt) for cnt in range(len(func_params)) ] )
        else:
            inject_args = "".join( [ INJECT_FUNCARG_VAL.format(count=cnt) for cnt in range(len(func_params)) ] )
        hook_conditions.append(INJECT_INST.format(func_name = func_stub, func_args = inject_args))

    hook_conditions.append(GENERATED_FTR)
    return hook_conditions

def gen_instrumentation(func_sigs): 
    capt_hook = []
    global_code = []

    capt_hook.append(GENERATED_HDR)
    global_code.append(GENERATED_HDR)

    for func_rv, func_stub, func_params in func_sigs:
        hook = Hook(func_stub, func_params)
        callout = gen_callout(func_stub)

        # Generate the code for pre/post hook functions
        hook_code = gen_hook_code(hook, callout)

        # Add generated code to lists
        global_code.append(callout.global_code)
        capt_hook.append(hook_code)

    capt_hook.append(GENERATED_FTR)
    global_code.append(GENERATED_FTR)

    return capt_hook, global_code

def process(out, rtn, ins, img, split):
    func_sigs = get_func_signatures(rtn)
    func_sigs = split_signatures(func_sigs)
    analysis = gen_analysis(func_sigs)
    instrumentation, global_code = gen_instrumentation(func_sigs)

    global_code = "".join(global_code)
    analysis = "".join(analysis)
    instrumentation = "".join(instrumentation)
    sequences = SEQ_TEMPLATE.format(p_num=SEQUENCES.p_num, lengths=SEQUENCES.get_lengths(), windows=SEQUENCES.get_windows(), cases=SEQUENCES.get_dfa())

    if split:
        i_file = out + "_instrument.cpp"
        a_file = out + "_analysis.cpp"
        with open( i_file, "w" ) as fout:
            fout.write( instrumentation )
            print "Wrote file:",  i_file
        with open( a_file, "w" ) as fout:
            fout.write( analysis )
            print "Wrote file:",  a_file
        source_code = TOOL_TEMPLATE.format(g_code=global_code, log_name=out, i_code='#include "{f}"'.format(f=i_file), a_code='#include "{f}"'.format(f=a_file), seq_code=sequences)
    else:
        source_code = TOOL_TEMPLATE.format(g_code=global_code, log_name=out, i_code=instrumentation, a_code=analysis, seq_code=sequences)

    with open(out + ".cpp" , "w" ) as fout:
        fout.write(source_code)
        print "Wrote file:",out+".cpp"

def get_args(cmd_line):
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--extras', default=None, help='File with callouts and sequences')
    parser.add_argument('--img', default=None, help='Image hooks')
    parser.add_argument('--inst', default=None, help='File containing instructions to hook')
    parser.add_argument('-o', '--out', default='TMP', help='Output file name. Default: TMP.cpp')
    parser.add_argument('-r', '--rtn', default=None, help='File containing list of prototypes for funcs/routines to watch in trace')
    parser.add_argument('-s', '--split', default=False, action='store_true', help='Split output files into separate source code files')
    parser.add_argument('-t', '--templates', default='templates', help='Py module containing templated code')
    retval = parser.parse_args(cmd_line)
    retval.out = retval.out.partition('.')[0]
    return retval

if __name__ == "__main__":
    args = get_args(sys.argv[1:])
    try:
        extras = __import__(args.extras.partition('.py')[0])
    except ImportError as err:
        print 'Error importing extras module'
        repr(err)
        sys.exit(1)
    except AttributeError as err:
        pass
    else:
        CALLOUTS = extras.CALLOUTS
        SEQUENCES = Sequences(extras.SEQUENCES)
        SEQUENCES.init_DFA()
        SEQUENCES.init_accepts()

    try:
        templates = __import__(args.templates.partition('.py')[0])
    except ImportError as err:
        print 'Error importing templated code file'
        repr(err)
        sys.exit(1)
    else:
        PREHOOK=templates.PREHOOK
        POSTHOOK=templates.POSTHOOK
        TOOL_TEMPLATE=templates.TOOL_TEMPLATE
        SEQ_TEMPLATE=templates.SEQUENCE_TEMPLATE
        INJECT_INST=templates.INJECT_INST
        INJECT_FUNCARG_VAL = templates.INJECT_FUNCARG_VAL
        INJECT_FUNCARG_REF = templates.INJECT_FUNCARG_REF

    process(args.out, args.rtn, args.inst, args.img, args.split)
