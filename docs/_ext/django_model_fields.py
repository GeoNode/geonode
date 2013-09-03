'''adapted from http://djangosnippets.org/snippets/2533/

extended with foreign key information, related objects and blank/null details
'''
import inspect
from django.db.models.related import RelatedObject
from django.utils.html import strip_tags
from django.utils.encoding import force_unicode

def process_docstring(app, what, name, obj, options, lines):
    # This causes import errors if left outside the function
    from django.db import models
    
    if inspect.isclass(obj) and issubclass(obj, models.Model):
        meta = obj._meta
        fields = meta.fields + meta.many_to_many + meta.get_all_related_objects()
        processed = [ _process(f) for f in fields ]
        processed.sort(key=lambda f: f[0])
        [ lines.extend(p[1:]) for p in processed if p ] 
    
    return lines
    
def _process(f):
    '''process a field, m2m, or related object.
    
    return a tuple of field name, and param and type strings
    '''
    
    type_fmt = u':type %s: %s'
    rel_type_fmt = u':type %s: %s to :class:`~%s`'
    fqn = lambda c: '%s.%s' % (c.__module__, c.__name__)
    
    if isinstance(f, RelatedObject):
        attname = f.get_accessor_name()
        help_text = '`Generated field`'
        type_tag = rel_type_fmt % (attname, 'RelatedManager', fqn(f.model))
        meta = ''
    else:
        help_text = strip_tags(force_unicode(f.help_text))
        verbose_name = force_unicode(f.verbose_name).capitalize()

        meta = []

        if f.blank:
            meta.append('Blank')
        if f.null:
            meta.append('Null')

        if meta:
            meta = '[ %s ]' % ' , '.join(['%s' % m for m in meta ])
        else:
            meta = ''

        attname = getattr(f, 'name', getattr(f, 'attname', None))
        
        # Add the field's type to the docstring
        rel = getattr(f, 'rel', None)
        if rel:
            to = f.rel.to if hasattr(f.rel, 'to') else f.through
            type_tag = rel_type_fmt % (attname, type(f).__name__, fqn(to))
        else:
            type_tag = type_fmt % (attname, type(f).__name__)
       
    fmt_args = ( attname,
                 meta,
                 help_text or verbose_name
               )

    return attname, u':param %s: %s %s' % fmt_args, type_tag


if __name__ == '__main__':
    '''just for testing to avoid entire sphinx build'''
    import sys
    from geonode.layers.models import Layer
    l = process_docstring(None,None,None,Layer,None,[])
    print '\n'.join([str(i) for i in l])
 
