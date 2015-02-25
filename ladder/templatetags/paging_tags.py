from django import template
from django.core.urlresolvers import reverse
from ladder.helpers import PagingInfo

register = template.Library()

PAGE_LIST_CUTOFF = 15

class PageListNode( template.Node ) :
  def __init__( self, page_info ) :
    self.page_info  = template.Variable( page_info )

  def render( self, context ) :
    def _resolve_with_context( var ) :
      return var.resolve( context )

    info      = _resolve_with_context( self.page_info )
    html      = ["Pages: "]
    base_url  = _resolve_with_context( template.Variable( 'request' ) ).path

    half_cut  = int(PAGE_LIST_CUTOFF / 2)
    first     = info.page - 1 - half_cut if info.page > half_cut else 0
    last      = first + PAGE_LIST_CUTOFF if info.page > half_cut else PAGE_LIST_CUTOFF

    # Previous page link
    if info.page > 1 :
      html.append( "<a href=\"{0}?p={1}&l={2}\">&lt; Previous</a>".format( base_url, info.page - 1, info.page_length ) )

    # First page link
    if first > 0 :
      html.append( "<a href=\"{0}?p={1}&l={2}\">&lt;&lt; {1}</a> ...".format( base_url, 1, info.page_length ) )

    # Page jump links
    for p in info.page_list[first:last] :
      if p == info.page :
        html.append( "<strong>{0}</strong>".format( p ) )
      else :
        html.append( "<a href=\"{0}?p={1}&l={2}\">{1}</a>".format( base_url, p, info.page_length ) )

    # Last page link
    if last < len( info.page_list ) :
      html.append( "... <a href=\"{0}?p={1}&l={2}\">{1} &gt;&gt;</a>".format( base_url, info.page_list[-1], info.page_length ) )

    # Next page link
    if info.page < len( info.page_list ) :
      html.append( "<a href=\"{0}?p={1}&l={2}\">Next &gt;</a>".format( base_url, info.page + 1, info.page_length ) )

    return "\n".join( html )

@register.tag
def page_list( parser, token ) :
  try:
    _, page_info = token.split_contents()
  except ValueError :
    raise template.TemplateSyntaxError( "{} tag requires 1 argument, got {}".format( token.contents.split()[0], len(token.split_contents()) ) )
  return PageListNode( page_info )
