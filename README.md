# ODS Export

1. Use directions

 - /\<date\>/xml for marc xml output  - ODS daily export; e.g./20200701/xml
 
 - /\<date\>/xml856 ; adds 856 tags to the marcxml using decorator
  
 - /\<date>\/symbols for text ouput ; e.g./20200701/symbols
  
 - /\<date\>/json for json output ; e.g./20200701/json

 - /\<date\>/S daily document symbols starting with S/ ; e.g. 20200701/S
  
 - /unbis for T codes lookup table -> ~7500 records
 - /\<date\>/unbis
  
 
 use 'skip' and 'limit' url parameters for pagination; default values: skip=0&limit=50; e.g. ?limit=64
 
 2. UNBIS Thesaurus TCode lookup endpoints work as below:
 
  - /tcode/\<tcode\>; /tcode/T0000898 ; for {T0000898: "CONSUMER COOPERATIVES"}
 
  - /label/\<label\>; /label/CONSUMER COOPERATIVES ; for {CONSUMER COOPERATIVES: "T0000898"}
 

3. /pdf/\<path:path\>
   - DEPRECATED  - list the English pdf  for the symbol ( e.g./pdf/A/C.5/44/SR.41 )
4. /intoods ; /exporttoods
   - self-service option; used for sending metadata to the ODS; DEPRECATED with the introduction of ODS Actions
5. /itp/<ITPsection>/\<path:path\>
   - list ITP sections as **datasets** (json) e.g.(/itp/itss/A/78)

6. /ds/\<path:path\>
   - display metadata for document symbol in json (e.g./ds/A/RES/77/1)
7. /xml/\<path:path\> ; /xml856/\<path:path\>
    - marcxml for the symbol ( e.g. /xml/A/RES/77/1)
8. /list/\<query\>
    - parameters are tag, query
    - sorting 269 by default
    - 
 9. /\<lan code\>symbol
  
