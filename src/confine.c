#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/landlock.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

static void die(const char *what) { perror(what); exit(125); }
static void limit(int kind, rlim_t soft, rlim_t hard) {
    struct rlimit value={soft,hard}; if(setrlimit(kind,&value)) die("setrlimit");
}
static void allow_path(int rules,const char *path,uint64_t access) {
    int fd=open(path,O_PATH|O_CLOEXEC); if(fd<0) die(path);
    struct landlock_path_beneath_attr rule={.allowed_access=access,.parent_fd=fd};
    if(syscall(SYS_landlock_add_rule,rules,LANDLOCK_RULE_PATH_BENEATH,&rule,0)) die("landlock_add_rule");
    close(fd);
}
#define ALLOW(n) BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,SYS_##n,0,1),BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ALLOW)
static void seccomp_filter(void) {
    struct sock_filter code[]={
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,arch)),
        BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K,AUDIT_ARCH_X86_64,1,0),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD|BPF_W|BPF_ABS,offsetof(struct seccomp_data,nr)),
        // Only exact native syscall numbers are allowed; x32 numbers fail closed.
        ALLOW(read),ALLOW(write),ALLOW(close),ALLOW(fstat),ALLOW(newfstatat),
        ALLOW(mmap),ALLOW(mprotect),ALLOW(munmap),ALLOW(brk),ALLOW(mremap),
        ALLOW(rt_sigaction),ALLOW(rt_sigprocmask),ALLOW(rt_sigreturn),
        ALLOW(pread64),ALLOW(access),ALLOW(execve),ALLOW(exit),ALLOW(exit_group),
        ALLOW(arch_prctl),ALLOW(set_tid_address),ALLOW(set_robust_list),
        ALLOW(prlimit64),ALLOW(getrandom),ALLOW(rseq),ALLOW(futex),
        ALLOW(clock_gettime),ALLOW(clock_nanosleep),ALLOW(nanosleep),
        ALLOW(getpid),ALLOW(gettid),ALLOW(getcwd),ALLOW(readlink),ALLOW(readlinkat),
        ALLOW(openat),ALLOW(lseek),ALLOW(madvise),ALLOW(uname),ALLOW(fcntl),
        ALLOW(getuid),ALLOW(geteuid),ALLOW(getgid),ALLOW(getegid),ALLOW(fsync),
        BPF_STMT(BPF_RET|BPF_K,SECCOMP_RET_ERRNO|(EPERM&SECCOMP_RET_DATA))
    };
    struct sock_fprog program={.len=(unsigned short)(sizeof(code)/sizeof(code[0])),.filter=code};
    if(prctl(PR_SET_SECCOMP,SECCOMP_MODE_FILTER,&program)) die("seccomp");
}
int main(int argc,char **argv) {
    int abi=(int)syscall(SYS_landlock_create_ruleset,NULL,0,LANDLOCK_CREATE_RULESET_VERSION);
    if(argc==2) { printf("{\"landlock_abi\":%d,\"arch\":\"x86_64\"}\n",abi); return abi>=3?0:125; }
    if(argc<4 || abi<3) { fprintf(stderr,"usage: confine SCRATCH WORKER [ARGS...] (Landlock ABI >=3 required)\n"); return 125; }
    if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)) die("no_new_privs");
    uint64_t handled=(1ULL<<15)-1; // all filesystem rights through ABI 3, including TRUNCATE
    struct landlock_ruleset_attr attr={.handled_access_fs=handled};
    int rules=(int)syscall(SYS_landlock_create_ruleset,&attr,sizeof(attr),0); if(rules<0) die("landlock_create_ruleset");
    uint64_t readonly=LANDLOCK_ACCESS_FS_READ_FILE|LANDLOCK_ACCESS_FS_READ_DIR|LANDLOCK_ACCESS_FS_EXECUTE;
    allow_path(rules,"/usr/lib",readonly);
    // /lib and /lib64 may resolve to the same inode: duplicate allow rules are harmless.
    if(access("/lib",F_OK)==0) allow_path(rules,"/lib",readonly);
    if(access("/lib64",F_OK)==0) allow_path(rules,"/lib64",readonly);
    allow_path(rules,argv[2],LANDLOCK_ACCESS_FS_READ_FILE|LANDLOCK_ACCESS_FS_EXECUTE);
    allow_path(rules,argv[1],handled&~(LANDLOCK_ACCESS_FS_EXECUTE|LANDLOCK_ACCESS_FS_MAKE_CHAR|LANDLOCK_ACCESS_FS_MAKE_BLOCK|LANDLOCK_ACCESS_FS_MAKE_SOCK));
    if(syscall(SYS_landlock_restrict_self,rules,0)) die("landlock_restrict_self");
    close(rules);
    limit(RLIMIT_AS,64*1024*1024,64*1024*1024); limit(RLIMIT_NOFILE,32,32);
    limit(RLIMIT_FSIZE,32768,32768); limit(RLIMIT_CPU,1,2); limit(RLIMIT_CORE,0,0);
    // No inherited descriptors except stdin/out/err, then a strict syscall allowlist.
    if(syscall(SYS_close_range,3,~0U,0)<0) die("close_range");
    if(chdir(argv[1])) die("chdir");
    seccomp_filter();
    char *const env[]={"LANG=C","LC_ALL=C",NULL};
    execve(argv[2],&argv[2],env); die("execve");
}
