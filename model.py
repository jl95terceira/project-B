import dataclasses
import enum
import io
import xml.parsers.expat as expat
from   _util import *

class DocX:

    def __init__(self, docxfn:str):

        self._generic:dict[str,Element] = {}
        for fn,f in internal_files_by_name(docxfn):

            if fn == '_rels/.rels' and False:

                self._rels = Relationships(f)
            
            else:

                self._generic[fn] = load_etree(f)

    def save(self,docxfn:str):

        with zipfile.ZipFile(file=docxfn, mode='w') as zf:

            for fn,et in self._generic.items():

                with zf.open(name=fn, mode='w') as f:

                    dump_etree(f, et)

@dataclasses.dataclass
class XmlDecl:

    version   :str
    encoding  :str
    standalone:bool

class Relationships:

    @dataclasses.dataclass
    class Relationship:

        type  :str
        target:'Target'

        class Target(enum.Enum):

            APP      = 0
            CORE     = 1
            DOCUMENT = 2

    _rel_target_map = {
        'docProps/app.xml' : Relationship.Target.APP,
        'docProps/core.xml': Relationship.Target.CORE,
        'word/document.xml': Relationship.Target.DOCUMENT
    }

    def __init__(self, f:io.BytesIO):

        xp = expat.ParserCreate()
        class _State(enum.Enum):

            INIT          = 0
            RELATIONSHIPS = 1

        st = [_State.INIT]
        def xmldeclh(vers,enc,stal):

            self._xmldecl = XmlDecl(version=vers,encoding=enc,standalone=bool(stal))

        xp.XmlDeclHandler = xmldeclh
        self._rels = {}
        def startelemh(name:str, attrs:dict[str,str]):

            if st[0] is _State.INIT:

                if name != 'Relationships': raise Exception('found at root an element other than Relationships')
                self._xmlns = attrs['xmlns']
                st[0] = _State.RELATIONSHIPS
            
            elif st[0] is _State.RELATIONSHIPS:

                if name != 'Relationship': raise Exception('found in Relationships an element that is not a Relationship')
                self._rels[attrs['Id']] = Relationships.Relationship(type=attrs['Type'],target=Relationships._rel_target_map[attrs['Target']])

        xp.StartElementHandler = startelemh
        xp.ParseFile(f)
