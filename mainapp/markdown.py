import mistune

class CustomMarkdownRenderer(mistune.HTMLRenderer):
    def autolink(self, link, is_email=False):
        text = link
        if is_email:
            link = 'mailto:%s' % link
        return '<a href="%s" rel="nofollow">%s</a>' % (link, text)

    def link(self, text, link, title=None):
        if not title:
            return '<a href="%s" rel="nofollow">%s</a>' % (link, text)
        title = escape(title, quote=True)
        return '<a href="%s" title="%s" rel="nofollow">%s</a>' % (link, title, text)

markdown = mistune.create_markdown(renderer=CustomMarkdownRenderer())
