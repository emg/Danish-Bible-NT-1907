# -*- coding: utf-8 -*-
import xml.sax
import codecs
import sys
import re

#
#
# This list is a Python list of the books of the Danish Bible,
# including a few (but not all) apocryphals.
#
# 
# Note that:
#
# 1. Each entry in the list consists of a "tuple" with four entries:
#
#    a. The old way of abbreviating the book.
#
#    b. The new, standard way (this is what should be used).
#
#    c. The full, spelled-out way
#
#    d. The OSIS equivalent.
# 
#    e. The BibleWorks equivalent
#
#
danish2osis_list = [
    # As-used-by-refs-in-paratext , As-should-be-printed-in-OSIS , Long-title, OSIS Ref, BibleWorks

    # Old Testament
    (u"1.Mos", u"1 Mos", u"Første Mosebog", u"Gen", u"Gen"),
    (u"2.Mos", u"2 Mos", u"Anden Mosebog", u"Exod", u"Exo"),
    (u"3.Mos", u"3 Mos", u"Tredje Mosebog", u"Lev", u"Lev"),
    (u"4.Mos", u"4 Mos", u"Fjerde Mosebog", u"Num", u"Num"),
    (u"5.Mos", u"5 Mos", u"Femte Mosebog", u"Deut", u"Deu"),
    (u"Jos", u"Jos", u"Josvabogen", u"Josh", u"Jos"),
    (u"Dom", u"Dom", u"Dommerbogen", u"Judg", u"Jdg"),
    (u"Rut", u"Ruth", u"Ruths Bog", u"Ruth", u"Rut"),
    (u"1.Sam", u"1 Sam", u"Første Samuelsbog", u"1Sam", u"1Sa"),
    (u"2.Sam", u"2 Sam", u"Anden Samuelsbog", u"2Sam", u"2Sa"),
    (u"1.Kong", u"1 Kong", u"Første Kongebog", u"1Kgs", u"1Ki"),
    (u"2.Kong", u"2 Kong", u"Anden Kongebog", u"2Kgs", u"2Ki"),
    (u"1.Krøn", u"1 Krøn", u"Første Krønikebog", u"1Chr", u"1Ch"),
    (u"2.Krøn", u"2 Krøn", u"Andeb Krønikebog", u"2Chr", u"2Ch"),
    (u"Ezra", u"Ezra", u"Ezras Bog", u"Ezra", u"Ezr"),
    (u"Neh", u"Neh", u"Nehemias' Bog", u"Neh", u"Neh"),
    (u"Est", u"Est", u"Esters Bog", u"Esth", u"Est"),
    (u"Job", u"Job", u"Jobs Bog", u"Job", u"Job"),
    (u"Sl", u"Sl", u"Salmernes Bog", u"Ps", u"Psa"),
    (u"Ordsp", u"Ordsp", u"Ordsprogenes Bog", u"Prov", u"Pro"),
    (u"Præd", u"Præd", u"Prædikerens Bog", u"Eccl", u"Ecc"),
    (u"Højs", u"Højs", u"Højsangen", u"Song", u"Sol"),
    (u"Es", u"Es", u"Esajas' Bog", u"Isa", u"Isa"),
    (u"Jer", u"Jer", u"Jeremias' Bog", u"Jer", u"Jer"),
    (u"Klages", u"Klages", u"Klagesangene", u"Lam", u"Lam"),
    (u"Ez", u"Ez", u"Ezekiels Bog", u"Ezek", u"Eze"),
    (u"Dan", u"Dan", u"Daniels Bog", u"Dan", u"Dan"),
    (u"Hos", u"Hos", u"Hoseas' Bog", u"Hos", u"Hos"),
    (u"Joel", u"Joel", u"Joels Bog", u"Joel", u"Joe"),
    (u"Am", u"Am", u"Amos' Bog", u"Amos", u"Amo"),
    (u"Ob", u"Obad", u"Obadias' Bog", u"Obad", u"Oba"),
    (u"Jon", u"Jon", u"Jonas' Bog", u"Jonah", u"Jon"),
    (u"Mika", u"Mika", u"Mikas Bog", u"Mic", u"Mic"),
    (u"Nah", u"Nah", u"Nahums Bog", u"Nah", u"Nah"),
    (u"Hab", u"Hab", u"Habakkuks Bog", u"Hab", u"Hab"),
    (u"Zef", u"Sef", u"Sefanias' Bog", u"Zeph", u"Zep"),
    (u"Hagg", u"Hagg", u"Haggajs Bog", u"Hag", u"Hag"),
    (u"Zak", u"Zak", u"Zakarias' Bog", u"Zech", u"Zec"),
    (u"Mal", u"Mal", u"Malakias' Bog", u"Mal", u"Mal"),

    # Apocryphals
    (u"Visd", u"Visd", u"", u"Wis", u""),
    (u"Sir", u"Sir", u"", u"Sir", u""),
    (u"Tob", u"Tob", u"", u"Tob", u""),
    (u"1.Makk", u"1 Makk", u"", u"1Macc", u""),
    (u"2.Makk", u"2 Makk", u"", u"2Macc", u""),

    # New Testament
    (u"Matt", u"Matt", u"Matthæusevangeliet", u"Matt", u"Mat"),
    (u"Mark", u"Mark", u"Markusevangeliet", u"Mark", u"Mar"),
    (u"Luk", u"Luk", u"Lukasevangeliet", u"Luke", u"Luk"),
    (u"Joh", u"Joh", u"Johannesevangeliet", u"John", u"Joh"),
    (u"Ap.G", u"ApG", u"Apostlenes Gerninger", u"Acts", u"Act"),
    (u"Rom", u"Rom", u"Paulus' Brev til Romerne", u"Rom", u"Rom"),
    (u"1.Kor", u"1 Kor", u"Paulus' Første Brev til Korintherne", u"1Cor", u"1Co"),
    (u"2.Kor", u"2 Kor", u"Paulus' Andet Brev til Korintherne", u"2Cor", u"2Co"),
    (u"Gal", u"Gal", u"Paulus' Brev til Galaterne", u"Gal", u"Gal"),
    (u"Ef", u"Ef", u"Paulus' Brev til Efeserne", u"Eph", u"Eph"),
    (u"Fil", u"Fil", u"Paulus' Brev til Filipperne", u"Phil", u"Phi"),
    (u"Kol", u"Kol", u"Paulus' Brev til Kolossenserne", u"Col", u"Col"),
    (u"1.Tess", u"1 Thess", u"Paulus' Første Brev til Thessalonikerne", u"1Thess", u"1Th"),
    (u"2.Tess", u"2 Thess", u"Paulus' Andet Brev til Thessalonikerne", u"2Thess", u"2Th"),
    (u"1.Tim", u"1 Tim", u"Paulus' Første Brev til Timotheus", u"1Tim", u"1Ti"),
    (u"2.Tim", u"2 Tim", u"Paulus' Andet Brev til Timotheus", u"2Tim", u"2Ti"),
    (u"Tit", u"Tit", u"Paulus' Brev til Titus", u"Titus", u"Tit"),
    (u"Filem", u"Filem", u"Paulus' Brev til Filemon", u"Phlm", u"Phm"),
    (u"Hebr", u"Hebr", u"Brevet til Hebræerne", u"Heb", u"Heb"),
    (u"Jak", u"Jak", u"Jakobs Brev", u"Jas", u"Jam"),
    (u"1.Pet", u"1 Pet", u"Peters Første Brev", u"1Pet", u"1Pe"),
    (u"2.Pet", u"2 Pet", u"Peters Andet Brev", u"2Pet", u"2Pe"),
    (u"1.Joh", u"1 Joh", u"Johannes' Første Brev", u"1John", u"1Jo"),
    (u"2.Joh", u"2 Joh", u"Johannes' Andet Brev", u"2John", u"2Jo"),
    (u"3.Joh", u"3 Joh", u"Johannes' Tredje Brev", u"3John", u"3Jo"),
    (u"Jud", u"Jud", u"Judas' Brev", u"Jude", u"Jud"),
    (u"Åb", u"Åb", u"Johannes' Åbenbaring", u"Rev", u"Rev"),
]

osis_dict = {} # osisID --> (index-in-danish2osis_list, BibleWorks)

for index in xrange(0, len(danish2osis_list)):
    (Paratext, ShouldBePrinted, FullName, osisBookID, BibleWorks) = danish2osis_list[index]
    osis_dict[osisBookID] = (index, BibleWorks)

tag_re = re.compile(ur'<[^>]+>')

punct_re = re.compile(ur'[\.,;:\"?!()[]/\-]')

xml_entity_re = re.compile(ur'(&quot;)|(&gt;)|(&lt;)|(&amp;)')

token_re = re.compile(ur'(\s*)([^\s]*)(\s*)')

surface_re = re.compile(ur'([^\w]*)(\w*)([^\w]*)')

whitespace_re = re.compile(ur'^\s*$')

def usage():
    sys.stderr.write("Usage:\n     python osis2bibleworks.py filename\n")


def osisID2ref(osisID):
    (osisBook, chapter_str, verse_str) = osisID.strip().split(".")
    chapter = int(chapter_str)
    verse = int(verse_str)
    book_number = osis_dict[osisBook][0]
    BibleWorksBook = osis_dict[osisBook][1]
    return "%02d-%03d-%03d-%s" % (book_number, chapter, verse, BibleWorksBook)

def getBasename(pathname):
    filename = pathname.split("/")[-1]
    if "." in filename:
        basename = ".".join(filename.split(".")[:-1])
    else:
        basename = filename
    return basename
    

class OSISHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.elemstack = []
        self.charstack = []
        self.bInVerse = False

        self.nixed_elements = set(["header", "work", "date", "type", "identifier", "language", "rights", "refSystem", "note", "title"])
        self.ignored_elements = set(["osis", "osisText", "chapter", "div", "p"])

        self.nixing_stack = []

        self.verses = {} # AGNT-ref --> [token-list]

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def characters(self, data):
        self.charstack.append(data)

    def handleChars(self, chars_before):
        if len(self.nixing_stack) > 0:
            bDoIt = False
        elif self.bInVerse:
            bDoIt = True
        else:
            bDoIt = False

        if not bDoIt:
            return

        chars = chars_before
        if whitespace_re.match(chars):
            self.verses[self.curref].append(" ")
        else:
            self.verses[self.curref].extend(chars.split())

    def startElement(self, tag, attributes):
        self.elemstack.append(tag)

        chars = "".join(self.charstack)
        del self.charstack
        self.charstack = []

        self.handleChars(chars)

        if tag in self.nixed_elements:
            self.nixing_stack.append(tag)
        elif len(self.nixing_stack) != 0:
            pass
        elif tag == "verse":
            if attributes.has_key("eID"):
                pass
            else:
                osisID = attributes["osisID"]
                self.curref = osisID2ref(osisID)
                self.verses.setdefault(self.curref, [])
                self.bInVerse = True
        elif tag in self.ignored_elements:
            pass
        else:
            raise Exception("Unknown start-tag: <%s>" % tag)


    def endElement(self, tag):
        chars = "".join(self.charstack)
        del self.charstack
        self.charstack = []

        self.handleChars(chars)

        if tag in self.nixed_elements:
            oldTag = self.nixing_stack.pop()
            assert tag == oldTag
        elif len(self.nixing_stack) != 0:
            pass
        elif tag == "verse":
            pass
        elif tag == "chapter":
            self.bInVerse = False
        elif tag in self.ignored_elements:
            pass
        else:
            raise Exception("Unknown end-tag: </%s>" % tag)



    def dumpBibleWorks(self, fout):
        for ref in sorted(self.verses):
            (book_number_str, chapter_str, verse_str, BibleWorksBook) = ref.split("-")
            chapter = int(chapter_str)
            verse = int(verse_str)
            BBW_ref = u"%s %d:%d" % (BibleWorksBook, chapter, verse)
            token_str = u" ".join((u" ".join(self.verses[ref]).split()))
            fout.write((u"%s %s\n" % (BBW_ref, token_str)).replace(u"\u201f", u"\u00ab").replace(u"\u201e", u"\u00bb").encode('cp1252'))

filename = sys.argv[1]

handler = OSISHandler()

fin = open(filename, "r")
sys.stderr.write("Now reading: %s ...\n" % filename)
xml.sax.parse(fin, handler)
sys.stderr.write("Done!\n")

sys.stderr.write("Now dumping on stdout...\n")
handler.dumpBibleWorks(sys.stdout)
sys.stderr.write("Done!\n")

