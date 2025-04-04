from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from .forms import EmailPostForm
from .models import Post


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 2
    template_name = "blog/post/list.html"


def post_list(request: HttpRequest) -> HttpResponse:
    post_list = Post.published.all()
    paginator = Paginator(post_list, per_page=2)
    page_number = request.GET.get("page", 1)

    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    context = {"posts": posts}
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
    context = {"post": post}
    return render(request, "blog/post/detail.html", context)


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
