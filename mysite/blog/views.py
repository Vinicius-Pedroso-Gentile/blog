from django.shortcuts import get_object_or_404, render
from .models import Post
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import CommentForm, EmailPostForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count


def post_list(request, tag_slug=None):
	post_list = Post.published.all()
	tag = None
	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		post_list = post_list.filter(tags__in = [tag])
	paginator = Paginator(post_list, 3)
	page_number = request.GET.get('page', 1)

	try:
		posts = paginator.page(page_number)

	except PageNotAnInteger:
		posts = paginator.page(paginator.num_pages)

	return render(
		request,
		'blog/post/list.html',
		{
			'posts': posts,
			'tag': tag
		}
	)
 
# class PostListView(ListView):
# 	"""
# 	Alternative post list view
# 	"""
# 	queryset = Post.published.all()
# 	context_object_name = 'posts'
# 	paginate_by = 3
# 	template_name = 'blog/post/list.html'

def post_detail(request, year, month, day, post):
	post = get_object_or_404(Post,status=Post.Status.PUBLISHED, slug=post,
		publish__year=year,
		publish__month=month,
		publish__day=day)
	# List of active comments for this post, aqui ele está usando o related_name
	comments = post.comments.filter(active=True)

	post_tags_ids = post.tags.values_list('id', flat=True) # Aqui ele pegou o id de todas as tags que tem relação com post
	similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id) # Aqui filtramos esses ids e tiramos o do nosso post
	# Nesse cara aqui a gente cria um campo novo para a nossa tabela usando o annotate e com isso a gente ordena de acordo
	similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]

	form = CommentForm()
	return render(
		request,
		'blog/post/detail.html',
		{
			'post': post,
			'form': form,
			'comments': comments,
			'similar_posts': similar_posts
		},
	)


def post_share(request, post_id):
	post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
	sent = False
	if request.method == 'POST':
		form = EmailPostForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			post_url = request.build_absolute_uri(post.get_absolute_url())
			subject = f"{cd['name']} recommends you read " \
				f"{post.title}"
			message = f"Read {post.title} at {post_url}\n\n" \
				f"{cd['name']}\'s comments: {cd['comments']}"
			send_mail(subject, message, 'vinicius.p.gentile@gmail.com',[cd['to']])
			sent = True
	else:
		form = EmailPostForm()
	return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
	post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
	comment = None
	form = CommentForm(data=request.POST)

	if form.is_valid():
		# Create a Comment object without saving it to the database
		comment = form.save(commit=False)
		# Assign the post to the comment
		comment.post = post
		# Save the comment to the database
		comment.save()

	return render(request, 'blog/post/comment.html',
	{'post': post,
	'form': form,
	'comment': comment})