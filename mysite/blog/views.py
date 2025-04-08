from typing import Optional

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from taggit.models import Tag

from .forms import CommentForm, EmailPostForm, SearchForm
from .models import Comment, Post


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 2
    template_name = "blog/post/list.html"


def post_list(
    request: HttpRequest, tag_slug: Optional[str] = None
) -> HttpResponse:
    post_list = Post.published.all()

    tag = get_object_or_404(Tag, slug=tag_slug) if tag_slug else None
    if tag:
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, per_page=5)
    page_number = request.GET.get("page", 1)

    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    context = {"posts": posts, "tag": tag}
    return render(request, "blog/post/list.html", context)


def post_detail(
    request: HttpRequest, year: int, month: int, day: int, slug: str
) -> HttpResponse:
    post = get_object_or_404(
        Post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
        slug=slug,
        status=Post.Status.PUBLISHED,
    )
    comments = Comment.objects.filter(post=post, active=True).all()
    form = CommentForm()

    post_tags_ids = post.tags.values_list("id", flat=True)
    similar_posts = (
        Post.published.filter(tags__in=post_tags_ids)
        .exclude(id=post.id)
        .annotate(same_tags=Count("tags"))
        .order_by("-same_tags", "-publish")[:4]
    )

    context = {
        "post": post,
        "comments": comments,
        "form": form,
        "similar_posts": similar_posts,
    }
    return render(request, "blog/post/detail.html", context)


@require_POST
def post_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None

    form = CommentForm(data=request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    context = {"post": post, "form": form, "comment": comment}
    return render(request, "blog/post/comment.html", context)


def post_share(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method != "POST":
        form = EmailPostForm()
    else:
        form = EmailPostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            name, email, to, comments = (
                data["name"],
                data["email"],
                data["to"],
                data["comments"],
            )
            post_url = request.build_absolute_uri(post.get_absolute_url())

            subject = f"{name} ({email}) recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n{name}'s comments: {comments}"

            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[to],
            )
            sent = True

    context = {"post": post, "form": form, "sent": sent}
    return render(request, "blog/post/share.html", context)


def post_search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("query")
    form = SearchForm(request.GET or None)
    results = []

    if query and form.is_valid():
        query = form.cleaned_data["query"]
        vector = SearchVector("title", weight="A") + SearchVector(
            "body", weight="B"
        )
        search_query = SearchQuery(query)
        results = (
            Post.published.annotate(
                rank=SearchRank(vector, search_query),
                trigram_title=TrigramSimilarity("title", query),
                trigram_body=TrigramSimilarity("body", query),
            )
            .filter(
                Q(rank__gte=0.1)
                | Q(trigram_title__gte=0.3)
                | Q(trigram_body__gte=0.3)
            )
            .annotate(score=F("rank") + F("trigram_title") + F("trigram_body"))
            .order_by("-score")
        )

    context = {"form": form, "query": query, "results": results}
    return render(request, "blog/post/search.html", context)
