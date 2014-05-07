PREHOOK="""
VOID pre_{func_name}(CHAR * name, {params})
{{

    /* 
     * Function: {func_name}
     * Input parameters: {doc_params}
     */

    /*
     * BASELINE
     */
    TraceFile << "PRE CALL-OUT (PID:"<< PID << ",TID:" << TID << "): " << name << " ("<< {baseline} <<") " << dec << endl; 

    /* Callout Code if any */
    {callout_code}

    /* Sequence Interaction */
    {sequence_code}
}}
"""

POSTHOOK="""
VOID post_{func_name}(CHAR * name, ADDRINT ret)
{{

    /* 
     *  Function: {func_name} 
     *  Input parameters: {doc_params}
     */

    /* 
     * BASELINE
     */
    TraceFile << "POST CALL-OUT (PID:"<<PID<<",TID:"<<TID<<"): "<< name << " RETURN-VALUE @:" << hex << ret << dec << " RETURN-VALUE-INTERP:" << dec << ((int) ret ) << endl; 
    
    /* Callout Code if any */
    {callout_code}

    /* Sequence Interaction */
    {sequence_code}
}}
"""


INJECT_INST="""
                if (rtn_match(R1, "_{func_name}"))
                {{
                    RTN_Open(rtn);
                    RTN_InsertCall(rtn, IPOINT_BEFORE, (AFUNPTR)pre_{func_name},
                                   IARG_ADDRINT, "{func_name}",{func_args}
                                   IARG_END);
                    RTN_InsertCall(rtn, IPOINT_AFTER, (AFUNPTR)post_{func_name},
                                   IARG_ADDRINT, "{func_name}", 
                                   IARG_FUNCRET_EXITPOINT_VALUE,
                                   IARG_END);
                    if(REPORT_MERGING)
                    {{
                        printf("Added pre and post hooks to: {func_name}\\n");
                    }}
                    if(KnobSelectMem)
                    {{
                       for(INS curr=RTN_InsHead(rtn); INS_Valid(curr); curr=INS_Next(curr))
                       {{
                           instrument_mem(curr);
                       }}
                    }}
                    RTN_Close(rtn);
                }}
"""
INJECT_FUNCARG_VAL="""
                                   IARG_FUNCARG_ENTRYPOINT_VALUE, {count},"""
INJECT_FUNCARG_REF="""
                                   IARG_FUNCARG_ENTRYPOINT_REFERENCE, {count},"""

SEQUENCE_TEMPLATE="""
void accept(int pattern_index);

#define ACCEPT(K) if(t->step == t->goal) {{ return K; }} else {{ return 0; }}

#define PUSH(K) if(PATTERNS[K]){{ get_tail(PATTERNS[K])->next = new_clause(K); }} else{{ PATTERNS[K]=new_clause(K); }}

#define TRANS(K, S) if(PATTERNS[K]){{ t=PATTERNS[K]; window_size = P_WND[K]; while(t){{ if(t->step==S){{ t->step++; }} ACCEPT(K) t=t->next; }} }}

int CLOCK = 0;
struct cnode **PATTERNS = NULL;
#define P_NUM {p_num}
int P_LEN[P_NUM] = {lengths};
int P_WND[P_NUM] = {windows};

struct cnode
{{
    // Which step in the pattern the clause is 
    int step;
    // Which step is the goal
    int goal;
    // Clock time for this clause's creation
    int start;
    // Clock + Window => This clause is invalid
    int expire;
    // Next clause of the same pattern
    struct cnode * next ;
}};

struct cnode * new_clause (int p_idx)
{{
    struct cnode * x = (struct cnode *) malloc(sizeof(struct cnode));
    x->start = CLOCK;
    x->expire = CLOCK + P_WND[p_idx];
    x->step = 0;
    x->goal = P_LEN[p_idx] - 1;
    x->next = NULL;
    return x;
}}

struct cnode * get_tail( struct cnode * Y )
{{
    struct cnode * rv = Y;
    while(rv->next)
    {{
        rv = rv->next;
    }}
    return rv;
}}

void init_cnode_array()
{{
    int k;
    PATTERNS = (struct cnode **) malloc(sizeof(struct cnode*) * P_NUM);
    for (k = 0; k < P_NUM ; k ++)
    {{
        PATTERNS[k] = NULL;
    }}
}}

int fast_push_code (int code)
{{
    struct cnode * t;
    int window_size = 0;
    int k = 0;
    for (k = 0; k < P_NUM ; k++)
    {{
        t = PATTERNS[k];
        while(t && ( (t->expire < CLOCK) || (t->step >= t->goal) ) )
        {{
            t = t->next;
            free(PATTERNS[k]);
            PATTERNS[k] = t;
        }}
    }}

    switch(code)
    {{
    {cases}
    }}

    return 0;
}}
"""


TOOL_TEMPLATE="""

/* ****** ****** ****** ****** ****** ****** ****** ****** ****** ******

   MBMC - Tracer POST-HOOK (C) CMU SEI 2013: Will Casey, Jeff Gennari, 
                                   Jose Morales, Evan Wright, Jono Spring. 
                                   Michael Appel
                               NYU CIMS 2013: Bud Mishra, Thomson Nguyen

*/

#include "pin.H"

#include <iostream>
#include <fstream>
#include <iomanip>
#include <stdio.h>
#include <string>


/* ===================================================================== */
/* Platform Specific */
/* ===================================================================== */

#if defined __amd64__ || defined __x86_64__ || defined _M_X64 || defined _M_AMD64
    #define ENV64BIT
#else
    #define ENV32BIT
#endif

#ifdef _WIN32
    // This will also fire on 64 bit Windows
    namespace WINDOWS
    {{
        #include <Windows.h>
    }}
    #include<io.h>
    #include<WinDef.h>
    #include<WinNT.h>
    #include<BaseTsd.h>

    /* Windows Data Types that are not working even with addt'l inclusions */
    typedef unsigned long ULONG;
    typedef unsigned short USHORT;

    typedef void *PVOID;
    typedef PVOID HANDLE;

    typedef wchar_t WCHAR;
    typedef WCHAR *PWSTR;

    /* Structs to access object attributes pointers in syscalls */

    typedef struct _UNICODE_STRING {{
            USHORT Length;
            USHORT MaximumLength;
            PWSTR Buffer;
    }} UNICODE_STRING, *PUNICODE_STRING;

    typedef struct _OBJECT_ATTRIBUTES {{
            ULONG	Length;
            HANDLE RootDirectory;
            PUNICODE_STRING ObjectName;
            ULONG Attributes;
            PVOID SecurityDescriptor;
            PVOID SecurityQualityOfService;
    }} OBJECT_ATTRIBUTES, *POBJECT_ATTRIBUTES;
#else
    #include <unistd.h>
#endif

#ifdef _WIN64
    // Only 64 bit windows
#endif

#ifdef __ANDROID__
    // Android platform specific lines here
    // Linux macros are also defined for android
#endif

#ifdef __ANDROID_API__
    #if __ANDROID_API__ > 0
        // Android API version specific code
    #endif
#endif

#ifdef __linux__
    // This will also trigger on Android devices
#endif

#if defined __APPLE__ && defined __MACH__
    // OS X+
    // Defined by GNU C and Intel C++
    #define ENVMACOS
#endif

#ifdef ENVMACOS
    #include <regex.h>
#else
    #include <regex>
#endif

/* ===================================================================== */
/* Global Variables */
/* ===================================================================== */

#define TICUB 2048 
#define PID LEVEL_PINCLIENT::PIN_GetPid()
#define TID LEVEL_PINCLIENT::PIN_ThreadId()

UINT64 icount = 0;
UINT64 slp_count = 0;  //codelet count.
std::ofstream TraceFile;
int call_stack_depth = 0;
string invalid = "UNKNOWN-SYM";
int REPORT_MERGING = 1;
UINT64 ticount[TICUB];

/* For Memory Instrumentation */
static VOID * WriteAddr;
static INT32 WriteSize;


/* ===================================================================== */
/* Util Functions */
/* ===================================================================== */

int rtn_match(string a, string b)
{{
    return a==b;
}}

VOID thread_init(){{
    int t = 0;
    for ( t = 0 ; t < TICUB ; t ++ ){{
	ticount[t] = 0;
    }}
}}

VOID do_count(ADDRINT X ){{
  icount++; 
  TraceFile << ":::[" << PID << "." << TID << "] " << dec << icount <<"\\t"<< hex << X << endl;
}}

VOID string_report(const string *s){{
  TraceFile.write(s->c_str(), s->size());
}}


/* ===================================================================== */
/* Supporting global code from extras.py */
/* ===================================================================== */

{g_code}

/* ===================================================================== */
/* done with supporting extras.py */
/* ===================================================================== */

/* ===================================================================== */
/* Sequence Functions */
/* ===================================================================== */

{seq_code}

/* ===================================================================== */
/* Commandline Switches */
/* ===================================================================== */


KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool",
    "o", "{log_name}.out", "specify trace file name");
KNOB<BOOL>   KnobNoCompress(KNOB_MODE_WRITEONCE, "pintool",
    "no_compress", "0", "Do not compress");
KNOB<BOOL> KnobSelectMem(KNOB_MODE_WRITEONCE, "pintool",
    "m", "0", "Output memory values reads and writes");
KNOB<BOOL> KnobAllMem(KNOB_MODE_WRITEONCE, "pintool",
    "mm", "0", "Output memory values reads and writes");


/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */


INT32 Usage()
{{
    cerr << "This tool produces a trace of calls to RtlAllocateHeap.";
    cerr << endl << endl;
    cerr << KNOB_BASE::StringKnobSummary();
    cerr << endl;
    return -1;
}}


/* ===================================================================== */
/* Instrumenation                                                        */
/* ===================================================================== */
{i_code}
/* ===================================================================== */
/* Memory IO Recording Routines */
/* ===================================================================== */


static VOID EmitMem(VOID * ea, INT32 size)
{{
    if (!KnobAllMem || !KnobSelectMem)
        return;
    
    switch(size)
    {{
      case 0:
        TraceFile << setw(1);
        break;
        
      case 1:
        TraceFile << static_cast<UINT32>(*static_cast<UINT8*>(ea));
        break;
        
      case 2:
        TraceFile << *static_cast<UINT16*>(ea);
        break;
        
      case 4:
        TraceFile << *static_cast<UINT32*>(ea);
        break;
        
      case 8:
        TraceFile << *static_cast<UINT64*>(ea);
        break;
        
      default:
        TraceFile.unsetf(ios::showbase);
        TraceFile << setw(1) << "0x";
        for (INT32 i = 0; i < size; i++)
        {{
            TraceFile << static_cast<UINT32>(static_cast<UINT8*>(ea)[i]);
        }}
        TraceFile.setf(ios::showbase);
        break;
    }}
}}

static VOID RecordMem(VOID * ip, CHAR r, VOID * addr, INT32 size, BOOL isPrefetch)
{{
    TraceFile << "M\t" << ip << ": " << r << " " << setw(2+2*sizeof(ADDRINT)) << addr << " "
              << dec << setw(2) << size << " "
              << hex << setw(2+2*sizeof(ADDRINT));
    if (!isPrefetch)
        EmitMem(addr, size);
    TraceFile << endl;
}}

static VOID RecordWriteAddrSize(VOID * addr, INT32 size)
{{
    WriteAddr = addr;
    WriteSize = size;
}}

static VOID RecordMemWrite(VOID * ip)
{{
    RecordMem(ip, 'W', WriteAddr, WriteSize, false);
}}


/* ===================================================================== */
/* Instrumentation routines                                              */
/* ===================================================================== */


VOID instrument_mem(INS ins)
{{
    // instruments loads using a predicated call, i.e.
    // the call happens iff the load will be actually executed
    if (INS_IsMemoryRead(ins))
    {{
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordMem,
            IARG_INST_PTR,
            IARG_UINT32, 'R',
            IARG_MEMORYREAD_EA,
            IARG_MEMORYREAD_SIZE,
            IARG_BOOL, INS_IsPrefetch(ins),
            IARG_END);
    }}

    if (INS_HasMemoryRead2(ins))
    {{
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordMem,
            IARG_INST_PTR,
            IARG_UINT32, 'R',
            IARG_MEMORYREAD2_EA,
            IARG_MEMORYREAD_SIZE,
            IARG_BOOL, INS_IsPrefetch(ins),
            IARG_END);
    }}

    // instruments stores using a predicated call, i.e.
    // the call happens iff the store will be actually executed
    if (INS_IsMemoryWrite(ins))
    {{
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordWriteAddrSize,
            IARG_MEMORYWRITE_EA,
            IARG_MEMORYWRITE_SIZE,
            IARG_END);
        
        if (INS_HasFallThrough(ins))
        {{
            INS_InsertCall(
                ins, IPOINT_AFTER, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }}
        if (INS_IsBranchOrCall(ins))
        {{
            INS_InsertCall(
                ins, IPOINT_TAKEN_BRANCH, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }}
        
    }}
}}


/* ===================================================================== */
/* Trace routines                                                        */
/* ===================================================================== */

const string *Target2String(ADDRINT target)
{{
    string name = RTN_FindNameByAddress(target);
    if (name == "")
      return &invalid;
    else
      return new string(name);
}}

VOID trace_instrument(TRACE trace, VOID *v)
{{
  for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl))
  {{ 
    /* iterate over all basic blocks */
    
    string codelet_string = "";
    // this writes disassembly 
    char codelet_buffer[65536*2]; int cbs = 0;
    INS head = BBL_InsHead(bbl);
    INS tail = BBL_InsTail(bbl);
    
    ADDRINT stage_entry = INS_Address( head );
    ADDRINT target = 0;
    if (INS_IsCall(tail))
    {{
        if( INS_IsDirectBranchOrCall(tail))
        {{
            target = INS_DirectBranchOrCallTargetAddress(tail);
        }}
    }}

    INS cur ;
    int branch_id = slp_count;
      
    /* If compression is turned off (default), only output the addresses of
     * the BBL once
     */
    if (!KnobNoCompress)
    {{
      /* Instrument the head instruction right before it is called, and also
       * before we instrument the instructions in the basic block 
       */
      string msg_pre  = "\\n@@BBL(" + decstr( branch_id ) + ") STAGE " + Target2String(stage_entry)->c_str() + "\\n" ;
      INS_InsertCall(head, IPOINT_BEFORE, AFUNPTR(string_report),
		     IARG_PTR, new string(msg_pre),
		     IARG_END);
    }}
   
    /* Walk the list of instructions inside the BBL. Disassemble each, and add
     * it to the codelet string. Also, instrument each instruction at the
     * point before it is called with the do_count function.
     */
    for ( cur = head; INS_Valid( cur ); cur = INS_Next(cur ) )
    {{
        cbs += sprintf( codelet_buffer + cbs , "\\n\\t@%llx\\t%s", INS_Address( cur ), INS_Disassemble( cur ).c_str() );
        INS_InsertCall(cur, IPOINT_BEFORE, (AFUNPTR)do_count, IARG_ADDRINT, INS_Address( cur ), IARG_END);
        if(KnobAllMem)
        {{
            instrument_mem(cur);
        }}
    }}

    /* Finish off the codelet assembly string with an out message and
     * address ranges of the BBL
     */
    cbs += sprintf( codelet_buffer + cbs , "\\n\\t}}BBL.OUT [%d] %llx - %llx\\n", branch_id, INS_Address( head ), INS_Address( tail ));
  
    /* If compression is turned on, output the codelet every single time we
     * hit the same block.
     */
    if(KnobNoCompress)
    {{
        INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(string_report),
		     IARG_PTR, new string(codelet_buffer),
		     IARG_END);
      slp_count ++;
    }}
    else
    {{
        /* add the mapped BBL to output */
        TraceFile.write(codelet_buffer, cbs);	

        /* Instrument the tail instruction by inserting just before it is called
        */
        string msg_post = "+@@BBL(" + decstr( branch_id ) + ") ACHIEVE : GOTO " + Target2String(target)->c_str();
        INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(string_report),
                     IARG_PTR, new string(msg_post),
                     IARG_END);

        slp_count ++;
    }}
  }}
}}

/* ===================================================================== */
/* Image Mapping routines                                                */
/* ===================================================================== */

void report_sym_structure( SYM sym, int depth )
{{
  int k = 0;
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\\t" ; 
  TraceFile << "<SYM>";
  
  string sym_1 = PIN_UndecorateSymbolName(SYM_Name(sym), UNDECORATION_NAME_ONLY);
  string sym_2 = PIN_UndecorateSymbolName(SYM_Name(sym), UNDECORATION_COMPLETE );
  ADDRINT offset  = SYM_Value( sym );	
  TraceFile << hex << offset << " sym.1:" << sym_1 << " sym.2:" << sym_2 << "</SYM>" << endl;
}}

void report_routine_structure( RTN rtn , int depth)
{{
  string R1 = LEVEL_PINCLIENT::RTN_Name (rtn );  
  AFUNPTR R3 =LEVEL_PINCLIENT::RTN_Funptr (rtn);
  INT32 R4 = 	LEVEL_PINCLIENT::RTN_Id (rtn );
  USIZE R5 =	LEVEL_PINCLIENT::RTN_Range ( rtn);
  USIZE R6 = 	LEVEL_PINCLIENT::RTN_Size ( rtn);
  ADDRINT R7 =	LEVEL_PINCLIENT::RTN_Address ( rtn);
  string r2_1 = "";
  string r2_2 = "";
  int k = 0;
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\\t" ; 
  TraceFile << "<ROUTINE> R1:" << R1 << " R2.1:" << r2_1 << " R2.2" << r2_2 << " R3:" << R3 << " R4:" << R4 << " R5:" << R5 << " R6:" << R6 << " R7:" << R7 << "</ROUTINE>" << endl;
}}

void report_section_structure(SEC sec, int depth )
{{
  BOOL S1 = LEVEL_PINCLIENT::SEC_Valid (sec);
  string S2 = LEVEL_PINCLIENT::SEC_Name (sec);
  SEC_TYPE S3 = LEVEL_PINCLIENT::SEC_Type (sec);
  BOOL S4 = LEVEL_PINCLIENT::SEC_Mapped (sec);
  ADDRINT S5  = LEVEL_PINCLIENT::SEC_Address (sec);
  BOOL S6 = LEVEL_PINCLIENT::SEC_IsReadable (sec);
  BOOL S7 = LEVEL_PINCLIENT::SEC_IsWriteable (sec);
  BOOL S8 = LEVEL_PINCLIENT::SEC_IsExecutable (sec);
  USIZE S9 = LEVEL_PINCLIENT::SEC_Size (sec);
  char sec_type[128];
  int k;

  switch ( S3 )
  {{
  case SEC_TYPE_REGREL :  	
    strcpy( sec_type, "relocations" );
    break;
  case SEC_TYPE_DYNREL:
    strcpy( sec_type, "dynamic-relocations" );
    break;
  case SEC_TYPE_EXEC:
    strcpy( sec_type, "contains-code" );
    break;
  case SEC_TYPE_DATA:
    strcpy( sec_type, "contains-initialized-data" );    
    break;
  case SEC_TYPE_LSDA:
    strcpy( sec_type, "old-exception_info-obsolete" );    
    break;    
  case SEC_TYPE_BSS:
    strcpy( sec_type, "contains-uninitialized-data" );    
    break;    
  case SEC_TYPE_LOOS: 
    strcpy( sec_type, "OS-specific" );    
    break;    
  case SEC_TYPE_USER:
    strcpy( sec_type, "Application-specific" );    
    break;    
  default: 
    strcpy( sec_type, "UNKNOWN" );    
    break;       
  }}
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "<SECTION>S1:" << S1 << " S2:" << S2 << " S3:" << S3 << " S4:" << S4 << " S5:" << S5 << " S6:" << S6 << " S7:" << S7 << " S8:" << S8 << " S9:" << S9 << " Stype:" << sec_type << endl;

  for( RTN rtn= SEC_RtnHead(sec); RTN_Valid(rtn); rtn = RTN_Next(rtn) )
  {{
    report_routine_structure( rtn, depth + 1  );
    string R1 = LEVEL_PINCLIENT::RTN_Name (rtn );

    {a_code}

  }}
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\\t" ; 
  TraceFile << "</SECTION>" << endl;
}}

void report_image_structure(IMG img, int depth)
{{
  UINT32 I1 = IMG_Id(img);
  string I2 = IMG_Name(img);
  int I3 = IMG_IsMainExecutable( img );
  int I4 = IMG_IsStaticExecutable( img );
  ADDRINT I5 = IMG_LoadOffset(img);
  ADDRINT I6 = IMG_LowAddress(img);
  ADDRINT I7 = IMG_HighAddress(img);
  ADDRINT I8 = IMG_LoadOffset(img);
  ADDRINT I9 = IMG_StartAddress(img);
  ADDRINT I10 = IMG_Entry(img);
  USIZE   I11 = IMG_SizeMapped( img );
  IMG_TYPE I12 = IMG_Type(img);
  char I13[128];

  int k ; 
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "<IMAGE-LOAD>" << " I1:" << I1 << " I2:" << I2 << " I3:" << I3 << " I4:" << I4 << " I5:" << hex<< I5 << " I6:"<< I6 << " I7:" << I7 << " I8:" << I8 << " I9:"<< I9  << " I10:"<< I10  << " I11:" << I11 ;

  switch ( I12 )
  {{
  case IMG_TYPE_STATIC:
    strcpy( I13 ,"static" ); break;
  case IMG_TYPE_SHARED:
    strcpy( I13 ,"shared" ); break;
  case IMG_TYPE_INVALID:
    strcpy( I13 ,"invalid" ); break;
  case IMG_TYPE_LAST:
    strcpy( I13 ,"last" ); break;
  case IMG_TYPE_SHAREDLIB:
    strcpy( I13 ,"shared-lib" ); break;
  case IMG_TYPE_RELOCATABLE:
    strcpy( I13 ,"relocatable" ); break;
  #if PIN_PRODUCT_VERSION_MINOR > 12
      case IMG_TYPE_DYNAMIC_CODE:
        strcpy( I13 ,"dynamic-code" ); break;
  #endif
  default:
    strcpy( I13 ,"UNKNOWN" ); break;
  }}

  TraceFile << " I12:" << I12 << " I13:" << I13 << endl;

  for( SEC sec = IMG_SecHead(img); SEC_Valid(sec); sec = SEC_Next(sec) )
  {{
    report_section_structure( sec, depth + 1   ); 
  }}

  /* */

  for (SYM sym = IMG_RegsymHead(img); SYM_Valid(sym); sym = SYM_Next(sym))
  {{
    report_sym_structure( sym, depth +1 );
  }}
 
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "</IMAGE-LOAD>" << endl;
}}

void report_image_structure_2(IMG img, int depth)
{{
  UINT32 I1 = IMG_Id(img);
  string I2 = IMG_Name(img);
  int I3 = IMG_IsMainExecutable( img );
  int I4 = IMG_IsStaticExecutable( img );
  ADDRINT I5 = IMG_LoadOffset(img);
  ADDRINT I6 = IMG_LowAddress(img);
  ADDRINT I7 = IMG_HighAddress(img);
  ADDRINT I8 = IMG_LoadOffset(img);
  ADDRINT I9 = IMG_StartAddress(img);
  ADDRINT I10 = IMG_Entry(img);
  USIZE   I11 = IMG_SizeMapped( img );
  IMG_TYPE I12 = IMG_Type(img);
  char I13[128];

  int k ; 
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\\t" ; 
  TraceFile << "<IMAGE-UNLOAD>" << " I1:" << I1 << " I2:" << I2 << " I3:" << I3 << " I4:" << I4 << " I5:" << hex<< I5 << " I6:"<< I6 << " I7:" << I7 << " I8:" << I8 << " I9:"<< I9  << " I10:"<< I10  << " I11:" << I11 ;

  switch ( I12 )
  {{
  case IMG_TYPE_STATIC:
    strcpy( I13 ,"static" ); break;
  case IMG_TYPE_SHARED:
    strcpy( I13 ,"shared" ); break;
  case IMG_TYPE_INVALID:
    strcpy( I13 ,"invalid" ); break;
  case IMG_TYPE_LAST:
    strcpy( I13 ,"last" ); break;
  case IMG_TYPE_SHAREDLIB:
    strcpy( I13 ,"shared-lib" ); break;
  case IMG_TYPE_RELOCATABLE:
    strcpy( I13 ,"relocatable" ); break;
  #if PIN_PRODUCT_VERSION_MINOR > 12
      case IMG_TYPE_DYNAMIC_CODE:
        strcpy( I13 ,"dynamic-code" ); break;
  #endif
  default:
    strcpy( I13 ,"UNKNOWN" ); break;      
  }}

  TraceFile << " I12:" << I12 << " I13:" << I13 << endl;
  
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\\t" ; 
  TraceFile << "</IMAGE-UNLOAD>" << endl;
    
}}

VOID ImageLoad(IMG img, VOID *v)
{{
  report_image_structure(img, 0 );
}}

VOID ImageUnLoad(IMG img, VOID *v )
{{
  report_image_structure_2(img, 0 );
}}

/* ===================================================================== */

VOID Fini(INT32 code, VOID *v)
{{
    TraceFile.close();
}}

/* ===================================================================== */
/* Process                                                               */
/* ===================================================================== */

BOOL FollowChild(CHILD_PROCESS childProcess, VOID * userData)
{{
    fprintf(stdout, "before child:%u\\n", PID);
    return TRUE;
}}        

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char *argv[])
{{
    // Init sequence pattern array
    init_cnode_array();

    // Initialize pin & symbol manager
    PIN_InitSymbols();
    if( PIN_Init(argc,argv) )
    {{
        return Usage();
    }}
    thread_init();
     
    PIN_AddFollowChildProcessFunction(FollowChild, 0);    
    
    // Write to a file since cout and cerr maybe closed by the application
    TraceFile.open(KnobOutputFile.Value().c_str());
    TraceFile << hex;
    TraceFile.setf(ios::showbase);
    
    // Register Image to be called to instrument functions.
    IMG_AddInstrumentFunction(ImageLoad, 0);
    IMG_AddUnloadFunction(ImageUnLoad, 0);
    TRACE_AddInstrumentFunction(trace_instrument, 0);

    // Never returns
    PIN_StartProgram();
    
    return 0;
}}

/* ===================================================================== */
/* eof */
/* ===================================================================== */

"""
