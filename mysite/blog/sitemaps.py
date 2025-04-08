from django.contrib.sitemaps import Sitemap
from django.db import models

from .models import Post


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self) -> models.QuerySet[Post]:
        return Post.published.all()

    def lastmod(self, obj: Post) -> models.DateTimeField:
        return obj.updated
