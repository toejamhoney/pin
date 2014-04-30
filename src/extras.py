{
    'DbgPrintEx' : {
        'flag' : 8,
        'global' : '',
        'pre' : 'TraceFile << "bye cruel world" << hex << X0 << dec << endl;',
        'post' : 'TraceFile << "hello world" << endl;',
        },
    'NtOpenFile': {
        'flag':8 ,
        'global':'\n'.join(['#include<WinDef.h>','#include<WinNT.h>', '#include<BaseTsd.h>',"/* Windows Data Types that are not working even with addt'l inclusions */","typedef unsigned long ULONG;","typedef unsigned short USHORT;","","typedef void *PVOID;","typedef PVOID HANDLE;","","typedef wchar_t WCHAR;","typedef WCHAR *PWSTR;","", 'typedef struct _UNICODE_STRING {','        USHORT Length;','        USHORT MaximumLength;','        PWSTR Buffer;','} UNICODE_STRING, *PUNICODE_STRING;','','typedef struct _OBJECT_ATTRIBUTES {','        ULONG   Length;','        HANDLE RootDirectory;','        PUNICODE_STRING ObjectName;','        ULONG Attributes;','        PVOID SecurityDescriptor;','        PVOID SecurityQualityOfService;','} OBJECT_ATTRIBUTES, *POBJECT_ATTRIBUTES;'] ), 
        'pre' : '\n'.join( [ 'TraceFile << "NTOpenFile" <<endl << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ),
        'post':''
        },
    'NtCreateFile': {
        'flag': 8,
        'global' : '',
        'pre': '\n\t'.join( [ 'TraceFile << "NTCreateFile" <<endl;', 'TraceFile << "    PHANDLE " << (unsigned long) X0 << endl << "    ACCESS_MASK " << (unsigned long) X1 << endl << "    POBJECT_ATTRIBUTES " << (unsigned long) X2 << endl << "    PIO_STATUS_BLOCK " << (unsigned long) X3 << endl << "    ULONG " << (unsigned long) X4 << endl << "    ULONG " << (unsigned long) X5 << endl;' , 'PUNICODE_STRING ObjName = ((POBJECT_ATTRIBUTES)X2)->ObjectName;', 'USHORT len = ObjName->Length;', 'USHORT max_len = ObjName->MaximumLength;', 'TraceFile << "    ObjName->Length: " << len << endl;', 'TraceFile << "    ObjName->MaximumLength: " << max_len << endl;', 'char file_name[256] = {0};', 'PWSTR buff = ObjName->Buffer;', 'wcstombs(file_name, buff, 256);', 'TraceFile << "        ObjName->Buffer: " << buff << endl;', 'TraceFile << "        file_name: " << file_name << endl;', 'TraceFile << "        " << (char*)((POBJECT_ATTRIBUTES)X2)->ObjectName << endl;' ] ), 
        'post':''
        }    
}



