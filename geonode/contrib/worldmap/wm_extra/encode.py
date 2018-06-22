import string
from htmllib import HTMLParser
from cgi import escape
from urlparse import urlparse
from formatter import AbstractFormatter
from htmlentitydefs import entitydefs
from xml.sax.saxutils import quoteattr
import re

ALPHABET = string.ascii_uppercase + string.ascii_lowercase + \
           string.digits + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'


def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0:
            break
    return ''.join(reversed(s))


def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n


def xssescape(text):
    """Gets rid of < and > and & and, for good measure, :"""
    return escape(text, quote=True).replace(':', '&#58;')


def despam(text):
    """
    Rudimentary bad word filter, to be replaced soon by something more solid
    """
    return re.sub(
                    r'c.?[i1].?[a@].?[l1].?[i1].?[s$]|v.?[Ii1].?[a@].?gr.?[a@]|[l1].?[e3].?v.?[i!1].?t.?r.?[a@]|\
                    -online|4u|adipex|advicer|baccarrat|blackjack|bllogspot|booker|byob|car-rental-e-site|car-rentals-e-site|\
                    carisoprodol|c.?[a@].?[s$].?[i!1].?n.?[o0]|chatroom|coolhu|coolhu|credit-card-debt|credit-report|cwas|cyclen|\
                    benzaprine|dating-e-site|day-trading|debt-consolidation|debt-consolidation|discreetordering|\
                    duty-free|dutyfree|equityloans|fioricet|flowers-leading-site|freenet-shopping|freenet|gambling-|hair-loss|\
                    health-insurancedeals-4u|homeequityloans|homefinance|holdem|\
                    hotel-dealse-site|hotele-site|hotelse-site|incest|insurance-quotesdeals-4u|insurancedeals-4u|jrcreations|\
                    macinstruct|mortgage-4-u|mortgagequotes|online-gambling|onlinegambling-4u|ottawavalleyag|ownsthis|\
                    palm-texas-holdem-game \
                    |p.?[a@].?x.?[i1!].?[l!1]|penis|pharmacy|phentermine|poker-chip|poze|pussy|rental-car-e-site|ringtones\
                    |roulette |shemale|shoes|slot-machine|\
                    shit|fuck|damn|cunt|ass.?hole|ass.?wipe|jackass|bitch|twat|whore|cock.?sucker|faggot| \
                    texas-holdem|thorcarlson|top-site|top-e-site|tramadol|trim-spa|\
                    ultram|v.?[i1!].?[o0].?x|x.?[a@].?n.?[a@].?x|zolus' + '(?i)', r'', text
    )


class XssCleaner(HTMLParser):
    """
    Cross-site scripting protection, from http://code.activestate.com/recipes/496942-cross-site-scripting-xss-defense/
    """
    def __init__(self, fmt=AbstractFormatter):
        HTMLParser.__init__(self, fmt)
        self.result = ""
        self.open_tags = []
        # A list of forbidden tags.
        self.forbidden_tags = ['script', 'embed', 'iframe', 'frame', ]

        # A list of tags that require no closing tag.
        self.requires_no_close = ['img', 'br']

        # A dictionary showing the only attributes allowed for particular tags.
        # If a tag is not listed here, it is allowed no attributes.  Adding
        # "on" tags, like "onhover," would not be smart.  Also be very careful
        # of "background" and "style."

#         <h5 style="text-align: center;"><b><i><u><font size="5" face="impact">THIS IS A TEST</font></u></i></b></h5>
#         <blockquote style="margin: 0 0 0 40px; border: none; padding: 0px;"><p style="text-align: center;">
#         <font size="5" face="arial" color="#cc3333">of the EBS</font></p><p style="text-align: center;">
#         <font size="5" face="arial"><br></font></p><p style="text-align: center;"><font size="5" face="arial">
#         <sup>reddit</sup><sub>2</sub></font></p>
#         <p style="text-align: center;"><font size="5" face="arial"><sub><br></sub></font></p>
#         <p style="text-align: center;"><font size="5" face="arial">fiiiiiii<sub>4</sub></font></p>
#         <p style="text-align: center;"><font size="5" face="arial"><sub><br></sub></font></p>
#         <p style="text-align: center;"><hr><br></p><p style="text-align: center;">
#         <strike>strike</strike></p></blockquote>

        self.allowed_attributes =\
            {'a': ['href', 'title', 'target', 'style'],
             'p': ['style'],
             'img': ['src', 'alt', 'border', 'style', 'align'],
             'blockquote': ['type', 'style', 'align'],
             'font': ['size', 'face', 'align'],
             'h5': ['style'], 'h4': ['style'], 'h3': ['style'], 'h2': ['style'], 'h1': ['style'],
             'table': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             'tbody': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             'tr': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             'td': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             'div': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             'span': ['border', 'width', 'height', 'style', 'align', 'bgcolor'],
             }

        # The only schemes allowed in URLs (for href and src attributes).
        # Adding "javascript" or "vbscript" to this list would not be smart.
        self.allowed_schemes = ['http', 'https', 'ftp']

    def handle_data(self, data):
        if data:
            self.result += xssescape(data)

    def handle_charref(self, ref):
        if len(ref) < 7 and ref.isdigit():
            self.result += '&#%s;' % ref
        else:
            self.result += xssescape('&#%s' % ref)

    def handle_entityref(self, ref):
        if ref in entitydefs:
            self.result += '&%s;' % ref
        else:
            self.result += xssescape('&%s' % ref)

    def handle_comment(self, comment):
        if comment:
            self.result += xssescape("<!--%s-->" % comment)

    def handle_starttag(self, tag, method, attrs):
        if tag in self.forbidden_tags:
            self.result += xssescape("<%s>" % tag)
        else:
            bt = "<" + tag
            if tag in self.allowed_attributes:
                attrs = dict(attrs)
                self.allowed_attributes_here =\
                [x for x in self.allowed_attributes[tag] if x in attrs and
                    len(attrs[x]) > 0
                ]
                for attribute in self.allowed_attributes_here:
                    if attribute in ['href', 'src', 'background']:
                        if self.url_is_acceptable(attrs[attribute]):
                            bt += ' %s="%s"' % (attribute, attrs[attribute])
                    else:
                        bt += ' %s=%s' %\
                              (xssescape(attribute), quoteattr(attrs[attribute]))
            if bt == "<a" or bt == "<img":
                return
            if tag in self.requires_no_close:
                bt += "/"
            bt += ">"
            self.result += bt
            self.open_tags.insert(0, tag)

    def handle_endtag(self, tag, attrs):
        bracketed = "</%s>" % tag
        if tag in self.forbidden_tags:
            self.result += xssescape(bracketed)
        elif tag in self.open_tags:
            self.result += bracketed
            self.open_tags.remove(tag)

    def unknown_starttag(self, tag, attributes):
        self.handle_starttag(tag, None, attributes)

    def unknown_endtag(self, tag):
        self.handle_endtag(tag, None)

    def url_is_acceptable(self, url):
        # Requires all URLs to be "absolute."
        parsed = urlparse(url)
        return parsed[0] in self.allowed_schemes and '.' in parsed[1]

    def strip(self, rawstring):
        """Returns the argument stripped of potentially harmful HTML or Javascript code"""
        self.result = ""
        self.feed(rawstring)
        for endtag in self.open_tags:
            if endtag not in self.requires_no_close:
                self.result += "</%s>" % endtag
        return self.result

    def xtags(self):
        """Returns a printable string informing the user which tags are allowed"""
        self.forbidden_tags.sort()
        tg = ""
        for x in self.forbidden_tags:
            tg += "<" + x
            if x in self.allowed_attributes:
                for y in self.allowed_attributes[x]:
                    tg += ' %s=""' % y
            tg += "> "
        return xssescape(tg.strip())
        # end of http://code.activestate.com/recipes/496942/ }}}
