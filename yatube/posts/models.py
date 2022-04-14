from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_posts',
        verbose_name='Автор поста',
        help_text='Автор поста'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self) -> str:
        return f'{self.text[:15]}'


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Название группы'
    )
    slug = models.SlugField(
        'Group',
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Описание группы'
    )

    def __str__(self) -> str:
        return f'{self.title}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Коментируемый пост',
        help_text='Коментируемый пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
        help_text='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время публикации комментария'
    )
    active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return f'Комментарий от {self.author} к {self.post}'
