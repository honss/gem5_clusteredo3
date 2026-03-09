# Minimal program: 5 instructions total (no C runtime).
# Build: as -o tiny.o tiny.s && ld -e _start -o tiny tiny.o

.globl _start
_start:
    mov   $1, %eax      # 1: eax = 1
    add   $2, %eax      # 2: eax = 3
    mov   $60, %eax     # 3: exit syscall number
    xor   %edi, %edi    # 4: exit code 0
    syscall             # 5: exit(0)
