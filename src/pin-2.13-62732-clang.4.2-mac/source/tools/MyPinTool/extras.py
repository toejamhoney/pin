SEQUENCES = {
            (1,2,3): ('do123', 4),
            (1,1,3): ('do113', 5),
            (1,2): ('do113', 5),
            (3,3,3): ('bar', 6),
            (4,): ('fopen_start', 1),
            (4,-4): ('fopen_done', 1000),
            (4,-6): ('open_closed', 1000),
            }

do123 = """printf("HELLO FROM DO123!!!\\n");"""

do113 = """printf("HELLO FROM DO113!!!\\n");"""

bar = """printf("HELLO FROM BAR!!!\\n");
        printf("HELLO AGAIN! FROM BAR!!!\\n");
"""

fopen_start = """printf("FOPEN going to be called with: %s\\n", (char*)X0);"""
fopen_done = """printf("FOPEN has been called\\n");"""
open_closed = """printf("FOPEN -> FCLOSE: A file was opened and closed\\n");"""

CALLOUTS = { 'DbgPrintEx' : {
        'preflag' : 1,
        'postflag' : -1,
        'global' : '',
        'pre' : 'TraceFile << "bye cruel world" << hex << X0 << dec << endl;',
        'post' : 'TraceFile << "hello world" << endl;',
        },
    'NtOpenFile': {
        'preflag':'2' ,
        'postflag':'-2' ,
        'global':'', #'\n'.join(['#ifdef _WIN32', '#include<WinDef.h>','#include<WinNT.h>', '#include<BaseTsd.h>', "#endif","/* Windows Data Types that are not working even with addt'l inclusions */","typedef unsigned long ULONG;","typedef unsigned short USHORT;","","typedef void *PVOID;","typedef PVOID HANDLE;","","typedef wchar_t WCHAR;","typedef WCHAR *PWSTR;","", 'typedef struct _UNICODE_STRING {','        USHORT Length;','        USHORT MaximumLength;','        PWSTR Buffer;','} UNICODE_STRING, *PUNICODE_STRING;','','typedef struct _OBJECT_ATTRIBUTES {','        ULONG   Length;','        HANDLE RootDirectory;','        PUNICODE_STRING ObjectName;','        ULONG Attributes;','        PVOID SecurityDescriptor;','        PVOID SecurityQualityOfService;','} OBJECT_ATTRIBUTES, *POBJECT_ATTRIBUTES;'] ), 
        'pre' : '\n'.join( [ 'TraceFile << "NTOpenFile" <<endl << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ),
        'post':''
        },
    'NtCreateFile': {
        'preflag': 3,
        'postflag': -3,
        'global' : '',
        'pre': '\n\t'.join( [ 'TraceFile << "NTCreateFile" <<endl;', 'TraceFile << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ), 
        'post':''
        },
    'fopen' : {
        'preflag': 4,
        'postflag': -4,
        'global':'',
        'pre':'\n\t'.join( [ 'TraceFile << "CALL-OUT ENTER <ACTION: OPEN-FILE>: " << name << " ( path=" << hex << (char *)X0 << ", mode=" << (char*)X1 << ")" << dec << endl;' ] ),
        'post':'\n\t'.join( [ 'TraceFile << "CALL-OUT EXIT: "<< name << " RETURN-VALUE @:" << hex << ret << dec << " RETURN-VALUE-INTERP:" << dec << ((int) ret) << endl;', ] )
        },
    'printf' : {
        'preflag': 5,
        'postflag': -5,
        'global':'',
        'pre': '\n\t'.join( ['TraceFile << "CALL-OUT ENTER <ACTION: PRINT>: " << name << " (" << hex << (char *)X0 << "," << X1 << ")" << dec << endl;', ] ),
        'post': '\n\t'.join( ['TraceFile << "CALL-OUT EXIT: " << name << " RETURN-VALUE @: " << hex << ret << dec << " RETURN-VALUE-INTERP: " << dec << ((int) ret) << endl;', ] )
        },
    'fclose' : {
        'preflag': 6,
        'postflag': -6,
        'global':'',
        'pre':'\n\t'.join( [ 'TraceFile << "CALL-OUT ENTER <ACTION: CLOSE-FILE>: " << name << " ( path=" << hex << (char *)X0 << ")" << dec << endl;' ] ),
        'post':'\n\t'.join( ['TraceFile << "CALL-OUT EXIT: " << name << " RETURN-VALUE @: " << hex << ret << dec << " RETURN-VALUE-INTERP: " << dec << ((int) ret) << endl;', ] )
    },
}
