/* Linux x86-64 entry point. Give the shell the actual binary path so a menu
   launch, PATH lookup or symlink also locates the bundled interpreter. */
.section .rodata
self:    .asciz "/proc/self/exe"
shell:   .asciz "/bin/sh"
option:  .asciz "-c"
command: .asciz "d=${0%/*}; exec \"$d/runtime/bin/python3\" -EsB \"$d/launcher.py\" \"$@\""
.section .bss
path:    .skip 4096
.section .text
.global _start
_start:
    mov %rsp, %r12
    mov $89, %eax                  /* readlink */
    lea self(%rip), %rdi
    lea path(%rip), %rsi
    mov $4095, %edx
    syscall
    cmp $0, %rax
    jle failed
    cmp $4095, %rax
    je failed
    mov (%r12), %rcx               /* argc */
    lea 16(%r12,%rcx,8), %rdx      /* original environment */
    push $0
    dec %rcx
copy_args:
    test %rcx, %rcx
    jz prefix
    push 8(%r12,%rcx,8)
    dec %rcx
    jmp copy_args
prefix:
    lea path(%rip), %rax
    push %rax
    lea command(%rip), %rax
    push %rax
    lea option(%rip), %rax
    push %rax
    lea shell(%rip), %rdi
    push %rdi
    mov %rsp, %rsi
    mov $59, %eax                  /* execve */
    syscall
failed:
    mov $127, %edi
    mov $60, %eax                  /* exit */
    syscall
.section .note.GNU-stack,"",@progbits
