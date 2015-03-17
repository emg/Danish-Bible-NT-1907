# The mql program from Emdros.
#
# See http://emdros.org/ for more information.
#
MQL = /usr/bin/mql


CLEANFILES = *~ *.pyc *.pyo \
             MQL/NT1907.mql \
             EmdrosDB/nt1907.sqlite3 \
             MQL/*~ BibleWorks/*~ OSIS/*~


all: MQL/NT1907.mql BibleWorks/DA_NT1907_bibleworks.txt

clean:
	rm -f $(CLEANFILES)


# Create an Emdros MQL script which can populate an Emdros database
# with the data from the Bible.
#
# Emdros is a general-purpose text database engine, especially well
# suited for creating digital libraries, such as most kinds of Bible
# software.
#
# For more information, see http://emdros.org/
#
mql: MQL/NT1907.mql

MQL/NT1907.mql: OSIS/DA_NT1907.OSIS.xml osis2mql.py 
	python osis2mql.py --NT $< >$@



# Create a BibleWorks file
bbw: BibleWorks/DA_NT1907_bibleworks.txt

BibleWorks/DA_NT1907_bibleworks.txt: OSIS/DA_NT1907.OSIS.xml osis2bibleworks.py
	python osis2bibleworks.py OSIS/DA_NT1907.OSIS.xml > $@



# Create an SQLite3 database in Emdros format from the MQL
db3: EmdrosDB/nt1907.sqlite3

EmdrosDB/nt1907.sqlite3: MQL/NT1907.mql MQL/osis_schema.mql
	-echo "DROP DATABASE '${@}' GO" | $(MQL) -b 3
	echo "CREATE DATABASE '${@}' GO" | $(MQL) -b 3
	$(MQL) -b 3 -d $@ MQL/osis_schema.mql
	$(MQL) -b 3 -d $@ $<
	echo "CREATE OBJECT FROM MONADS={1-4000000}[db dbname:='DANT1907';friendly_dbname:='Dansk NT 1907';bible_parts:=(NT);language:=danish;dbtype:=bible;]" | $(MQL) -b 3 -n -d $@
	echo "VACUUM DATABASE ANALYZE GO" | $(MQL) -b 3 -d $@

.PHONY: db3 mql bbw
