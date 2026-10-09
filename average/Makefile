FILE    ?= data.txt

NASM    = nasm
LD      = ld

NFLAGS  = -f elf64
LDFLAGS = -m elf_x86_64

all: average

average: main.o
	$(LD) $(LDFLAGS) -o $@ $^

main.o: main.asm
	$(NASM) $(NFLAGS) $< -o $@

run: average
	./average "$(FILE)"

clean:
	rm -f average main.o

.PHONY: all run clean