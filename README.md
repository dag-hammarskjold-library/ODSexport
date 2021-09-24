# ODS Export

1. Use directions

 - /\<date\>/xml for marc xml output ; e.g./20200701/xml
 - /\<date\>/xml999
 - /\<date\>/xmlupdated
 
 - /\<date\>/xml856 ; adds 856 tags to the xml using decorator
  
 - /\<date>\/symbols for text ouput ; e.g./20200701/symbols
  
 - /\<date\>/json for json output ; e.g./20200701/json

 - /\<date\>/S for document symbols starting with S/ ; e.g. 20200701/S
  
 - /unbis for T codes lookup table -> ~7500 records
 - /\<date\>/unbis
  
 <date\> format is yyyymmdd or yyyy-mm-dd
 if \<date\> is less than optimal it defaults to today
 
 use 'skip' and 'limit' url parameters for pagination; default values: skip=0&limit=50; e.g. ?limit=64
 
 2. UNBIS Thesaurus TCode lookup endpoints work as below:
 
  - /tcode/\<tcode\>; /tcode/T0000898 ; for {T0000898: "CONSUMER COOPERATIVES"}
 
  - /label/\<label\>; /label/CONSUMER COOPERATIVES ; for {CONSUMER COOPERATIVES: "T0000898"}
 

3. /pdf/\<path:path\>
4. /intoods ; /exporttoods
5. /itpitsp/\<path:path\>
6. /date
7. /ds/\<path:path\>
8. /xml/\<path:path\> ; /xml856/\<path:path\>
9. /votes/\<topic\>
10. 
  
