# -*- coding: utf-8 -*-
#
# The purpose of this script is to convert a Bible text in OSIS to an
# Emdros MQL script that populates an Emdros text database with the
# contents of the Bible text.
#

import xml.sax
import codecs
import sys
import re

tag_re = re.compile(ur'<[^>]+>')

punct_re = re.compile(ur'[\.,;:\"?!()[]/\-]')

xml_entity_re = re.compile(ur'(&quot;)|(&gt;)|(&lt;)|(&amp;)')

token_re = re.compile(ur'(\s*)([^\s]*)(\s*)')

letter_r = ur'a-zA-ZæøåÆØÅïéÉ\d-'

surface_re = re.compile(ur'([^%s]*)([%s]*)([^%s]*)' % (letter_r, letter_r, letter_r))

whitespace_re = re.compile(ur'^\s+$')

def usage():
    sys.stderr.write("""Usage:

     python osis2mql.py (--NT|--OT|--NTNoTokens|--OTNoTokens|--NTNoTokensButSnippets|--OTNoTokensButSnippets) filename

     Writes the MQL on stdout.

""")


def getBasename(pathname):
    filename = pathname.split("/")[-1]
    if "." in filename:
        basename = ".".join(filename.split(".")[:-1])
    else:
        basename = filename
    return basename
    
########################################
##
## MQL string mangling
##
########################################
special_re = re.compile(r"[\n\t\"\\]")

special_dict = {
    '\n' : '\\n',
    '\t' : '\\t',
    '"' : '\\"',
    '\\' : '\\\\',
}

upper_bit_re = re.compile(ur'[\x80-\xff]')

def special_sub(mo):
    c = mo.group(0)
    assert len(c) == 1
    return special_dict[c]

def upper_bit_sub(mo):
    c = mo.group(0)
    assert len(c) == 1
    return "\\x%02x" % ord(c)

def mangleMQLString(ustr):
    result = special_re.sub(special_sub, ustr.encode('utf-8'))
    result = upper_bit_re.sub(upper_bit_sub, result)
    return result

   

def mangle_XML_entities(s):
    r = s.replace("&", "&amp;")
    r = r.replace("<", "&lt;")
    r = r.replace(">", "&gt;")
    r = r.replace("\"", "&quot;")
    return r

class Token:
    def __init__(self, monad, prefix, surface, suffix, xmlindex):
        self.monad = monad
        self.wholesurface = prefix + surface + suffix
        self.prefix = prefix
        self.surface = surface
        self.suffix = suffix
        self.xmlindex = xmlindex

    def dumpMQL(self, f):
        surface_lowcase = self.surface.lower();
        surface_stripped_lowcase = surface_re.findall(surface_lowcase)[0][1]

        f.write("CREATE OBJECT FROM MONADS={%d}\n" % self.monad)
        #f.write((u"[surface_stripped_lowcase:=\"%s\";\n" % (mangleMQLString(surface_stripped_lowcase))).encode('utf-8'))
        f.write("[")
        f.write((u"wholesurface:=\"%s\";xmlindex:=%d;\n]\n" % (mangleMQLString(self.wholesurface), self.xmlindex)).encode('utf-8'))


class SRObject:
    def __init__(self, objectTypeName, starting_monad):
        self.objectTypeName = objectTypeName
        self.fm = starting_monad
        self.lm = starting_monad
        self.stringFeatures = {}
        self.nonStringFeatures = {}
        self.id_d = 0

    def setID_D(self, id_d):
        self.id_d = id_d

    def setStringFeature(self, name, value):
        self.stringFeatures[name] = value

    def setNonStringFeature(self, name, value):
        self.nonStringFeatures[name] = value

    def getStringFeature(self, name):
        return self.stringFeatures[name]

    def setLastMonad(self, ending_monad):
        if ending_monad < self.fm:
            self.lm = self.fm
        else:
            self.lm = ending_monad

    def dumpMQL(self, fout):
        fout.write("CREATE OBJECT FROM MONADS={%d-%d}" % (self.fm, self.lm))
        if self.id_d != 0:
            fout.write("WITH ID_D=%d" % self.id_d)
        fout.write("[")
        for (key,value) in self.nonStringFeatures.items():
            print >>fout, "  %s:=%s;" % (key, value)
        for (key,value) in self.stringFeatures.items():
            print >>fout, (u"  %s:=\"%s\";" % (key, mangleMQLString(value))).encode('utf-8')
        fout.write("]\n")


class OSISHandler(xml.sax.ContentHandler):
    def __init__(self, first_monad, bDoSnippets):
        self.bDoSnippets = bDoSnippets


        self.elemstack = []
        self.charstack = []
        self.objects = {} # objType --> [obj1,obj2,...]
        self.tokens = [] # list of Token objects
        self.objstack = []

        self.divtypestack = [""] # "" to always have one

        self.bInChapter = False

        self.nixed_elements = set(["header", "work", "date", "type", "identifier", "language", "rights", "refSystem"])
        self.ignored_elements = set(["osis", "osisText"])

        self.nixing_stack = []
        self.single_tag_elements = {
            #"br" : None
                                    }
        self.handled_elements = set(["div", "title", "chapter", "verse", "p"])
        self.simple_SR_elements = set(["note"])

        self.curmonad = first_monad
        self.xmlindex = 1

        self.tag2objectTypeName = {
            "p" : "paragraph",
            "title" : "title",
            "chapter" : "chapter",
            "verse" : "verse",
            "note" : "note",
            }

        self.curBook = None # SRObject("book")
        self.curChapter = None # SRObject("chapter")
        self.curVerse = None # SRObject("verse")
        
    def startDocument(self):
        pass

    def endDocument(self):
        self.endVerse()
        self.endChapter()
        self.endBook()


    def characters(self, data):
        self.charstack.append(data)

    def createObject(self, objectTypeName):
        obj = SRObject(objectTypeName, self.curmonad)
        obj.setNonStringFeature("xmlindex", self.xmlindex)
        self.xmlindex += 1
        self.objstack.append(obj)
        return obj

    def createObjectSingleTag(self, objectTypeName):
        # The reason we subtract 1 for single tags (such as <br/>) is
        # that they do not anticipate something inside of them, and
        # so, since we have already added 1 to self.curmonad, we need
        # to associate it, not with the following token, but with the
        # previous token.
        obj = SRObject(objectTypeName, self.curmonad - 1)
        obj.setNonStringFeature("xmlindex", self.xmlindex)
        self.xmlindex += 1
        self.objstack.append(obj)
        return obj

    def endObject(self, objectTypeName):
        obj = self.objstack.pop()
        assert obj.objectTypeName == objectTypeName
        self.objects.setdefault(objectTypeName, []).append(obj)
        
    def addCurMonadToObjects(self):
        for obj in self.objstack:
            obj.setLastMonad(self.curmonad)

    def getCurElement(self):
        if len(self.elemstack) == 0:
            return ""
        else:
            return self.elemstack[-1]

    def handleChars(self, chars_before):
        if len(self.nixing_stack) > 0:
            bDoIt = False
        elif self.getCurElement() == "title":
            bDoIt = True
        elif self.bInChapter:
            bDoIt = True
        else:
            bDoIt = False

        if not bDoIt:
            return

        chars = chars_before
        if whitespace_re.match(chars):
            #myToken = Token(self.curmonad, " ")
            #self.tokens.append(myToken)
            #self.curmonad += 1
            pass
        else:
            if self.bDoSnippets:
                snippet_obj = self.createObject("snippet")

            st_prefix = 1
            st_token = 2
            st_suffix = 3

            t = ""
            state = st_prefix

            for c in chars:
                if c in " \n\r\t":
                    if state == st_prefix:
                        t += c
                    elif state == st_token:
                        t += c
                        state = st_suffix
                    else:
                        t += c
                else:
                    if state == st_prefix:
                        t += c
                        state = st_token
                    elif state == st_token:
                        t += c
                    else:
                        self.addToken(t)
                        t = c
                        state = st_token
            if t != "":
                self.addToken(t)

            if self.bDoSnippets:
                snippet_obj.setStringFeature("content", mangle_XML_entities(chars))
                snippet_obj.setLastMonad(self.curmonad-1)
                self.endObject("snippet")

    def addToken(self, prefix_surface_suffix):
        (prefix, surface, suffix) = token_re.findall(prefix_surface_suffix)[0]

        myToken = Token(self.curmonad, prefix, surface, suffix, self.xmlindex)
        self.xmlindex += 1
        self.tokens.append(myToken)

        self.curmonad += 1
        


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
        elif tag in self.simple_SR_elements:
            objectTypeName = self.tag2objectTypeName[tag]
            self.createObject(objectTypeName)
        elif tag in self.handled_elements:
            self.handleElementStart(tag, attributes)
        elif tag in self.ignored_elements:
            pass
        else:
            raise ("Error: Unknown start-tag '<" + tag + ">'").encode('utf-8')

        self.addCurMonadToObjects()

    def handleElementStart(self, tag, attributes):
        if tag == "verse":
            if attributes.has_key(u"eID"):
                self.endVerse()
            else:
                self.endVerse()
                self.startVerse(attributes["osisID"])
        elif tag == "chapter":
            if attributes.has_key(u"eID"):
                self.endVerse()
                self.endChapter()
            else:
                self.endVerse()
                self.endChapter()
                self.startChapter(attributes["osisID"])
        elif tag == "p":
            obj = self.createObject("paragraph")
            self.bPrevIsSentenceEnd = True
        elif tag == "title":
            canonical = "false"
            if self.divtypestack[-1] == "bookGroup":
                obj = self.createObject("title")
                obj.setNonStringFeature("divtype", "bookGroup")
            elif self.divtypestack[-1] == "book":
                if self.bInChapter:
                    obj = self.createObject("title")
                    obj.setNonStringFeature("divtype", "chapter")
                    if attributes.has_key("canonical"):
                        if attributes["canonical"] == "true":
                            canonical = "true"
                        else:
                            canonical = "false"
                    else:
                        canonical = "false"
                else:
                    obj = self.createObject("title")
                    obj.setNonStringFeature("divtype", "book")
            obj.setNonStringFeature("canonical", canonical)
        elif tag == "div":
            self.divtypestack.append(attributes["type"])
            if self.divtypestack[-1] == "bookGroup":
                pass
            elif self.divtypestack[-1] == "book":
                self.endVerse()
                self.endChapter()
                self.endBook()
                self.startBook(attributes["osisID"])

    def handleElementEnd(self, tag):
        if tag == "verse":
            pass # All done at start
        elif tag == "chapter":
            pass # All done at start
        elif tag == "p":
            self.endObject("paragraph")
        elif tag == "title":
            if self.divtypestack[-1] == "bookGroup":
                self.endObject("title")
            elif self.divtypestack[-1] == "book":
                self.endObject("title")
            self.bPrevIsSentenceEnd = True
        elif tag == "div":
            self.divtypestack.pop()
            if self.divtypestack[-1] == "bookGroup":
                pass # All done at start
            elif self.divtypestack[-1] == "book":
                pass # All done at start
            self.bPrevIsSentenceEnd = True



    def startBook(self, osisID):
        #if osisID == "Gen":
        #    self.curmonad = 1000
        #elif osisID == "Matt":
        #    self.curmonad = 1000000

        obj = SRObject("book", self.curmonad)
        obj.setNonStringFeature("xmlindex", self.xmlindex)
        self.xmlindex += 1
        obj.setStringFeature("osisID", osisID)
        self.curBook = obj

    def endBook(self):
        if self.curBook != None:
            self.curBook.setLastMonad(self.curmonad-1)
            self.objects.setdefault("book", []).append(self.curBook)
            self.curBook = None


    def startChapter(self, osisID):
        self.bInChapter = True
        obj = SRObject("chapter", self.curmonad)
        obj.setNonStringFeature("xmlindex", self.xmlindex)
        self.xmlindex += 1
        obj.setStringFeature("osisID", osisID)
        (osisBook, osisChapterStr) = osisID.split(".")
        obj.setStringFeature("osisBook", osisBook)
        obj.setNonStringFeature("chapter", osisChapterStr)
        self.curChapter = obj

    def endChapter(self):
        self.bInChapter = False
        self.bPrevIsSentenceEnd = True
        if self.curChapter != None:
            self.curChapter.setLastMonad(self.curmonad-1)
            self.objects.setdefault("chapter", []).append(self.curChapter)
            self.curChapter = None


    def startVerse(self, osisID):
        obj = SRObject("verse", self.curmonad)
        obj.setStringFeature("osisID", " %s " % osisID)
        (osisBook, osisChapterStr, osisVerseStr) = osisID.split(".")
        obj.setStringFeature("osisBook", osisBook)
        obj.setNonStringFeature("chapter", osisChapterStr)
        obj.setNonStringFeature("verse", osisVerseStr)
        obj.setNonStringFeature("xmlindex", self.xmlindex)
        self.xmlindex += 1

        self.curVerse = obj

    def endVerse(self):
        if self.curVerse != None:
            self.curVerse.setLastMonad(self.curmonad-1)
            self.objects.setdefault("verse", []).append(self.curVerse)
            self.curVerse = None

    def endElement(self, tag):
        chars = "".join(self.charstack)
        del self.charstack
        self.charstack = []

        self.handleChars(chars)

        self.curmonad -= 1
        self.addCurMonadToObjects()
        self.curmonad += 1


        if tag in self.nixed_elements:
            oldTag = self.nixing_stack.pop()
            assert tag == oldTag
        elif len(self.nixing_stack) != 0:
            pass
        elif tag in self.simple_SR_elements:
            objectTypeName = self.tag2objectTypeName[tag]
            self.endObject(objectTypeName)
        elif tag in self.handled_elements:
            self.handleElementEnd(tag)
        elif tag in self.ignored_elements:
            pass
        else:
            raise ("Error: Unknown end-tag " + tag).encode('utf-8')

        self.elemstack.pop()


    def dumpMQL(self, fout):
        myobject_types = self.objects.keys()
        myobject_types.sort()

        for objectTypeName in myobject_types:
            count = 0

            sys.stderr.write("Now dumping [%s] ...\n" % objectTypeName)

            fout.write("BEGIN TRANSACTION GO\n")
            fout.write("CREATE OBJECTS WITH OBJECT TYPE [%s]\n" % objectTypeName)
            for obj in self.objects[objectTypeName]:
                obj.dumpMQL(fout)
                count += 1
                if count == 50000:
                    fout.write("GO COMMIT TRANSACTION GO\nBEGIN TRANSACTION GO\n")
                    fout.write("CREATE OBJECTS WITH OBJECT TYPE [%s]\n" % objectTypeName)
                    count = 0
            fout.write("GO\n")
            fout.write("COMMIT TRANSACTION GO\n")


        count = 0

        if self.bDumpTokens:
            sys.stderr.write("Now dumping [Token] ...\n")

            fout.write("BEGIN TRANSACTION GO\n")
            fout.write("CREATE OBJECTS WITH OBJECT TYPE [Token]\n")
            for obj in self.tokens:
                obj.dumpMQL(fout)
                count += 1
                if count == 50000:
                    fout.write("GO COMMIT TRANSACTION GO\nBEGIN TRANSACTION GO\n")
                    fout.write("CREATE OBJECTS WITH OBJECT TYPE [Token]\n")
                    count = 0
            fout.write("GO\n")
            fout.write("COMMIT TRANSACTION GO\n")

        
        fout.write("VACUUM DATABASE ANALYZE GO\n")

        sys.stderr.write("Finished dumping!\n")
        



if len(sys.argv) != 3:
    usage()
    sys.exit(1)
else:
    bDumpTokens = True
    bDoSnippets = False
    if sys.argv[1] == "--OT":
        first_monad = 1
    elif sys.argv[1] == "--NT":
        first_monad = 1000000
    elif sys.argv[1] == "--OTNoTokens":
        first_monad = 1
        bDumpTokens = False
    elif sys.argv[1] == "--OTNoTokensButSnippets":
        first_monad = 1
        bDumpTokens = False
        bDoSnippets = True
    elif sys.argv[1] == "--NTNoTokens":
        first_monad = 1000000
        bDumpTokens = False
        bDoSnippets = False
    elif sys.argv[1] == "--NTNoTokensButSnippets":
        first_monad = 1000000
        bDumpTokens = False
        bDoSnippets = True
    else:
        usage()
        sys.exit(1)
        
    filename = sys.argv[2]

    handler = OSISHandler(first_monad, bDoSnippets)
    handler.bDumpTokens = bDumpTokens

    fin = open(filename, "r")
    sys.stderr.write("Now reading: %s ...\n" % filename)
    xml.sax.parse(fin, handler)
    
    handler.dumpMQL(sys.stdout)

