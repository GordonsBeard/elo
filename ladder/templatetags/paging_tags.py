from django import template
from django.core.urlresolvers import reverse
from ladder.helpers import PagingInfo

register = template.Library()

class PageListNode( template.Node ) :
  def __init__( self, page_info, base_url, url_args ) :
    self.page_info  = template.Variable( page_info )
    print self.page_info
    self.base_url   = base_url
    self.url_args   = map( template.Variable, url_args )

  def render( self, context ) :
    def _resolve_with_context( var ) :
      return var.resolve( context )

    info = _resolve_with_context( self.page_info )
    html = ["Pages: "]
    for p in info.page_list :
      if p == info.page :
        html.append( "<strong>{0}</strong>".format( p ) )
      else :
        link = reverse( self.base_url, args = map( _resolve_with_context, self.url_args ) )
        html.append( "<a href=\"{0}?p={1}&l={2}\">{1}</a>".format( link, p, info.page_length ) )
    return "\n".join( html )

@register.tag
def page_list( parser, token ) :
  try:
    split     = token.split_contents()
    page_info = split[1]
    base_url  = split[2]
    url_args  = split[3:]
  except ValueError :
    raise template.TemplateSyntaxError( "{} tag requires 3 arguments, got {}".format( token.contents.split()[0], len(token.split_contents()) ) )
  return PageListNode( page_info, base_url, url_args )
