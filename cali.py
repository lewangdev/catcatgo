import os
import re
import shutil
import errno
import html
import logging
from os import listdir
from os.path import join, split, splitext

import yaml
import misaka as m
from jinja2 import Environment, FileSystemLoader
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from xml.sax.saxutils import escape

logging.basicConfig(format='[%(asctime)s] p%(process)s %(pathname)s:%(lineno)d %(levelname)s - %(message)s',
        level=logging.DEBUG)

def copy(src, dst):
    try:
        if os.path.exists(dst):
            shutil.rmtree(dst)

        shutil.copytree(src, dst)
    except OSError as exc:  # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError:
        pass


def load_conf(conffile_path='_config.yml'):
    with open(conffile_path, 'r') as conffile:
        return yaml.load(conffile.read(), Loader=yaml.FullLoader)


def read(fpath):
    with open(fpath, 'r') as f:
        return f.read()


def parse_page(content):
    lines = content.splitlines()

    split_pos = 0
    for line in lines:
        if line == '---' and split_pos > 1:
            break
        split_pos += 1

    meta = yaml.load("\n".join(lines[1:split_pos]), Loader=yaml.FullLoader)
    html = "\n".join(lines[split_pos + 1:])
    return dict(meta=meta, html=html,
            title=meta.get('title', ''),
            order=meta.get('order', 0),
            description=meta.get('description', ''),
            header_img=meta.get('header_img', ''))


class HighlighterRenderer(m.HtmlRenderer):
    def blockcode(self, text, lang):
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            lexer = None

        if lexer:
            formatter = HtmlFormatter()
            return highlight(text, lexer, formatter)

        text_escaped = '\n<pre>\n<code>\n%s\n</code>\n</pre>\n' % html.escape(text)
        return text_escaped


def parse_post(postfile_path, mdrender):
    parent_path, filename = split(postfile_path)
    name, ext = splitext(filename)

    with open(postfile_path, 'r') as postfile:
        lines = postfile.read().splitlines()
        split_pos = 0
        for line in lines:
            if line == '---' and split_pos > 1:
                break
            split_pos += 1

        meta = yaml.load("\n".join(lines[1:split_pos]), Loader=yaml.FullLoader)
        content = "\n".join(lines[split_pos + 1:])

        meta['file'] = dict(archive=name[:len('yyyy-MM-dd')], name=name[len('yyyy-MM-dd') + 1:], ext=ext)
        return dict(meta=meta, markdown=content, html=mdrender(content),
                catalog=meta.get('catalog', False))


## filters for jinja2
def date_format(value, format='%b %d, %Y'):
    return value.strftime(format)

def strip_html(value):
    v = re.sub('<[^<]+?>', '', value)
    return v

def xml_escape(value):
    return escape(value)

def prepend(value, prefix):
    return "%s%s" % (prefix, value)

def markdownify(md):
    mdrender = m.Markdown(HighlighterRenderer(), extensions=('fenced-code', 'tables', 'autolink', 'no-intra-emphasis'))
    return mdrender(md)

class RubyLikeList(list):
    """
    We use templates for JekyII, Create this list to make jinja2 work well with these templates.
    """
    def __init__(self):
        super(RubyLikeList, self).__init__()

    @property
    def size(self):
        return self.__len__()


def paginate(posts, limit=10):
    total_count = len(posts)
    total_pages = int((total_count - 1) / limit + 1)
    paginators = []
    for i in range(total_pages):
        paginator = dict(total_pages=total_pages, posts=posts[i*limit:(i+1)*limit])
        if i > 0:
            paginator['previous_page'] = True
            paginator['previous_page_path'] = '/' if i == 1 else '/page%s' % (i - 1)

        if i < total_pages - 1:
            paginator['next_page'] = True
            paginator['next_page_path'] = '/page%s' % (i + 1)

        paginators.append(paginator)

    return paginators


def build():
    # load site config
    site = load_conf()
    theme_path = 'themes/%s' % site.get('theme', 'default')
    data_path = site.get('data_dir', '_data')
    output_path = site.get('output_path', 'dist')

    # create markdown doc render object
    mdrender = m.Markdown(HighlighterRenderer(), extensions=('fenced-code', 'tables', 'autolink', 'no-intra-emphasis'))

    # copy static files to output_path
    assets = ['css', 'fonts', 'img', 'js', 'CNAME', 'README.md']
    for asset in assets:
        copy('%s/%s' % (theme_path, asset), '%s/%s' % (output_path, asset))

    posts_path = '%s/_posts' % data_path
    docs = [parse_post(join(posts_path, f), mdrender) for f in listdir(posts_path) if
            f.endswith('.markdown') or f.endswith('.md')]

    # init jinja2
    template_path = os.path.join(os.path.dirname(__file__), theme_path)
    env = Environment(loader=FileSystemLoader(template_path))
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.filters['date'] = date_format
    env.filters['strip_html'] = strip_html
    env.filters['prepend'] = prepend
    env.filters['xml_escape'] = xml_escape
    env.filters['markdownify'] = markdownify

    # tags
    tags = {}

    # archives
    archives = {}

    # posts
    posts = []
    for doc in docs:
        post = dict(
            previous={},
            next={},
            title=doc['meta']['title'],
            subtitle=doc['meta']['subtitle'],
            header_img=doc['meta']['header_img'],
            date=doc['meta']['date'],
            tags=doc['meta']['tags'],
            author=doc['meta']['author'],
            url='/%s/%s' % (doc['meta']['file']['archive'].replace('-', '/'), doc['meta']['file']['name']),
            catalog=doc['catalog'],
            multilangual=doc['meta'].get('multilangual', 0),
            meta=doc['meta'],
            content=doc['html']
        )
        posts.append(post)
        for tag in post['tags']:
            tag_posts = tags.get(tag, RubyLikeList())
            tag_posts.append(post)
            tags[tag] = tag_posts
        archive_name = '-'.join(post['meta']['file']['archive'].split('-')[:2])
        archive_posts = archives.get(archive_name, RubyLikeList())
        archive_posts.append(post)
        archives[archive_name] = archive_posts

    # sort from now to past and paginate it
    posts.sort(key=lambda p: p["date"].timetuple(), reverse=True)

    for i in range(len(posts)):
        if i > 0:
            posts[i]['previous'] = dict(url=posts[i - 1]['url'], title=posts[i - 1]['title'])
        if i < len(posts) - 1:
            posts[i]['next'] = dict(url=posts[i + 1]['url'], title=posts[i + 1]['title'])

    tags_keys = list(tags.keys())
    tags_keys.sort()
    site['tags'] = [tag for tag in map(lambda t: [t, tags[t]], tags_keys)]

    archives_keys = list(archives.keys())
    archives_keys.sort(reverse=True)
    site['archives'] = [archive for archive in map(lambda a: [a, archives[a]],
        archives_keys)]

    paginators = paginate(posts, limit=site['paginate'])

    pages = []
    pages_path = theme_path
    pagefile_paths = [join(pages_path, f) for f in listdir(pages_path) if
                      f.endswith('.html') or f.endswith('.htm')]
    for pagefile_path in pagefile_paths:
        parent_path, filename = split(pagefile_path)
        name, ext = splitext(filename)
        page = parse_page(read(pagefile_path))

        if name in set(['index']):
            for i in range(len(paginators)):
                content = env.get_template(pagefile_path[len(theme_path):]) \
                    .render(dict(site=site, page=page['meta'], paginator=paginators[i]))
                page = parse_page(content)
                name = 'index' if i == 0 else 'page%s' % i
                page['file'] = dict(name=name, ext=ext)
                page['url'] = '/%s' % name
                pages.append(page)
        else:
            content = env.get_template(pagefile_path[len(theme_path):]) \
                .render(dict(site=site, page=page['meta'], paginator={}))
            page = parse_page(content)
            page['file'] = dict(name=name, ext=ext)
            page['url'] = '/%s' % name
            pages.append(page)

    site['pages'] = sorted(pages, key=lambda p: p.get('order', 0))

    # create html for posts
    for post in posts:
        html = env.get_template('_layouts/%s.html' % (post['meta']['layout'])) \
            .render(dict(site=site, page=post, content=post['content']))
        path = '%s%s' % (output_path, post['url'])
        mkdir(path)
        with open("%s/index.html" % path, "w") as htmlfile:
            htmlfile.write(html)

    # create html for pages
    for page in pages:
        html = env.get_template('_layouts/%s.html' % (page['meta']['layout'])) \
            .render(dict(site=site, page=page, content=page['html']))

        if page['file']['name'] in set(['index', '404']):
            with open("%s/%s.html" % (output_path, page['file']['name']), "w") as htmlfile:
                htmlfile.write(html)
        else:
            mkdir('%s/%s' % (output_path, page['file']['name']))
            with open("%s/%s/index.html" % (output_path, page['file']['name']), "w") as htmlfile:
                htmlfile.write(html)

    logging.info("%s posts and %s pages are processed.", len(posts), len(pages))

if __name__ == '__main__':
    build()

