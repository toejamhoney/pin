SEQUENCES = """
// This is a comment, this /* is not a comment. */ Single lines only.
// All sequences start with sequence:<name>
sequence:21
// The next line is the regular expression
(2)(-1)$
// Second line is the suffix length
0
// Third is the valid C code to be performed. All lines before the next
// sequence, else:, or EOF will be inserted.
TraceFile << "REGEX MATCHED 2,1$" << endl;
// Optional fourth and on is the else block if the regular expression fails
else:
TraceFile << "REGEX FAILED 2,1$" << endl;
// Blank lines are ok

sequence:22
(2)(2)$
2
TraceFile << "REGEX MATCH 2,2$" << endl;
else:
TraceFile << "REGEX FAILED 2,2$" << endl;
sequence:-21
(-2)(1)$
1
TraceFile << "REGEX IMPOSSIBLE MATCH -2,1$" << endl;
else:
TraceFile << "REGEX FAILED IMPOSSIBLE MATCH -2,1$ of suffix length 1" << endl;
sequence:-21real
(-2)(1)$
3
TraceFile << "REGEX MATCH -2,1$" << endl;
else:
TraceFile << "REGEX FAILED -2,1$" << endl;
"""

CALLOUTS = { 'DbgPrintEx' : {
        'preflag' : 8,
        'postflag' : 8,
        'global' : '',
        'pre' : 'TraceFile << "bye cruel world" << hex << X0 << dec << endl;',
        'post' : 'TraceFile << "hello world" << endl;',
        },
    'NtOpenFile': {
        'preflag':'1a' ,
        'postflag':'1b' ,
        'global':'', #'\n'.join(['#ifdef _WIN32', '#include<WinDef.h>','#include<WinNT.h>', '#include<BaseTsd.h>', "#endif","/* Windows Data Types that are not working even with addt'l inclusions */","typedef unsigned long ULONG;","typedef unsigned short USHORT;","","typedef void *PVOID;","typedef PVOID HANDLE;","","typedef wchar_t WCHAR;","typedef WCHAR *PWSTR;","", 'typedef struct _UNICODE_STRING {','        USHORT Length;','        USHORT MaximumLength;','        PWSTR Buffer;','} UNICODE_STRING, *PUNICODE_STRING;','','typedef struct _OBJECT_ATTRIBUTES {','        ULONG   Length;','        HANDLE RootDirectory;','        PUNICODE_STRING ObjectName;','        ULONG Attributes;','        PVOID SecurityDescriptor;','        PVOID SecurityQualityOfService;','} OBJECT_ATTRIBUTES, *POBJECT_ATTRIBUTES;'] ), 
        'pre' : '\n'.join( [ 'TraceFile << "NTOpenFile" <<endl << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ),
        'post':''
        },
    'NtCreateFile': {
        'preflag': '2a',
        'postflag':'2b' ,
        'global' : '',
        'pre': '\n\t'.join( [ 'TraceFile << "NTCreateFile" <<endl;', 'TraceFile << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ), 
        'post':''
        },
    'fopen' : {
        'preflag':1,
        'postflag':1,
        'global':'',
        'pre':'\n\t'.join( [ 'TraceFile << "CALL-OUT ENTER <ACTION: OPEN-FILE>: " << name << " ( path=" << hex << (char *)X0 << ", mode=" << (char*)X1 << ")" << dec << endl;' ] ),
        'post':'\n\t'.join( [ 'TraceFile << "CALL-OUT EXIT: "<< name << " RETURN-VALUE @:" << hex << ret << dec << " RETURN-VALUE-INTERP:" << dec << ((int) ret) << endl;', ] )
        },
    'printf' : {
        'preflag':2,
        'postflag':2,
        'global':'',
        'pre': '\n\t'.join( ['TraceFile << "CALL-OUT ENTER <ACTION: PRINT>: " << name << " (" << hex << (char *)X0 << "," << X1 << ")" << dec << endl;', ] ),
        'post': '\n\t'.join( ['TraceFile << "CALL-OUT EXIT: " << name << " RETURN-VALUE @: " << hex << ret << dec << " RETURN-VALUE-INTERP: " << dec << ((int) ret) << endl;', ] )
        },
    'fclose' : {
        'preflag':3,
        'postflag':3,
        'global':'',
        'pre':'\n\t'.join( [ 'TraceFile << "CALL-OUT ENTER <ACTION: CLOSE-FILE>: " << name << " ( path=" << hex << (char *)X0 << ")" << dec << endl;' ] ),
        'post':'\n\t'.join( ['TraceFile << "CALL-OUT EXIT: " << name << " RETURN-VALUE @: " << hex << ret << dec << " RETURN-VALUE-INTERP: " << dec << ((int) ret) << endl;', ] )
    },
}
