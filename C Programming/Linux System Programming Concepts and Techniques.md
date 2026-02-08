Linux System Programming Concepts and Techniques 

C Review:
    [C in 100 Seconds]{https://www.youtube.com/watch?v=U3aXWizDbQ4&pp=ygUSZ2x1ZSBjIHByb2dyYW1taW5n}
    [C Programming Language - Intro to Computer Science - Harvard's CS50 (2018)]{https://www.youtube.com/watch?v=ix5jPkxsr7M&pp=ygUSZ2x1ZSBjIHByb2dyYW1taW5n}

Forward declaration 
Declare struct (at top)
When use, make a pointer


Header File
#define <>
#define “”
For locally defined 

Libraries
source code (.c) + header code (.h)
Collection of compiled objects (.o)
Static (.a) or Dynamic (.so) Libraries
Naming Convention:
lib<library_name>.a
lib<library_name>.so
Terminal Command - Static Library:
gcc -c a.o -o a.o
gcc -c b.o -o b.o
ar rs lib<library_name>.a a.o b.o
Terminal Command - Dynamic Library
gcc -c -fPIC a.c -o a.o
gcc -c -fPIC b.c -o b.o
gcc a.o b.o - shared -o lib<library_name>.so
Terminal Command - Final Executable - Static
gcc -c application.c -o application.o
gcc application.o -o exe -L . -l<library_name>
Run Executable: ./exe 
Terminal Command - Final Executable Dynamic
gcc -c application.c -o application.o
Place the lib<library_name>.so in the default location /usr/lib
Run: sudo ldconfig
gcc application.o -o exe -l<library_name>
Run Executable: ./exe 

Four Stages of Compilation Process
Preprocessing —> text substituted src files
Compilation —> assembly code
Assembler —> machine code
Linking —> executable

Makefile
Rules
Format: 
target: dependencies
            <TAB>command
Target: What we want to prepare (final dish)
Dependencies: What raw materials do we need to prepare for the final dish
Command: Action / Steps to prepare 

Iterative Macros

Glue Based Data Structures

Bit Programming

Machine Endiannes (Big Endian and Little Endian)
Example:	0x12345678
Big Endian: 	12 34 56 78
Little Endian: 	78 56 34 12

TLV Based Communication

POSIX Timers
timer_create()
timer_settime()
timer_gettime()
timer_delete()


Memory Layout of Linx Process
    [Memory Segments in C/C++]{https://www.youtube.com/watch?v=2htbIR2QpaM&pp=ygUWbWVtb3J5IG1hbmFnZW1lbnQgaW4gYw%3D%3D}
    [C Programming and Memory Management - Full Course]{https://www.youtube.com/watch?v=rJrd2QMVbGM&t=7559s&pp=ygUWbWVtb3J5IG1hbmFnZW1lbnQgaW4gY9IHCQmRCgGHKiGM7w%3D%3D}

Stack Memory Management

    (Upside Down Image)
    CPU Registers
    eip:  Instruction Pointer Register (Address of next instructions)
    esp: Stack Pointer Register (Address if top of stack)
    ebp: Base Pointer Register (starting Address in calle’s stack frame)
    Eax: Return Register

Heap Memory Management
    malloc(): claim memory size
    free(): release memory size
    calloc(): 
    realloc(): modify claimed memory size
    System Calls:
    brk(): expand heap memory
    sbrk(): expand heap memory, return old value of break pointer
    MMU: converts Virtual Address to Physical Address
    Break pointer: top of the Heap Stack
    Internal Fragmentation:
    External Fragmentation:
