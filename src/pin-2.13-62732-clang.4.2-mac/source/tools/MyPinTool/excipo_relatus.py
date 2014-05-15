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
        self.init_DFA()
        self.init_accepts()

    def __iter__(self):
        return iter(self.seqs)

    def debug(self):
        print '-'*79
        print 'Found Sequence Patterns:'
        for idx, seq in enumerate(self.seqs):
            print idx,':',seq.seq
        print '-'*79

    def init_DFA(self):
        self.update_pushes()
        self.update_transitions()
        self.DFA.finalize()

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
    
    def __init__(self, name, params, is_callout):
        self.func_name = name
        self.is_callout = is_callout
        self.doc_params = ', '.join( [ '{typ} {ident}'.format(typ=f[0], ident=f[1]) for f in params ] )
        self.formals = self.formalize_params(params)
        self.baseline = self.create_baseline(params)

    def formalize_params(self, params):
        formals_list = []
        for idx, param in enumerate(params):
            if self.is_callout:
                formals_list.append("%s X%s " % ("void **", idx))
            else:
                formals_list.append("%s X%s " % ("void *", idx))
        return ', '.join(formals_list)

    def create_baseline(self, params):
        baseline = 'hex'
        for cnt in range(len(params)):
            if self.is_callout:
                baseline += ' << *X{par_count} << ", " '.format(par_count = cnt)
            else:
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
            #if self.pre_flag in SEQUENCES.flags:
                #self.pre_seq_code = self.gen_seq_code(self.pre_flag)
        if 'postflag' in dic:
            self.post_flag = dic.get('postflag')
            #if self.post_flag in SEQUENCES.flags:
                #self.post_seq_code = self.gen_seq_code(self.post_flag)
        if 'global' in dic:
            self.global_code = dic.get('global')
        if 'pre' in dic:
            self.pre_code = dic.get('pre')
        if 'post' in dic:
            self.post_code = dic.get('post')

    def init_seq_code(self, flag, accept_code=None):
        if accept_code:
            src_code = self.gen_seq_accept(flag, accept_code);
        else:
            src_code = self.gen_seq_code(flag);

        if flag is self.pre_flag:
            self.pre_seq_code = '\n'.join(src_code)
        else:
            self.post_seq_code = '\n'.join(src_code)

    def gen_seq_accept(self, flag, accept_code):
        src_code = []
        src_code.append('int retval = fast_push_code({0});'.format(flag))
        src_code.append('    switch(retval)')
        src_code.append('    {')
        #src_code.append(SEQUENCES.get_accept_code(flag))
        src_code.append(accept_code)
        src_code.append('    }')
        return src_code

    def gen_seq_code(self, flag):
        return [ 'fast_push_code({0});'.format(flag), ]


    def __str__(self):
        return self.name + ': ' + str(self.pre_flag) + ' -> ' + str(self.post_flag) + '\n' + self.pre_seq_code + '\n' + self.post_seq_code


class CDeclaration(object):

    def __init__(self):
        self.rt = ''
        self.ident = ''
        self.formals = []
        self.string = '{ret} {ident}({formals});'

    def __str__(self):
        return self.string.format(
                            ret=self.rt,
                            ident=self.ident,
                            formals=', '.join( [ '{typ} {ident}'.format(typ=f[0], ident=f[1]) for f in self.formals ] )
                            )


class Lexception(Exception):

    def __init__(self, string):
        self.string = string

    def __str__(self):
        return "Error analyzing api function: {blame}".format(blame=self.string)


class CLexer(object):

    def lex(self, api_line):
        cdecl = CDeclaration()
        self.analyze(cdecl, api_line)
        return cdecl

    def analyze(self, cdecl, line):
        rt, _, name_formals = line.partition(' ')
        if not rt or not name_formals:
            raise Lexception(line + ': return type, function name error')
        ident, _, formals = name_formals.partition('(')
        if not ident or not formals:
            raise Lexception(line + ': identifier, parens, or params error')
        cdecl.rt = rt
        cdecl.ident = ident
        formals = formals.rstrip('); ').split(',')
        for formal in formals:
            formal = formal.strip()
            typ, _, name = formal.partition(' ')
            if formal and (not typ or not name):
                raise Lexception(line + ': formal params list error')
            cdecl.formals.append( (typ, name) )


class TraceFunction(object):

    def __init__(self, decl):
        self.name = decl.ident
        self.decl = decl
        self.callout = CallOut(self.name)
        self.is_callout = False

    def add_callout(self, cout_dict):
        self.is_callout = True
        self.callout.initialize(cout_dict)

    def get_flags(self):
        return (self.callout.pre_flag, self.callout.post_flag)

    def get_name(self):
        return self.decl.ident

    def get_formals(self):
        return self.decl.formals

    def __str__(self):
        string = 'TFunc {name}: {decl}\n'.format(name=self.name, decl=self.decl)
        if self.callout:
            string += '\tCallout: {cout}\n'.format(cout=self.callout)
        string += '\n'
        return string


class TraceList(object):

    def __init__(self):
        self.funcs = {}
        self.seqs = None
        self.flag_map = {}

    def load_api(self, api_file):
        lexer = CLexer()
        with open(api_file) as fin:
            for line in fin:
                try:
                    cdecl = lexer.lex(line.rstrip())
                except Lexception as e:
                    print e
                else:
                    tfunc = TraceFunction(cdecl)
                    self.funcs[tfunc.name] = tfunc

    def load_callouts(self):
        if not CALLOUTS:
            print 'Skipping Callout Analysis'
            return
        for cout_name, cout_params in CALLOUTS.items():
            if cout_name in self.funcs:
                tfunc = self.funcs.get(cout_name)
                tfunc.add_callout(cout_params)
                pre_flag, post_flag = tfunc.get_flags()
                #callout = CallOut(cout_name)
                #callout.initialize(cout_params)
                #self.funcs[cout_name].callout = callout
                self.add_flag(pre_flag, cout_name)
                self.add_flag(post_flag, cout_name)

    def add_flag(self, flag, name):
        if flag:
            if flag in self.flag_map:
                self.flag_map[flag].append(name)
                print 'Note: duplicate flag {0} for {1}'.format(flag, [ ', '.join(n for n in self.flag_map.get(flag)) ] )
            else:
                self.flag_map[flag] = [ name, ]

    def load_sequences(self):
        if not SEQUENCES:
            print 'Skipping Sequence Analysis'
        else:
            self.seqs = Sequences(SEQUENCES)
            for flag in self.seqs.flags:
                try:
                    f_list = self.flag_map.get(flag)
                except TypeError:
                    print 'No sequence flags were found'
                else:
                    if not f_list:
                        print 'Sequence flag not found in callouts: {0}'.format(flag)
                    else:
                        self.add_seq_code(flag, f_list)

    def add_seq_code(self, flag, f_list):
        for f_name in f_list:
            tfunc = self.funcs.get(f_name)
            if(self.seqs.accepts(flag)):
                tfunc.callout.init_seq_code(flag, self.seqs.get_accept_code(flag))
            else:
                tfunc.callout.init_seq_code(flag)

    def __str__(self):
        string = ''
        for tfunc in self.funcs.values():
            string += str(tfunc)
        return string

    def gen_analysis(self):
        hook_conditions = []

        hook_conditions.append(GENERATED_HDR)

        #for func_rv, func_stub, func_params in func_sigs:
        for tfunc in self.funcs.values():
            func_stub = tfunc.get_name()
            func_params = tfunc.get_formals()
            if tfunc.is_callout:
                inject_args = "".join( [ INJECT_FUNCARG_REF.format(count=cnt) for cnt in range(len(func_params)) ] )
            else:
                inject_args = "".join( [ INJECT_FUNCARG_VAL.format(count=cnt) for cnt in range(len(func_params)) ] )
            hook_conditions.append(INJECT_INST.format(func_name = func_stub, func_args = inject_args))

        hook_conditions.append(GENERATED_FTR)
        return hook_conditions

    def gen_hook_code(self, hook, callout):
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

    def gen_instrumentation(self): 
        capt_hook = []
        global_code = []

        capt_hook.append(GENERATED_HDR)
        global_code.append(GENERATED_HDR)

        #for func_rv, func_stub, func_params in func_sigs:
        for tfunc in self.funcs.values():
            func_stub = tfunc.get_name()
            func_params = tfunc.get_formals()

            hook = Hook(func_stub, func_params, tfunc.is_callout)
            callout = tfunc.callout

            # Generate the code for pre/post hook functions
            hook_code = self.gen_hook_code(hook, callout)

            # Add generated code to lists
            global_code.append(callout.global_code)
            capt_hook.append(hook_code)

        capt_hook.append(GENERATED_FTR)
        global_code.append(GENERATED_FTR)

        return capt_hook, global_code

    def gen_sequences(self):
        return SEQ_TEMPLATE.format(p_num=self.seqs.p_num, lengths=self.seqs.get_lengths(), windows=self.seqs.get_windows(), cases=self.seqs.get_dfa())


def process(out, rtn, ins, img, split):
    traces = TraceList()
    traces.load_api(rtn)
    traces.load_callouts()
    traces.load_sequences()

    analysis = traces.gen_analysis()
    instrumentation, global_code = traces.gen_instrumentation()
    sequences = traces.gen_sequences()

    analysis = "".join(analysis)
    instrumentation = "".join(instrumentation)
    global_code = "".join(global_code)

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
        try:
            CALLOUTS = extras.CALLOUTS
        except AttributeError:
            CALLOUTS = None
        try:
            SEQUENCES = extras.SEQUENCES
        except AttributeError:
            SEQUENCES = None
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
