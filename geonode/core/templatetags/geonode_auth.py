from django import template

register = template.Library()

class HasObjPermNode(template.Node):
    def __init__(self, user, obj, perm, varname):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.perm = perm
        self.varname = varname

    def render(self, context):
        user = self.user.resolve(context)
        obj = self.obj.resolve(context)
        context[self.varname] = user.has_perm(self.perm, obj=obj)
        return ''

def _check_quoted(string):
    return string[0] == '"' and string[-1] == '"'

@register.tag('has_obj_perm')
def do_has_obj_perm(parser, token):
    """
    {% has_obj_perm user obj "app.view_thing" as can_view_thing %}
    """
    args = token.split_contents()[1:]
    return HasObjPermNode(args[0], args[1], args[2][1:-1], args[4])
