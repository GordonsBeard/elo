from django import template

register = template.Library()

class CanChallengeNode(template.Node):
    def __init__(self, user, challengee, ladder):
        self.user = template.Variable(user)
        self.challengee = template.Variable(challengee)
        self.ladder = template.Variable(ladder)
    def render(self, context):
        user = self.user.resolve(context)
        challengee = self.challengee.resolve(context)
        if user.is_authenticated() and user != challengee:
            return "<a href='challenge/{0}'>Challenge this user</a>".format(challengee.pk)
        else:
            return ""

@register.tag
def can_user_be_challenged(parser, token):
    """ This tag returns a link if a user can be challenged. """
    try:
        tag_name, user, challengee, ladder = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires 3 arguments" % token.contents.split()[0])
    return CanChallengeNode(user, challengee, ladder)
