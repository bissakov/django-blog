from typing import Dict

from django import template
from django.db.models import Count, QuerySet
from django.utils.safestring import SafeString, mark_safe
from markdown import markdown

from ..models import Post

register = template.Library()


@register.simple_tag
def total_posts() -> int:
    return Post.published.count()


@register.inclusion_tag("blog/post/latest_posts.html")
def show_latest_posts(count: int = 5) -> Dict[str, QuerySet[Post]]:
    latest_posts = Post.published.order_by("-publish")[:count]
    context = {"latest_posts": latest_posts}
    return context


@register.simple_tag
def get_most_commented_posts(count: int = 5) -> QuerySet[Post]:
    posts = Post.published.annotate(total_comments=Count("comments")).order_by(
        "-total_comments"
    )[:count]
    return posts


@register.filter(name="markdown")
def markdown_format(text: str) -> SafeString:
    return mark_safe(markdown(text))
