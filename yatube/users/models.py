from django.db import models

from .validators import validate_not_empty


# Create your models here.
class Contact(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[validate_not_empty],
        verbose_name='Имя пользователя',
        help_text='Имя пользователя'
    )
    email = models.EmailField(
        verbose_name='Почта пользователя',
        help_text='Почта пользователя'
    )
    subject = models.CharField(
        max_length=100,
        verbose_name='Объект',
        help_text='Объект'
    )
    body = models.TextField(
        validators=[validate_not_empty],
        verbose_name='Описание',
        help_text='Описание'
    )
    is_answered = models.BooleanField(
        default=False,
        verbose_name='Ответ',
        help_text='Ответ'
    )
