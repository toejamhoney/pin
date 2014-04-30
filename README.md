Pin Tool Generation using Excipo Relatus
====

This documentation, and the included pin tool is intended for OSX. However, excipo_relatus.py (along with the other modules) are cross platform (as long as it has Python). In order to compile the generated source code, the appropriate pin tool package will need to be downloaded [from Intel](https://software.intel.com/en-us/articles/pin-a-dynamic-binary-instrumentation-tool), and then a makefile target added for whatever you want to name your tool. (The MyPinTool directory is Intel's intended starting point for creating tools quickly and simply.)

We are currently working within the pin tool directory structure. Specifically in the MyPinTool folder.
* pin/src/pin-2.13-62732-clang.4.2-mac/source/tools/MyPinTool/


#### Python package contents and structure
1. The system calls targeted can be found in the baseline.txt files. There are currently *nix \(including Android\) and win32 versions.
    * .../MyPinTool/w32_rtn_baseline.txt
    * .../MyPinTool/nix_rtn_baseline.txt

2. templates.py is the secondary input that provides the string templates for the generated cpp code. It uses the string.format or printf style.

3. extras.py is the ternary input file that specifies:
    * callouts on particular system calls you want to tag/bring attention to
    * sequences of callouts that you want to trigger specific actions \(documentation for sequences is included in extras.py\)
    * *Sequences are still under development, Regex will most likely not be used due to difficulty in a cross platform solution*


#### excipo_relatus (ER) process
1. ER processes the baseline routines (methods) specified in the txt files as prototypes, and inserts them into the generated code. If this file is not specified ER will still generate c++ code, which will compile as a working pin tool, but output will be restricted to image loads and basic runtime execution tracing.
2. ER uses the extras.py file to insert callout code into the strings from the templates module. Basically, if routine(method/function) name == a key in CALLOUTS dictionary then perform actions in 'pre' before call and 'post' after call.
3. Anything specified in sequences will look for specified combinations based on the flags from CALLOUT items.


#### How to generate code

   * cd .../MyPinTool/
   * python excipo_relatus.py -R nix_rtn_baseline.txt -e extras.py TMP.cpp
      * This creates a file called TMP.cpp (which we have added as a target in the makefile)
   * make
      * Make builds the tool in ./obj-intel64/TMP.dylib


#### How to run pin
   * \<path to pin\>/pin -t \<path to tool\>/TMP.dylib -- \<path to executable\>
   * We've included a small test file that opens, writes, closes files, and forks.
   * The file names can be found during execution with the tool
