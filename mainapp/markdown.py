import mistune


class CustomMarkdownRenderer(mistune.HTMLRenderer):
    def autolink(self, url, is_email=False):
        text = url
        if is_email:
            url = 'mailto:%s' % url
        return '<a href="%s" rel="nofollow">%s</a>' % (url, text)

    def link(self, text, url, title=None):
        if not title:
            return '<a href="%s" rel="nofollow">%s</a>' % (url, text)
        title = escape(title, quote=True)
        return '<a href="%s" title="%s" rel="nofollow">%s</a>' % (url, title, text)


markdown = mistune.create_markdown(renderer=CustomMarkdownRenderer())
