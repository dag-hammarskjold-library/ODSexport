import os, re, time
from functools import wraps
from dlx import DB
from dlx.marc import AuthSet, BibSet, QueryDocument, Condition
from dlx.file import File, Identifier
from .config import Config
import xml.etree.ElementTree as ET

DB.connect(Config.connect_string)
#collection = Config.DB.bibs



''' add 856 to the records in the collection;
    use elem_856 to get files info as a string XML - record is the root;
    fun uses a bibset as an input param
'''
def add_856(f):
    @wraps(f)
    def wrapper(*args):

        res = f(*args)
        #res is a bibset.to_xml, root is a collection
        ts1=time.time()
        root = ET.fromstring(res)
        for rec in root.findall('record'):
            for datafield in rec.findall('datafield'):
                if datafield.get("tag")=="191":
                    for subfield in datafield.findall("subfield"):
                        if subfield.get("code")=="a":
                            symbol = subfield.text
            print(f" time trav. xml is {time.time()-ts1}")
            ts=time.time()
            #txt_856=elem_856(symbol)
            #rc_856=ET.fromstring(txt_856)
            
            rc_856=elem_856(symbol)
            print(f"  time fetching elem_856 is {time.time()-ts}")
            ts5=time.time()
            for dfld in rc_856.findall('datafield'):
                rec.append(dfld)
            print(f"   time appending 856 datafields is {time.time()-ts5}")
        modified=ET.tostring(root, encoding="utf-8")

        return modified
    return wrapper

'''
return xml string of all files datafields for a symbol
'''

def elem_856(symbol):
    rc=ET.Element("record")
    for xfile in File.find_by_identifier(Identifier('symbol', symbol)):
        df = ET.SubElement(rc,"datafield")
        df.set("tag","856")
        df.set("ind1","4")
        df.set("ind2","0")

        sf_y=ET.SubElement(df,"subfield")
        sf_y.set("code",'y')
        sf_y.text=''.join(xfile.languages)

        sf_9=ET.SubElement(df,"subfield")
        sf_9.set("code",'9')
        sf_9.text=str(xfile.id)

        sf_s=ET.SubElement(df,"subfield")
        sf_s.set("code",'s')
        sf_s.text=str(xfile.size)

        sf_u=ET.SubElement(df,"subfield")
        sf_u.set("code",'u')
        sf_u.text=str(xfile.uri)    
    #return ET.tostring(rc)
    return rc


































def timeit(f):
    @wraps(f)
    def timed(*args, **kw):
        print(f"print anything")
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print(f"func:{f.__name__} took: {te-ts} sec",flush=True)
        return result

    return timed
