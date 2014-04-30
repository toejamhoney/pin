/*
Author:  Jeff Kramaer, Will Casey

*/
/* ===================================================================== */
/* ===================================================================== */
#include "pin.H"
#include <iostream>
#include <fstream>
#include <iomanip>
/* ===================================================================== */
/* Global Variables */
/* ===================================================================== */


std::ofstream TraceFile;
string invalid = "invalid_rtn";
int stack_count = 0; 
UINT64 icount = 0;
static VOID * WriteAddr;
static INT32 WriteSize;

int record_mem = 0;

/* ===================================================================== */
/* Commandline Switches */
/* ===================================================================== */
KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool", "o", "V4JKW.out", "specify trace file name");
KNOB<BOOL> KnobValues(KNOB_MODE_WRITEONCE, "pintool", "values", "1", "Output memory values reads and written");
KNOB<BOOL>   KnobPrintArgs(KNOB_MODE_WRITEONCE, "pintool", "a", "0", "print call arguments ");
/* ===================================================================== */
/* Print Help Message                                                    */
/* ===================================================================== */
static INT32 Usage(){
    cerr <<
        "This tool produces a memory address trace.\n"
        "For each (dynamic) instruction reading or writing to memory the the ip and ea are recorded\n"
        "\n";

    cerr << KNOB_BASE::StringKnobSummary();

    cerr << endl;

    return -1;
}


/* ===================================================================== */
/* Trace Navigation                                                      */
/* ===================================================================== */
VOID do_count() {
	icount++; }
VOID push_stack( ){
	stack_count ++ ;
}
VOID pop_stack() {
	stack_count --;
}

/* ===================================================================== */                                               
/* Memory I/O record                                                     */
/* ===================================================================== */

static VOID EmitMem(VOID * ea, INT32 size){
    if (!KnobValues)
        return;
    
    switch(size)
    {
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
        {
            TraceFile << static_cast<UINT32>(static_cast<UINT8*>(ea)[i]);
        }
        TraceFile.setf(ios::showbase);
        break;
    }
}
static VOID RecordMem(VOID * ip, CHAR r, VOID * addr, INT32 size, BOOL isPrefetch){
    if ( record_mem ){
    TraceFile << "M\t" << ip << ": " << r << " " << setw(2+2*sizeof(ADDRINT)) << addr << " "
              << dec << setw(2) << size << " "
              << hex << setw(2+2*sizeof(ADDRINT));
    if (!isPrefetch)
        EmitMem(addr, size);
    TraceFile << endl;}
}
static VOID RecordWriteAddrSize(VOID * addr, INT32 size){
    WriteAddr = addr;
    WriteSize = size;
}
static VOID RecordMemWrite(VOID * ip){
    RecordMem(ip, 'W', WriteAddr, WriteSize, false);
}

VOID instruction_instrument(INS ins, VOID *v){
	INS_InsertCall(ins, IPOINT_BEFORE, (AFUNPTR)do_count, IARG_END);
    // instruments loads using a predicated call, i.e.
    // the call happens iff the load will be actually executed
        
    if (INS_IsMemoryRead(ins))
    {
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordMem,
            IARG_INST_PTR,
            IARG_UINT32, 'R',
            IARG_MEMORYREAD_EA,
            IARG_MEMORYREAD_SIZE,
            IARG_BOOL, INS_IsPrefetch(ins),
            IARG_END);
    }

    if (INS_HasMemoryRead2(ins))
    {
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordMem,
            IARG_INST_PTR,
            IARG_UINT32, 'R',
            IARG_MEMORYREAD2_EA,
            IARG_MEMORYREAD_SIZE,
            IARG_BOOL, INS_IsPrefetch(ins),
            IARG_END);
    }

    // instruments stores using a predicated call, i.e.
    // the call happens iff the store will be actually executed
    if (INS_IsMemoryWrite(ins))
    {
        INS_InsertPredicatedCall(
            ins, IPOINT_BEFORE, (AFUNPTR)RecordWriteAddrSize,
            IARG_MEMORYWRITE_EA,
            IARG_MEMORYWRITE_SIZE,
            IARG_END);
        
        if (INS_HasFallThrough(ins))
        {
            INS_InsertCall(
                ins, IPOINT_AFTER, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }
        if (INS_IsBranchOrCall(ins))
        {
            INS_InsertCall(
                ins, IPOINT_TAKEN_BRANCH, (AFUNPTR)RecordMemWrite,
                IARG_INST_PTR,
                IARG_END);
        }
        
    }
}


/* ===================================================================== */
/* Trace instrumentation                                                 */
/* designed to capture call trace and stack navigation movies for        */
/* process execution                                                     */
/* ===================================================================== */
const string *Target2String(ADDRINT target){
    string name = RTN_FindNameByAddress(target);
    if (name == "")
        return &invalid;
    else
        return new string(name);}

VOID  trace_instrument_do_call_in_args(const string *s, ADDRINT arg0){
	TraceFile << "CALL IN:" << dec << stack_count << ":" << dec << icount << ":" << hex << arg0 << ":" << *s << endl;
}
VOID  trace_instrument_do_call_in_args_indirect(ADDRINT target, BOOL taken, ADDRINT arg0){
    if( !taken ) return;
    const string *s = Target2String(target);
    trace_instrument_do_call_in_args(s, arg0);
    if (s != &invalid)
        delete s;
}

VOID  trace_instrument_do_call_out_args(const string *s, ADDRINT arg0){
	TraceFile << "CALL OUT:" << dec << stack_count << ":" << dec << icount << ":" << hex << arg0 << ":" << *s << endl;
}
VOID  trace_instrument_do_call_out_args_indirect(ADDRINT target, BOOL taken, ADDRINT arg0){
    if( !taken ) return;
    const string *s = Target2String(target);
    trace_instrument_do_call_out_args(s, arg0);
    if (s != &invalid)
        delete s;
}

VOID trace_instrument(TRACE trace, VOID *v){

    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl)){ /* iterate over all basic blocks */

	INS head = BBL_InsHead(bbl);
        INS tail = BBL_InsTail(bbl);
	INS cur ;
	TraceFile << "BBL IN: "<< hex << (void *)BBL_Address( bbl ) << endl;
	for ( cur = head; INS_Valid( cur ); cur = INS_Next(cur ) ){
	    TraceFile << hex << INS_Address( cur ) << "\t" << dec << INS_Disassemble( cur ) << endl;
	}
	
        if( INS_IsCall(tail) ){ /* This INS is a call */
	    
	    //INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(push_stack), IARG_END); /* stack navigation */
            
	    if( INS_IsDirectBranchOrCall(tail) ){
                
		const ADDRINT target = INS_DirectBranchOrCallTargetAddress(tail);
                
		INS_InsertPredicatedCall(tail, IPOINT_BEFORE, AFUNPTR(trace_instrument_do_call_in_args), IARG_PTR, Target2String(target), IARG_G_ARG0_CALLER, IARG_END);                

            }else{
                
		INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(trace_instrument_do_call_in_args_indirect), IARG_BRANCH_TARGET_ADDR, IARG_BRANCH_TAKEN,  IARG_G_ARG0_CALLER, IARG_END);}
	    
        } else {
	
	    if ( INS_IsRet( tail ) ){
		INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(pop_stack), IARG_END); /* stack navigation */ 
	    } else {
		// sometimes code is not in an image
		RTN rtn = TRACE_Rtn(trace);
		// also track stup jumps into share libraries 
		if( RTN_Valid(rtn) && !INS_IsDirectBranchOrCall(tail) && ".plt" == SEC_Name( RTN_Sec( rtn ) ))
		{
		    //INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(push_stack), IARG_END);
		    INS_InsertCall(tail, IPOINT_BEFORE, AFUNPTR(trace_instrument_do_call_out_args_indirect),
				   IARG_BRANCH_TARGET_ADDR, IARG_BRANCH_TAKEN,  IARG_G_ARG0_CALLER, IARG_END);
		}
	    }
        }
    }
}

/* ===================================================================== */
/* Finialize                                                             */
/* ===================================================================== */

VOID Fini(INT32 code, VOID *v){
    TraceFile << "#eof" << endl;    
    TraceFile.close();
}

/* ===================================================================== */
/* Main                                                                  */
/* ===================================================================== */

int main(int argc, char *argv[]){
    PIN_InitSymbols();
	
    string trace_header = string("#\n"
                                 "# Memory Access Trace Generated By Pin\n"
								 "# Author: Jeff Kramer, Will Casey 2012\n"
                                 "#\n");
    
    if( PIN_Init(argc,argv) ){
        return Usage(); }
    
    TraceFile.open(KnobOutputFile.Value().c_str());  /* open trace file for output */
    TraceFile.write(trace_header.c_str(),trace_header.size()); /* dump execution trace header */
    TraceFile.setf(ios::showbase); 
    
    TRACE_AddInstrumentFunction(trace_instrument, 0);
    INS_AddInstrumentFunction(instruction_instrument, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Never returns

    PIN_StartProgram();
    
    RecordMemWrite(0);
    RecordWriteAddrSize(0, 0);
    
    return 0;
}

/* ===================================================================== */
/* eof */
/* ===================================================================== */
