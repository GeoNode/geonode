from django import template
from geonode.certification.models import Certification
register = template.Library()

class IsCertifiedNode(template.Node):
    def __init__(self, user, obj, varname):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.varname = varname

    def render(self, context):
        user = self.user.resolve(context)
        obj = self.obj.resolve(context)
        context[self.varname] = Certification.objects.is_certified(user=user, model_obj=obj)
        return ''

class ObjectCertificationsNode(template.Node):
    def __init__(self, obj, varname):
        self.obj = template.Variable(obj)
        self.varname = varname

    def render(self, context):
        obj = self.obj.resolve(context)
        context[self.varname] = Certification.objects.certifications_object(model_obj=obj)
        return ''

class UserCertificationsNode(template.Node):
    def __init__(self, user, varname):
        self.user = template.Variable(user)
        self.varname = varname

    def render(self, context):
        user = self.user.resolve(context)
        context[self.varname] = Certification.objects.certifications_user(user=user)
        return ''

def _check_quoted(string):
    return string[0] == '"' and string[-1] == '"'

@register.tag('is_certified')
def is_certified(parser, token):
    """
    {% is_certified user obj as certified %}
    """
    args = token.split_contents()[1:]
    return IsCertifiedNode(args[0], args[1], args[3])


@register.tag('object_certifications')
def object_certifications(parser, token):
    """
    {% is_certified user obj as certified %}
    """
    args = token.split_contents()[1:]
    return ObjectCertificationsNode(args[0], args[2])

@register.tag('user_certifications')
def user_certifications(parser, token):
    """
    {% is_certified user obj as certified %}
    """
    args = token.split_contents()[1:]
    return UserCertificationsNode(args[0], args[2])
