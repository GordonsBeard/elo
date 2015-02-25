from django import template
from django.core.urlresolvers import reverse
from ladder.helpers import PagingInfo

register = template.Library()

class PageListNode( template.Node ) :
  def __init__( self, page_info ) :
    self.page_info  = template.Variable( page_info )

  def render( self, context ) :
    def _resolve_with_context( var ) :
      return var.resolve( context )

    info      = _resolve_with_context( self.page_info )
    html      = ["Pages: "]
    base_url  = _resolve_with_context( template.Variable( 'request' ) ).path
    for p in info.page_list :
      if p == info.page :
        html.append( "<strong>{0}</strong>".format( p ) )
      else :
        html.append( "<a href=\"{0}?p={1}&l={2}\">{1}</a>".format( base_url, p, info.page_length ) )
    return "\n".join( html )

@register.tag
def page_list( parser, token ) :
  try:
    _, page_info = token.split_contents()
  except ValueError :
    raise template.TemplateSyntaxError( "{} tag requires 1 argument, got {}".format( token.contents.split()[0], len(token.split_contents()) ) )
  return PageListNode( page_info )
