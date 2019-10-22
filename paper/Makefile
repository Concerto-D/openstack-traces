
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
	@rm -f *.idx
	@rm -f *.log
	@rm -f *.toc
	@rm -f *.bbl
	@rm -f *.fls
	@rm -f *.ldb
	@rm -f *.tdo
	@rm -f *.blg
	@rm -f *.fdb_latexmk
	@rm -f *.out

mr_clean: clean
	@rm -f $(MAIN).pdf
