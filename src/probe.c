#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc,char **argv) {
    if(argc<2) return 2;
    int rc=0;
    if(!strcmp(argv[1],"read")) { int fd=open(argv[2],O_RDONLY); rc=fd<0?-1:0; if(fd>=0) close(fd); }
    else if(!strcmp(argv[1],"write")) { int fd=open(argv[2],O_WRONLY|O_CREAT|O_TRUNC,0600); rc=fd<0?-1:0; if(fd>=0) { if(write(fd,"ok",2)!=2) return 3; close(fd); } }
    else if(!strcmp(argv[1],"socket")) rc=socket(AF_INET,SOCK_STREAM,0);
    else if(!strcmp(argv[1],"fork")) rc=fork();
    else if(!strcmp(argv[1],"ptrace")) rc=(int)ptrace(PTRACE_TRACEME,0,NULL,NULL);
    else if(!strcmp(argv[1],"memory")) {
        volatile size_t bytes=128*1024*1024;
        void *p=malloc(bytes);
        __asm__ volatile("" : : "g"(p) : "memory");
        rc=p?0:-1;
        if(p) ((volatile char*)p)[0]=1;
        free(p);
    }
    else if(!strcmp(argv[1],"files")) { for(int i=0;i<100;i++) if(open(argv[2],O_RDONLY)<0) { rc=-1; break; } }
    else if(!strcmp(argv[1],"disk")) {
        int fd=open("limited.bin",O_WRONLY|O_CREAT,0600); if(fd<0) return 3;
        char data[4096]; memset(data,'x',sizeof(data));
        for(int i=0;i<32;i++) if(write(fd,data,sizeof(data))<0) { rc=-1; break; }
    }
    else if(!strcmp(argv[1],"cpu")) { volatile unsigned long n=0; for(;;) n++; }
    else if(!strcmp(argv[1],"wall")) sleep(10);
    else return 2;
    int error=errno;
    printf("{\"rc\":%d,\"errno\":%d}\n",rc,error);
    return 0;
}
