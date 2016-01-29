# -*- coding: utf-8 -*-
import xml.sax
import codecs
import sys
import re
reload(sys)
#sys.setdefaultencoding('iso-8859-1')
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

EMIT_TRAILING_NEWLINE = True
NO_TRAILING_NEWLINE = False

UBS_book_ids = [
    U"GEN",
    U"EXO",
    U"LEV",
    U"NUM",
    U"DEU",
    U"JOS",
    U"JDG",
    U"RUT",
    U"1SA",
    U"2SA",
    U"1KI",
    U"2KI",
    U"1CH",
    U"2CH",
    U"EZR",
    U"NEH",
    U"EST",
    U"JOB",
    U"PSA",
    U"PRO",
    U"ECC",
    U"SNG",
    U"ISA",
    U"JER",
    U"LAM",
    U"EZK",
    U"DAN",
    U"HOS",
    U"JOL",
    U"AMO",
    U"OBA",
    U"JON",
    U"MIC",
    U"NAM",
    U"HAB",
    U"ZEP",
    U"HAG",
    U"ZEC",
    U"MAL",
    U"MAT",
    U"MRK",
    U"LUK",
    U"JHN",
    U"ACT",
    U"ROM",
    U"1CO",
    U"2CO",
    U"GAL",
    U"EPH",
    U"PHP",
    U"COL",
    U"1TH",
    U"2TH",
    U"1TI",
    U"2TI",
    U"TIT",
    U"PHM",
    U"HEB",
    U"JAS",
    U"1PE",
    U"2PE",
    U"1JN",
    U"2JN",
    U"3JN",
    U"JUD",
    U"REV",
    ]

def usage():
    sys.stderr.write("Usage:\n     python osis2usfm.py <OSIS-infilename.xml>\n\n")

def mangle_XML_entities(s):
    r = s.replace("&", "&amp;")
    r = r.replace("<", "&lt;")
    r = r.replace(">", "&gt;")
    r = r.replace("\"", "&quot;")
    return r

class OSIS2USFMHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.elemstack = []
        self.charstack = []
        self.nixing_elements = set(['header', 'work', 'date', 'type', 'identifier', 'language', 'rights', 'refSystem', 'publisher'])
        self.nixing_stack = []
        self.books = []
        self.book_number = -1
        self.bInBible = False
        
    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def characters(self, data):
        self.charstack.append(data)

    def handle_chars(self, chars):
        if len(self.nixing_stack) != 0:
            pass
        else:
            self.addString(chars)

    def addString(self, s):
        outs = s.replace(u"\n", u" ")
        if len(outs.strip()) == 0:
            pass
        else:
            self.emit(outs)

    def emit(self, outs):
        if self.bInBible:
            self.books[-1].append(outs)

    def emitTag(self, tag, content, bNewlineAfter):
        if len(self.books[-1]) == 1:
            newlineBefore = u""
        elif len(self.books[-1][-1]) == 0:
            newlineBefore = u""
        elif self.books[-1][-1][-1] == u"\n":
            newlineBefore = u""
        else:
            newlineBefore = u"\n"

        if bNewlineAfter:
            newlineAfter = u"\n"
        else:
            newlineAfter = u""

        if content == u"":
            self.emit(u"%s\\%s%s" % (newlineBefore, tag, newlineAfter))
        else:
            self.emit(u"%s\\%s %s%s" % (newlineBefore, tag, content, newlineAfter))
    

    def startElement(self, tag, attributes):
        self.elemstack.append(tag)
        chars = "".join(self.charstack)
        del self.charstack
        self.charstack = []

        self.handle_chars(chars)


        if tag == "verse":
            if attributes.has_key("eID"):
                pass
            else:
                osisID = attributes["osisID"]
                arr = osisID.split(".")
                verse = arr[2]
                self.curverse = verse
                chapter = arr[1]
                self.emitTag(u"v", u"%s " % self.curverse, NO_TRAILING_NEWLINE)
        elif tag == "reference":
            pass
        elif tag == "p":
            self.emitTag(u"p", u" ", NO_TRAILING_NEWLINE)
        elif tag == "chapter":
            if attributes.has_key("eID"):
                pass
            else:
                osisID = attributes["osisID"]
                arr = osisID.split(".")
                chapter = arr[-1]
                self.curchapter = chapter
                self.emitTag(u"c", self.curchapter, EMIT_TRAILING_NEWLINE)
                self.mydivtype = "chapter"
        elif tag == "note":
            self.emit(u"\\f + \\fr %s,%s \\ft " % (self.curchapter, self.curverse))
        elif tag == "div":
            self.mydivtype = attributes["type"]
            if self.mydivtype == u"book":
                self.osisBookID = attributes[u"osisID"]
                if self.osisBookID == "Gen":
                    self.book_number = 0
                elif self.osisBookID == "Matt":
                    self.book_number = 39
                else:
                    self.book_number += 1
                UBS_id = UBS_book_ids[self.book_number]
                self.UBS_number = self.book_number + 1
                self.UBS_id = UBS_id
                self.books.append([UBS_id])
                self.bInBible = True

                self.emitTag(u"id", self.UBS_id, EMIT_TRAILING_NEWLINE)
        elif tag == "title":
            if len(self.nixing_stack) != 0:
                pass
            else:
                if self.mydivtype == "bookGroup":
                    pass
                elif self.mydivtype == "book":
                    self.emitTag(u"mt", u" ", NO_TRAILING_NEWLINE)
                elif self.mydivtype == "chapter":
                    self.emitTag(u"s", u" ", NO_TRAILING_NEWLINE)
                else:
                    raise Exception((u"Unknown mydivtype: '%s'" % self.mydivtype).encode('utf-8'))
        elif tag in self.nixing_elements:
            self.nixing_stack.append(tag)
        elif tag == "hi":
            self.emit(u"\\it ")
        elif tag == "osis":
            pass
        elif tag == "osisText":
            pass
        else:
            raise Exception((u"Unknown start-tag <%s> with attributes %s" % (tag, str(attributes))).encode('utf-8'))


    def endElement(self, tag):
        poppedelem = self.elemstack.pop()
        chars = "".join(self.charstack)
        del self.charstack
        self.charstack = []

        self.handle_chars(chars)

        if tag == "verse":
            pass
        elif tag == "reference":
            pass
        elif tag == "p":
            pass
        elif tag == "chapter":
            pass
        elif tag == "note":
            self.emit(u"\\ft*\\f* ")
        elif tag == "div":
            pass
        elif tag == "title":
            if len(self.nixing_stack) != 0:
                pass
            else:
                if self.mydivtype == "chapter":
                    self.emit(u"\n")
                elif self.mydivtype == "book":
                    self.emit(u"\n")
                else:
                    self.emit(u"\n")
                self.bHasJustSeenTitle = True
        elif tag in self.nixing_elements:
            assert self.nixing_stack.pop() == tag
        elif tag == "hi":
            self.emit(u"\\it*")
        elif tag == "osis":
            pass
        elif tag == "osisText":
            pass
        else:
            raise Exception((u"Unknown end-tag </%s>" % tag).encode('utf-8'))

    def transform_USFM(self, udoc):
        udoc = re.sub(ur'(\\v \d+ )\s*', ur'\1', udoc)
        udoc = re.sub(ur'(\\mt )\s*', ur'\1', udoc)
        udoc = re.sub(ur'(\\s )\s*', ur'\1', udoc)
        #udoc = re.sub(ur'', ur'', udoc)
        return udoc

    def dumpUSFM(self):
        first_UBS_id = self.books[0][0]
        offset = UBS_book_ids.index(first_UBS_id) + 1

        for index in xrange(0, len(self.books)):
            UBS_id = self.books[index][0]
            filename = "USFM/%02d%s.SFM" % (index + offset, UBS_id)
            sys.stderr.write("Now dumping: %s...\n" % filename)
            udoc = u"".join(self.books[index][1:])
            udoc = self.transform_USFM(udoc)
            fout = open(filename, "wb")
            fout.write(udoc.encode('utf-8'))
            fout.close()
        

if len(sys.argv) > 1:
    infilename = sys.argv[1]
else:
    usage()
    sys.exit(1)
    
fin = open(infilename, "r")
handler = OSIS2USFMHandler()
xml.sax.parse(fin, handler)

handler.dumpUSFM()

