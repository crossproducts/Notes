<h1>Udemy: Introduction to System Programming in C</h1>

File Manipulation System Calls
Create: 	open()
Delete:		remove()
Read: 		read()
Write:		write()
Reposition:	lseek()
Close:		close()


Groups: 	Special	User		Group  	Other
Permissions:	Read: 4 	Read: 4	Read: 4	Read: 4
Write: 2	Write: 2	Write: 2	Write: 2
Execute: 1	Execute: 1	Execute: 1	Execute: 1

Flags - $man 2 …


Processes
int fork(void)
Description: Create child process
Returns: process ID of the new process
Notes:
Parent continue w/ PID from before
Child continue w/ PID = 0
int execv(char *progName, char *argv[])
Description: load program in process address space
Returns: -1 if failed
Notes:
Parent continue w/ PID from before
Child new w/ PID = 0
void exit(int returnCode)
Description: terminate process
Returns: none
Notes:
int wait(int *returnCode)
Description: await process completion
Returns: process ID of process that exited
Notes:
Waits for child process to finish executing

Threads  (pthreads)
Allows a process to perform more than one task at a time

Core Functions
pthread_create()
pthread_create(&thread, NULL, func, arg);
Create a thread

pthread_join()
pthread_join(thread, &retval);
Wait for a thread to finish

pthread_exit()
pthread_exit(NULL);
Exit a thread explicitly

pthread_detach()
pthread_detach(thread);
Detach (no join needed)

Thread Identification Functions
pthread_self()
pthread_equal()

Mutexes Functions
pthread_mutex_init()
pthread_mutex_lock()
pthread_mutex_unlock()
pthread_mutex_destroy()

Conditional Variables Functions
pthread_cond_init()
pthread_cond_wait()
pthread_cond_signal()
pthread_cond_broadcast()
pthread_cond_destroy()

Synchronization with Semaphores 

Critical Section
section of code where only 1 process or thread should run at a time 

Semaphores
Control access to shared data
Prevents:
Race Conditions
Corrupted data
Undefined behavior 
Problems:
Bounding Buffers
Reader -  Writer
Dining - Philosopher 
Sleeping - Barber
etc
#include <semaphore.h>
signal()
Increments the counter
Wakes up waiting threads
wait()
Decrements the counter
If counter < 0 → block
Common sem operations 
sem_init()
sem_wait()
sem_post()
sem_destroy()
Mental model 🧠
A semaphore is like tokens:
sem_wait() = take a token
sem_post() = put a token back
No token? You wait.

