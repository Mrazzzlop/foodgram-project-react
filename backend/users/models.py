from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db.models import Q, F

from foodgram import constants


class User(AbstractUser):
    """Модель Пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    first_name = models.CharField(
        max_length=constants.FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя',
        help_text='Введите имя пользователя'
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия',
        help_text='Введите фамилию пользователя'
    )
    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
        unique=True,
        verbose_name='Логин',
        help_text='Введите логин пользователя',
        validators=(
            UnicodeUsernameValidator(),
        ),
    )
    email = models.EmailField(
        unique=True,
        verbose_name='E-mail',
        help_text='Введите email пользователя'
    )

    class Meta:
        """Класс Meta модели User."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель Подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Кто подписан на автора'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписан автор',
    )

    class Meta:
        """Класс Meta модели Subscription."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following',),
                name='unique_subscription_fields',
                violation_error_message=(
                    {'subscription': 'Уже подписан.'}
                )
            ),
            models.CheckConstraint(
                check=~Q(user=F('following')),
                name='self_subscription',
                violation_error_message=(
                    {'subscription': 'Нельзя подписаться на себя.'}
                )
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
