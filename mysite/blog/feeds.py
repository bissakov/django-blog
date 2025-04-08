from django.contrib.syndication.views import Feed
from django.db.models import DateTimeField, QuerySet
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from markdown import markdown

from .models import Post


class LatestPostsFeed(Feed):
    title = "My blog"
    link = reverse_lazy("blog:post_list")
    description = "New posts of the blog."

    def items(self) -> QuerySet[Post]:
        return Post.published.all()[:5]

    def item_title(self, item: Post) -> str:
        return item.title

    def item_description(self, item: Post) -> str:
        return truncatewords_html(markdown(item.body), 30)

    def item_pubdate(self, item: Post) -> DateTimeField:
        return item.publish
