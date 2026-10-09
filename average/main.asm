; Программа читает файл с двумя строками:
; первая строка - массив x;
; вторая строка - массив y;
; числа разделены запятыми.
; Вычисляет среднее арифметическое sum(x[i] - y[i]) / n.

BUF_SIZE equ 4194304      ; 4 MiB буфер файла
MAX_ELEMS equ 524288      ; максимальное количество элементов

section .data
usage:          db "Usage: average <file>", 10
usage_len       equ $ - usage

sep:            db ": "
sep_len         equ $ - sep

corrupt_msg:    db ": файл испорчен", 10
corrupt_msg_len equ $ - corrupt_msg

newline:        db 10
minus_str:      db '-'

section .bss
buf      resb BUF_SIZE
xarr     resq MAX_ELEMS
numbuf   resb 24
tmpbyte  resb 1

section .text
global _start

_start:
    ; argc / argv
    mov rcx, [rsp]
    cmp rcx, 2
    jl noarg

    ; argv[1] - имя файла
    mov r12, [rsp + 16]

    ; open(filename, O_RDONLY)
    mov rax, 2
    mov rdi, r12
    xor esi, esi
    xor edx, edx
    syscall

    cmp rax, 0
    jl error_corrupt

    mov r13, rax            ; fd

    ; Чтение файла в буфер
    xor r15, r15            ; сколько байт прочитано

read_loop:
    mov rdi, r13
    lea rsi, [rel buf]
    add rsi, r15

    mov rdx, BUF_SIZE
    sub rdx, r15
    jz check_overflow

    mov rax, 0              ; read
    syscall

    test rax, rax
    jz read_done
    js error_corrupt

    add r15, rax
    jmp read_loop

check_overflow:
    ; Если буфер полон, проверим, есть ли ещё данные.
    ; Если есть - считаем файл испорченным/слишком большим.
    mov rdi, r13
    lea rsi, [rel tmpbyte]
    mov rdx, 1
    mov rax, 0
    syscall

    test rax, rax
    jz read_done
    js error_corrupt
    jmp error_corrupt

read_done:
    ; close(fd)
    mov rdi, r13
    mov rax, 3
    syscall

    test r15, r15
    jz error_corrupt

    ; r13 - конец буфера, r14 - текущая позиция
    lea r13, [rel buf]
    add r13, r15
    lea r14, [rel buf]

    ; r15 - количество элементов первой строки
    xor r15, r15

first_expect_number:
    mov rdi, r14
    mov rsi, r13
    call skip_spaces
    mov r14, rdi

    cmp r14, r13
    je error_corrupt

    mov al, [r14]
    cmp al, 10              ; LF - пустой элемент или конец первой строки без числа
    je error_corrupt

    mov rdi, r14
    mov rsi, r13
    call parse_int
    jc error_corrupt

    cmp r15, MAX_ELEMS
    jae error_corrupt

    lea rcx, [rel xarr]
    mov [rcx + r15*8], rax
    inc r15

    mov r14, rdi            ; обновлённая позиция после числа

    ; После числа должны идти запятая или конец первой строки
    mov rdi, r14
    mov rsi, r13
    call skip_spaces
    mov r14, rdi

    cmp r14, r13
    je error_corrupt        ; нет второй строки

    mov al, [r14]
    cmp al, 10
    je first_line_done
    cmp al, ','
    je first_comma
    jmp error_corrupt

first_comma:
    inc r14
    jmp first_expect_number

first_line_done:
    inc r14                 ; пропустить LF
    cmp r14, r13
    je error_corrupt        ; нет второй строки

    ; r10 - сумма разностей, r11 - счётчик элементов второй строки
    xor r10, r10
    xor r11, r11

second_expect_number:
    mov rdi, r14
    mov rsi, r13
    call skip_spaces
    mov r14, rdi

    cmp r14, r13
    je error_corrupt

    mov al, [r14]
    cmp al, 10
    je error_corrupt

    ; Если элементов второй строки уже не меньше, чем первой, то лишний элемент
    cmp r11, r15
    jae error_corrupt

    mov rdi, r14
    mov rsi, r13
    call parse_int
    jc error_corrupt

    ; diff = x[i] - y[i]
    lea rcx, [rel xarr]
    mov rcx, [rcx + r11*8]
    sub rcx, rax
    add r10, rcx

    inc r11
    mov r14, rdi

    ; После числа: запятая, конец второй строки или EOF
    mov rdi, r14
    mov rsi, r13
    call skip_spaces
    mov r14, rdi

    cmp r14, r13
    je second_line_done

    mov al, [r14]
    cmp al, 10
    je second_line_done
    cmp al, ','
    je second_comma
    jmp error_corrupt

second_comma:
    inc r14
    jmp second_expect_number

second_line_done:
    ; Количество элементов должно совпадать
    cmp r11, r15
    jne error_corrupt

    ; После второй строки допускаются только пробельные символы до конца файла
trail_loop:
    cmp r14, r13
    je compute

    mov al, [r14]
    cmp al, ' '
    je trail_skip
    cmp al, 9
    je trail_skip
    cmp al, 10
    je trail_skip
    cmp al, 13
    je trail_skip

    jmp error_corrupt

trail_skip:
    inc r14
    jmp trail_loop

compute:
    test r15, r15
    jz error_corrupt

    ; average = sum / count
    mov rax, r10
    cqo
    idiv r15
    mov rbx, rax            ; результат

    ; Вывод имени файла
    mov rdi, r12
    call strlen

    mov rdx, rax
    mov rax, 1              ; write
    mov rdi, 1              ; stdout
    mov rsi, r12
    syscall

    ; Вывод ": "
    mov rax, 1
    mov rdi, 1
    lea rsi, [rel sep]
    mov rdx, sep_len
    syscall

    ; Если результат отрицательный, выводим '-'
    test rbx, rbx
    jns print_digits

    mov rax, 1
    mov rdi, 1
    lea rsi, [rel minus_str]
    mov rdx, 1
    syscall

    neg rbx

print_digits:
    ; Преобразование числа в строку задом наперёд
    lea rdi, [rel numbuf]
    add rdi, 24

    mov rax, rbx
    xor ecx, ecx
    mov r9, 10

convert_loop:
    xor edx, edx
    div r9

    add dl, '0'
    dec rdi
    mov [rdi], dl
    inc rcx

    test rax, rax
    jnz convert_loop

    ; Вывод цифр
    mov rsi, rdi
    mov rdx, rcx
    mov rax, 1
    mov rdi, 1
    syscall

    ; Перевод строки
    mov rax, 1
    mov rdi, 1
    lea rsi, [rel newline]
    mov rdx, 1
    syscall

    ; exit(0)
    mov rax, 60
    xor edi, edi
    syscall

error_corrupt:
    ; Вывод имени файла
    mov rdi, r12
    call strlen

    mov rdx, rax
    mov rax, 1
    mov rdi, 1
    mov rsi, r12
    syscall

    ; Вывод сообщения о повреждённом файле
    mov rax, 1
    mov rdi, 1
    lea rsi, [rel corrupt_msg]
    mov rdx, corrupt_msg_len
    syscall

    ; exit(1)
    mov rax, 60
    mov edi, 1
    syscall

noarg:
    mov rax, 1
    mov rdi, 1
    lea rsi, [rel usage]
    mov rdx, usage_len
    syscall

    mov rax, 60
    mov edi, 1
    syscall


; skip_spaces: пропускает пробелы, табы и CR, но не LF
; вход: rdi - текущая позиция, rsi - конец буфера
; выход: rdi - новая позиция
skip_spaces:
.skip_loop:
    cmp rdi, rsi
    jae .done

    movzx eax, byte [rdi]

    cmp al, ' '
    je .skip_one

    cmp al, 9
    je .skip_one

    cmp al, 13
    je .skip_one

    jmp .done

.skip_one:
    inc rdi
    jmp .skip_loop

.done:
    ret


; parse_int: разбирает целое число со знаком
; вход: rdi - позиция, rsi - конец буфера
; выход: CF=0 успешно, rax - число, rdi - позиция после числа
;        CF=1 ошибка

parse_int:
    xor eax, eax            ; значение
    xor ecx, ecx            ; знак: 0 плюс, 1 минус

.skip_ws:
    cmp rdi, rsi
    jae .error

    movzx edx, byte [rdi]

    cmp dl, ' '
    je .skip_one

    cmp dl, 9
    je .skip_one

    cmp dl, 13
    je .skip_one

    jmp .check_sign

.skip_one:
    inc rdi
    jmp .skip_ws

.check_sign:
    cmp dl, '-'
    je .minus

    cmp dl, '+'
    je .plus

    jmp .digits

.minus:
    mov ecx, 1
    inc rdi
    jmp .digits

.plus:
    inc rdi

.digits:
    xor r8d, r8d            ; количество цифр

.digit_loop:
    cmp rdi, rsi
    jae .finish

    movzx edx, byte [rdi]

    cmp dl, '0'
    jb .finish

    cmp dl, '9'
    ja .finish

    imul rax, rax, 10
    sub dl, '0'
    add rax, rdx

    inc rdi
    inc r8d
    jmp .digit_loop

.finish:
    test r8d, r8d
    jz .error

    test rcx, rcx
    jz .ok

    neg rax

.ok:
    clc
    ret

.error:
    stc
    ret


; strlen: длина строки
; вход: rdi - строка
; выход: rax - длина

strlen:
    xor eax, eax

.loop:
    cmp byte [rdi + rax], 0
    je .done

    inc rax
    jmp .loop

.done:
    ret