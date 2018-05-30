import mistune

class CustomMarkdownRenderer(mistune.Renderer):
    def autolink(self, link, is_email=False):
        text = link = mistune.escape_link(link)
        if is_email:
            link= 'mailto:%s' % link
        return '<a href="%s" rel="nofollow">%s</a>' % (link, text)

    def link(self, link, title, text):
        link = mistune.escape_link(link)
        if not title:
            return '<a href="%s" rel="nofollow">%s</a>' % (link, text)
        title = escape(title, quote=True)
        return '<a href="%s" title="%s" rel="nofollow">%s</a>' % (link, title, text)

markdown = mistune.Markdown(renderer=CustomMarkdownRenderer())
