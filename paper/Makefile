
TEX = pdflatex
BIB = bibtex
MAIN = main

READER = zathura

OBJ = $(shell find . -name '*.tex')

all: $(MAIN).pdf

$(MAIN).pdf: $(OBJ) $(MAIN).bib
	$(TEX) $(MAIN).tex
	$(BIB) $(MAIN)
	$(TEX) $(MAIN).tex
	$(TEX) $(MAIN).tex

open: $(MAIN).pdf
	$(READER) $^&

clean:
	@rm -f *.aux
	@rm -f *.bbl
	@rm -f *.blg
	@rm -f *.fls
	@rm -f *.fdb_latexmk
	@rm -f *.idx
	@rm -f *.ldb
	@rm -f *.log
	@rm -f *.out
	@rm -f *.spl
	@rm -f *.tdo
	@rm -f *.toc

mr_clean: clean
	@rm -f $(MAIN).pdf
