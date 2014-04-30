/* ===================================================================== */
/* This example demonstrates finding a function by name on Windows.      */
/* ===================================================================== */

#include "pin.H"
#include <iostream>
#include <fstream>
#include <stdio.h>
#include <unistd.h>


/* ===================================================================== */
/* Global Variables */
/* ===================================================================== */

UINT64 icount = 0;
UINT64 slp_count = 0;  //codelet count.
std::ofstream TraceFile;
string invalid = "UNKNOWN-SYM";

#define PID LEVEL_PINCLIENT::PIN_GetPid()
#define TID LEVEL_PINCLIENT::PIN_ThreadId()

#define TICUB 2048 
UINT64 ticount[TICUB];

VOID thread_init(){
    int tic = 0;
    for ( tic = 0 ; tic < TICUB ; tic ++ ){
	ticount[tic] = 0;
    }
}

VOID do_count(ADDRINT X ){
  icount++; 
  TraceFile << ":::[" << PID << "." << TID << "] " << dec << icount <<"\t"<< hex << X << endl;
}

VOID string_report(const string *s){
  TraceFile.write(s->c_str(), s->size());
}

/* ===================================================================== */
/* Commandline Switches */
/* ===================================================================== */

KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool",
    "o", "map_syms.out", "specify trace file name");
KNOB<BOOL>   KnobNoCompress(KNOB_MODE_WRITEONCE, "pintool",
    "no_compress", "0", "Do not compress");

/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */

INT32 Usage()
{
    cerr << "This tool produces a trace of calls to RtlAllocateHeap.";
    cerr << endl << endl;
    cerr << KNOB_BASE::StringKnobSummary();
    cerr << endl;
    return -1;
}

/* ===================================================================== */
/* Analysis routines                                                     */
/* ===================================================================== */
/* 
VOID Before(CHAR * name, WINDOWS::HANDLE hHeap,
            WINDOWS::DWORD dwFlags, WINDOWS::DWORD dwBytes) 
{
    TraceFile << "Before: " << name << "(" << hex << hHeap << ", "
              << dwFlags << ", " << dwBytes << ")" << dec << endl;
}

VOID After(CHAR * name, ADDRINT ret)
{
    TraceFile << "After: " << name << "  returns " << hex
              << ret << dec << endl;
}
*/


/* EXAMPLE ANALYSIS CODE */
VOID pre_printf(CHAR * name, void * X0 , void * X1 ) 
{
    /* BASELINE */
    TraceFile << "IN (PID:"<< PID << ",TID:" << TID << "): " << name << " (" << hex << X0 << ","<< X1 << ")" << dec << endl;
    /* callout */
    TraceFile << "CALL-OUT IN: " << name << " (" << hex << (char *)X0 << ","<< X1 << ")" << dec << endl;
    printf( "\n%s ( %s, %p )", name, (char*)X0, X1 );
}

VOID post_printf( CHAR * name, ADDRINT ret ){
    /* BASELINE */
    TraceFile << "OUT: " << name << " RETURN-VALUE @:" << hex << ret << endl;
    /* callout */
    TraceFile << "CALL-OUT OUT: "<< name << " RETURN-VALUE @:" << hex << ret << dec << " RETURN-VALUE-INTERP:" << dec << ((int) ret ) << endl; 
}


VOID pre_fopen(CHAR * name, void * X0 , void * X1 ) 
{
    /* BASELINE */
    TraceFile << "IN: " << name << " (" << hex << X0 << ","<< X1 << ")" << dec << endl;
    /* callout */
    TraceFile << "CALL-OUT <ACTION: OPEN-FILE> IN: " << name << " ( path=" << hex << (char *)X0 << ", mode="<< (char*)X1 << ")" << dec << endl;
    printf( "\n[[action:open file]] %s (path=%s, action=%s )", name, (char*)X0, (char*)X1 );
}

VOID post_fopen( CHAR * name, ADDRINT ret ){
    /* BASELINE */
    TraceFile << "OUT: " << name << " RETURN-VALUE @:" << hex << ret << endl;
    /* callout */
    TraceFile << "CALL-OUT OUT: "<< name << " RETURN-VALUE @:" << hex << ret << dec << " RETURN-VALUE-INTERP:" << dec << ((int) ret ) << endl; 
}


/* ===================================================================== */
/* Instrumentation routines                                              */
/* ===================================================================== */

VOID instruction_instrument(INS ins, VOID *v){
  INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)do_count, IARG_ADDRINT, INS_Address( ins ), IARG_END);
  int MEM = 0;
  /* capture memory I/O here also */
  if ( MEM ){
    ;
  }
}

/* ===================================================================== */
/* Trace routines                                                        */
/* ===================================================================== */

const string *Target2String(ADDRINT target)
{
    string name = RTN_FindNameByAddress(target);
    if (name == "")
      return &invalid;
    else
      return new string(name);
}

VOID trace_instrument(TRACE trace, VOID *v){
  for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl)){ 
    /* iterate over all basic blocks */
    
    string codelet_string = "";
    // this writes disassembly 
    char codelet_buffer[65536*2]; int cbs = 0;
    INS head = BBL_InsHead(bbl);
    INS tail = BBL_InsTail(bbl);
    
    ADDRINT stage_entry = INS_Address( head );
    ADDRINT target = 0;
    if (INS_IsCall(tail)){
      if( INS_IsDirectBranchOrCall(tail)){
        target = INS_DirectBranchOrCallTargetAddress(tail);}}

    INS cur ;
    int branch_id = slp_count;
      
    /* If compression is turned off (default), only output the addresses of
     * the BBL once
     */
    if (!KnobNoCompress){
      /* Instrument the head instruction right before it is called, but also
       * before we instrument the instructions in the basic block 
       */
      string msg_pre  = "\n@@BBL(" + decstr( branch_id ) + ") STAGE " + Target2String(stage_entry)->c_str() + "\n" ;
      INS_InsertCall(head, IPOINT_BEFORE, AFUNPTR(string_report),
		     IARG_PTR, new string(msg_pre),
		     IARG_END);
    }
   
    /* Walk the list of instructions inside the BBL. Disassemble each, and add
     * it to the codelet string. Also, instrument each instruction at the
     * point before it is called with the do_count function.
     */
    for ( cur = head; INS_Valid( cur ); cur = INS_Next(cur ) ){
      cbs += sprintf( codelet_buffer + cbs , "\n\t@%llx\t%s", INS_Address( cur ), INS_Disassemble( cur ).c_str() );
      INS_InsertCall(cur, IPOINT_BEFORE, (AFUNPTR)do_count, IARG_ADDRINT, INS_Address( cur ), IARG_END);
    }

    /* Finish off the codelet assembly string with an out message and
     * address ranges of the BBL
     */
    cbs += sprintf( codelet_buffer + cbs , "\n\t}BBL.OUT [%d] %llx - %llx\n", branch_id, INS_Address( head ), INS_Address( tail ));
  
    /* If compression is turned on, output the codelet every single time we
     * hit the same block.
     */
    if(KnobNoCompress){
      INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(string_report),
		     IARG_PTR, new string(codelet_buffer),
		     IARG_END);
      slp_count ++;
    }
    else{
      /* add the mapped BBL to output */
      TraceFile.write(codelet_buffer, cbs);	
 
      /* Instrument the tail instruction by inserting just before it is called
      */
      string msg_post = "+@@BBL(" + decstr( branch_id ) + ") ACHIEVE : GOTO " + Target2String(target)->c_str();
      INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(string_report),
		     IARG_PTR, new string(msg_post),
		     IARG_END);

      slp_count ++;
    }
  }
}


/* ===================================================================== */
/* Image Mapping routines                                                */
/* ===================================================================== */



void report_sym_structure( SYM sym, int depth )
{
  // TODO
  int k = 0;
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "<SYM>";
  
  string sym_1 = PIN_UndecorateSymbolName(SYM_Name(sym), UNDECORATION_NAME_ONLY);
  string sym_2 = PIN_UndecorateSymbolName(SYM_Name(sym), UNDECORATION_COMPLETE );
  ADDRINT offset  = SYM_Value( sym );	
  TraceFile << hex << offset << " sym.1:" << sym_1 << " sym.2:" << sym_2 << "</SYM>" << endl;
}



void report_routine_structure( RTN rtn , int depth){
  /*
    const string & 	LEVEL_PINCLIENT::RTN_Name (RTN x)
    SYM 	LEVEL_PINCLIENT::RTN_Sym (RTN x)
    AFUNPTR 	LEVEL_PINCLIENT::RTN_Funptr (RTN x)
    INT32 	LEVEL_PINCLIENT::RTN_Id (RTN x)
    USIZE 	LEVEL_PINCLIENT::RTN_Range (RTN rtn)
    USIZE 	LEVEL_PINCLIENT::RTN_Size (RTN rtn)
    ADDRINT 	LEVEL_PINCLIENT::RTN_Address (RTN rtn)
  */      
  string R1 = LEVEL_PINCLIENT::RTN_Name (rtn );  
  //  SYM  R2 = 	LEVEL_PINCLIENT::RTN_Sym (rtn );
  AFUNPTR R3 =LEVEL_PINCLIENT::RTN_Funptr (rtn);
  INT32 R4 = 	LEVEL_PINCLIENT::RTN_Id (rtn );
  USIZE R5 =	LEVEL_PINCLIENT::RTN_Range ( rtn);
  USIZE R6 = 	LEVEL_PINCLIENT::RTN_Size ( rtn);
  ADDRINT R7 =	LEVEL_PINCLIENT::RTN_Address ( rtn);
  string r2_1 = "";
  string r2_2 = "";
  int k = 0;
  //  string r2_1 = PIN_UndecorateSymbolName(SYM_Name(R2), UNDECORATION_NAME_ONLY);
  //  string r2_2 = PIN_UndecorateSymbolName(SYM_Name(R2), UNDECORATION_COMPLETE );
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "<ROUTINE> R1:" << R1 << " R2.1:" << r2_1 << " R2.2" << r2_2 << " R3:" << R3 << " R4:" << R4 << " R5:" << R5 << " R6:" << R6 << " R7:" << R7 << "</ROUTINE>" << endl;

  // Removed this as duplicate closing tag insertion
}

void report_section_structure(SEC sec, int depth ){
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

  switch ( S3 ){
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
  }
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "<SECTION>S1:" << S1 << " S2:" << S2 << " S3:" << S3 << " S4:" << S4 << " S5:" << S5 << " S6:" << S6 << " S7:" << S7 << " S8:" << S8 << " S9:" << S9 << " Stype:" << sec_type << endl;

  for( RTN rtn= SEC_RtnHead(sec); RTN_Valid(rtn); rtn = RTN_Next(rtn) ){
    report_routine_structure( rtn, depth + 1  );
    string R1 = LEVEL_PINCLIENT::RTN_Name (rtn );  
    /* string undFuncName = PIN_UndecorateSymbolName(SYM_Name(R2), UNDECORATION_NAME_ONLY);*/
    //RTN allocRtn = RTN_FindByAddress(IMG_LowAddress(img) + SYM_Value(sym));

    if (R1 == "_printf"){ /* have to check '__' entry for symbols */
      RTN_Open( rtn );
      RTN_InsertCall(rtn, IPOINT_BEFORE, (AFUNPTR)pre_printf,
		     IARG_ADDRINT, "THECALL:::printf",
		     IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
		     IARG_FUNCARG_ENTRYPOINT_VALUE, 1,
		     IARG_END);
      RTN_InsertCall(rtn, IPOINT_AFTER, (AFUNPTR)post_printf,
		     IARG_ADDRINT, "THECALL:::printf",
		     IARG_FUNCRET_EXITPOINT_VALUE, //REFERENCE, 
		     IARG_END);
      RTN_Close( rtn );      
      printf( ">>>>>>>>>>>>>>>>>>>>>>>> printf" );}

    if (R1 == "_fopen"){ /* have to check '__' entry for symbols */
      RTN_Open( rtn );
      RTN_InsertCall(rtn, IPOINT_BEFORE, (AFUNPTR)pre_fopen,
		     IARG_ADDRINT, "THECALL:::fopen",
		     IARG_FUNCARG_ENTRYPOINT_VALUE, 0,
		     IARG_FUNCARG_ENTRYPOINT_VALUE, 1,
		     IARG_END);      
      RTN_InsertCall(rtn, IPOINT_AFTER, (AFUNPTR)post_fopen,
		     IARG_ADDRINT, "THECALL:::fopen",
		     IARG_FUNCRET_EXITPOINT_VALUE, //REFERENCE, 
		     IARG_END);      
      RTN_Close( rtn );

      
      printf( ">>>>>>>>>>>>>>>>>>>>>>>> fopen" );}


  }

  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "</SECTION>" << endl;
}
  

void report_image_structure(IMG img, int depth){
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

  switch ( I12 ){
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
  case IMG_TYPE_DYNAMIC_CODE:
    strcpy( I13 ,"dynamic-code" ); break;
  default:
    strcpy( I13 ,"UNKNOWN" ); break;      }

  TraceFile << " I12:" << I12 << " I13:" << I13 << endl;

  for( SEC sec = IMG_SecHead(img); SEC_Valid(sec); sec = SEC_Next(sec) ){
    report_section_structure( sec, depth + 1   ); 
  }

  /* */

  for (SYM sym = IMG_RegsymHead(img); SYM_Valid(sym); sym = SYM_Next(sym)){
    report_sym_structure( sym, depth +1 );
  }
 
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "</IMAGE-LOAD>" << endl;
}

void report_image_structure_2(IMG img, int depth){
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
  TraceFile << "<IMAGE-UNLOAD>" << " I1:" << I1 << " I2:" << I2 << " I3:" << I3 << " I4:" << I4 << " I5:" << hex<< I5 << " I6:"<< I6 << " I7:" << I7 << " I8:" << I8 << " I9:"<< I9  << " I10:"<< I10  << " I11:" << I11 ;

  switch ( I12 ){
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
  case IMG_TYPE_DYNAMIC_CODE:
    strcpy( I13 ,"dynamic-code" ); break;
  default:
    strcpy( I13 ,"UNKNOWN" ); break;      }

  TraceFile << " I12:" << I12 << " I13:" << I13 << endl;
  
  for ( k = 0; k< depth ; k ++ )
    TraceFile << "\t" ; 
  TraceFile << "</IMAGE-UNLOAD>" << endl;
    
}

   
VOID ImageLoad(IMG img, VOID *v)
{
  report_image_structure(img, 0 );
}

VOID ImageUnLoad(IMG img, VOID *v )
{
  report_image_structure_2(img, 0 );
}

/* ===================================================================== */

VOID Fini(INT32 code, VOID *v)
{
    TraceFile.close();
}

/* ===================================================================== */
/* Process                                                               */
/* ===================================================================== */


BOOL FollowChild(CHILD_PROCESS childProcess, VOID * userData)
{
    fprintf(stdout, "before child:%u\n", getpid());
    return TRUE;
}        

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */


int main(int argc, char *argv[])
{
    // Initialize pin & symbol manager
    PIN_InitSymbols();
    if( PIN_Init(argc,argv) )
    {
        return Usage();
    }
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

    PIN_AddFiniFunction(Fini, 0);

    // Never returns
    PIN_StartProgram();
    
    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */
