/*
 * Parser for human readable OSM geo data search queries.
 */

start
  = _ x:geo_query _ { return x }

geo_query
  = x:query whitespace+ ( "in bbox" / "IN BBOX" )
    { return { bounds:"bbox", query:x } }
  / x:query whitespace+ ( "in" / "IN" ) whitespace+ y:string
    { return { bounds:"area", query:x, area:y } }
  / x:query whitespace+ ( "around" / "AROUND" ) whitespace+ y:string
    { return { bounds:"around", query:x, area:y } }
  / x:query whitespace+ ( "global" / "GLOBAL" )
    { return { bounds:"global", query:x } }
  / x:query
    { return { bounds:"bbox", query:x } }

query
  = logical_or

logical_or
  = x:logical_and whitespace+ ( "or" / "OR" / "||" / "|" ) whitespace+ y:logical_or
    { return { logical:"or", queries:[x,y] } }
  /*
  / x:logical_and whitespace+ ( "xor" / "XOR" ) whitespace+ y:logical_and
    { return { logical:"xor", queries:[x,y] } }
  / x:logical_and whitespace+ ( "except" / "EXCEPT" ) whitespace+ y:logical_and
    { return { logical:"minus", queries:[x,y] } }
  */
  / x:logical_and

logical_and
  = x:braces whitespace+ ( "and" / "AND" / "&&" / "&" ) whitespace+ y:logical_and
    { return { logical:"and", queries:[x,y] } }
  / x:braces

/*logical_not
  =  TODO? */

braces
  = statement
  / "(" _ x:logical_or _ ")" { return x; }

statement
  = type
  / meta
  / key_eq_val
  / key_not_eq_val
  / key_present
  / key_not_present
  / key_like_val
  / like_key_like_val
  / key_not_like_val
  / key_substr_val
  / free_form

key_eq_val
  = x:key_string _ ( "=" / "==" ) _ y:string
    { return { query:"eq", key:x, val:y } }

key_not_eq_val
  = x:key_string _ ( "!=" / "<>" ) _ y:string
    { return { query:"neq", key:x, val:y } }

key_present
  = x:key_string _ ( "=" / "==" ) _ "*"
    { return { query:"key", key:x } }
  / x:string whitespace+ ("is" whitespace+ "not" whitespace+ "null" / "IS" whitespace+ "NOT" whitespace+ "NULL")
    { return { query:"key", key:x } }

key_not_present
  = x:key_string _ ( "!=" / "<>" ) _ "*"
    { return { query:"nokey", key:x } }
  / x:string whitespace+ ("is" whitespace+ "null" / "IS" whitespace+ "NULL")
    { return { query:"nokey", key:x } }

key_like_val
  = x:key_string _ ( "~=" / "~" / "=~" ) _ y:(string / regexstring )
    { return { query:"like", key:x, val:y.regex?y:{regex:y} } }
  / x:string whitespace+ ("like" / "LIKE") whitespace+ y:(string / regexstring )
    { return { query:"like", key:x, val:y.regex?y:{regex:y} } }

like_key_like_val
  = "~" _ x:string/*(key_string / regexstring)*/ _ ( "~=" / "~" / "=~" ) _ y:(string / regexstring )
    { return { query:"likelike", key:x, val:y.regex?y:{regex:y} } }

key_not_like_val
  = x:key_string _ ( "!~" ) _ y:(string / regexstring )
    { return { query:"notlike", key:x, val:y.regex?y:{regex:y} } }
  / x:string whitespace+ ("not" whitespace+ "like" / "NOT" whitespace+ "LIKE") whitespace+ y:(string / regexstring )
    { return { query:"notlike", key:x, val:y.regex?y:{regex:y} } }

key_substr_val
  = x:string _ ( ":" ) _ y:string
    { return { query:"substr", key:x, val:y } }

type
  = "type" _ ":" _ x:string
    { return { query:"type", type:x } }

meta // TODO?
  = x:("user" / "uid" / "newer" / "id") _ ":" _ y:string
    { return { query:"meta", meta:x, val:y } }

free_form
  = x:string
    { return { query:"free form", free:x } }

/* ==== strings ==== */

key_string "Key"
  = s:[a-zA-Z0-9_:-]+ { return s.join(''); }
  / parts:('"' DoubleStringCharacters '"' / "'" SingleStringCharacters "'") {
      return parts[1];
    }

string "string"
  = s:[^'" ()~=!*/:<>&|[\]{}#+@$%?^.,]+ { return s.join(''); }
  / parts:('"' DoubleStringCharacters '"' / "'" SingleStringCharacters "'") {
      return parts[1];
    }

DoubleStringCharacters
  = chars:DoubleStringCharacter* { return chars.join(""); }

SingleStringCharacters
  = chars:SingleStringCharacter* { return chars.join(""); }

DoubleStringCharacter
  = !('"' / "\\") char_:.        { return char_;     }
  / "\\" sequence:EscapeSequence { return sequence;  }

SingleStringCharacter
  = !("'" / "\\") char_:.        { return char_;     }
  / "\\" sequence:EscapeSequence { return sequence;  }

EscapeSequence
  = CharacterEscapeSequence
  // / "0" !DecimalDigit { return "\0"; }
  // / HexEscapeSequence
  // / UnicodeEscapeSequence //TODO?

CharacterEscapeSequence
  = SingleEscapeCharacter

SingleEscapeCharacter
  = char_:['"\\bfnrtv] {
      return char_
        .replace("b", "\b")
        .replace("f", "\f")
        .replace("n", "\n")
        .replace("r", "\r")
        .replace("t", "\t")
        .replace("v", "\x0B") // IE does not recognize "\v".
    }

/* ==== regexes ==== */

regexstring "string"
  = parts:('/' (RegexStringCharacters) '/' ('i'/'')?) {
      return { regex: parts[1], modifier: parts[3] };
    }

RegexStringCharacters
  = chars:RegexStringCharacter+ { return chars.join(""); }

RegexStringCharacter
  = !('/' / "\\/") char_:. { return char_;     }
  / "\\/"                  { return "/";  }


/* ===== Whitespace ===== */

_ "whitespace"
  = whitespace*

whitespace "whitespace"
  = [ \t\n\r]
