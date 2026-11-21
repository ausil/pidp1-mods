# Shared code: the link client, the Flexo converter and the .ovl reader and drum writer are in
# ../UtilLibs, the link's wire format in the emulator's ad1proto.h.
UTILLIBS=../UtilLibs
# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -Wno-unused-result -I$(UTILLIBS) -I../../src/common
BISONFLAGS=
#CONFLICTS=-Wcounterexamples

OBJS=ad1.o helpText.o eval.o lex.yy.o y.tab.o listFile.o files.o commands.o \
	flexoConversion.o loader.o ad1link.o target.o overlays.o ovlfile.o ../Disassembler/decode_instruction.o

.PHONY: all clean install
.DELETE_ON_ERROR:

all: ad1

ad1: $(OBJS)
	$(CC) $(CFLAGS) -o ad1 $(OBJS)

clean:
	@rm -f ad1 *.o y.tab.c y.tab.h lex.yy.c parser.output .y.tab.c.old .y.tab.h.old .lex.yy.c.old

install: ad1
	cp ad1 ../../bin
	strip ../../bin/ad1

ad1.o: ad1.c ad1.h target.h $(UTILLIBS)/ad1link.h helpmsgs.h y.tab.h $(UTILLIBS)/flexoConversion.h
	$(CC) $(CFLAGS) -c ad1.c

helpText.o: helpText.c
	$(CC) $(CFLAGS) -c helpText.c

files.o: files.c ad1.h target.h $(UTILLIBS)/ad1link.h
	$(CC) $(CFLAGS) -c files.c

eval.o: eval.c ad1.h target.h $(UTILLIBS)/ad1link.h y.tab.h
	$(CC) $(CFLAGS) -c eval.c

commands.o: commands.c ad1.h target.h $(UTILLIBS)/ad1link.h helpmsgs.h y.tab.h ../Disassembler/decode_instruction.h
	$(CC) $(CFLAGS) -c commands.c

listFile.o: listFile.c ad1.h target.h $(UTILLIBS)/ad1link.h
	$(CC) $(CFLAGS) -c listFile.c

loader.o: loader.c ad1.h target.h $(UTILLIBS)/ad1link.h $(UTILLIBS)/ovlfile.h
	$(CC) $(CFLAGS) -c loader.c

ad1link.o: $(UTILLIBS)/ad1link.c $(UTILLIBS)/ad1link.h $(UTILLIBS)/ad1proto.h
	$(CC) $(CFLAGS) -c $(UTILLIBS)/ad1link.c -o ad1link.o

target.o: target.c target.h $(UTILLIBS)/ad1link.h $(UTILLIBS)/ad1proto.h
	$(CC) $(CFLAGS) -c target.c

flexoConversion.o: $(UTILLIBS)/flexoConversion.c $(UTILLIBS)/flexoConversion.h
	$(CC) $(CFLAGS) -c $(UTILLIBS)/flexoConversion.c -o flexoConversion.o

ovlfile.o: $(UTILLIBS)/ovlfile.c $(UTILLIBS)/ovlfile.h
	$(CC) $(CFLAGS) -c $(UTILLIBS)/ovlfile.c -o ovlfile.o

overlays.o: overlays.c ad1.h target.h $(UTILLIBS)/ad1link.h
	$(CC) $(CFLAGS) -c overlays.c

../Disassembler/decode_instruction.o: ../Disassembler/decode_instruction.c
	(cd ../Disassembler ; make decode_instruction.o)

lex.yy.o: lex.yy.c y.tab.h
	$(CC) $(CFLAGS) -c lex.yy.c

y.tab.o: y.tab.c
	$(CC) $(CFLAGS) -DYYDEBUG=1 -c y.tab.c

lex.yy.c: lexer.l y.tab.h FORCE
	flex -d lexer.l

%.tab.c %.tab.h: parser.y ad1.h FORCE
	bison $(BISONFLAGS) -o y.tab.c -d parser.y

FORCE:
