from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import User
from foodgram import constants
from colorfield.fields import ColorField


class Ingredient(models.Model):
    """Представляет модель ингредиентов, используемую в рецептах."""
    name = models.CharField(
        max_length=constants.INGREGIENT_NAME_MAX_LENGTH,
        verbose_name='Наименование'
    )
    measurement_unit = models.CharField(
        max_length=constants.INGREGIENT_MEASUREMENT_UNIT_NAME_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        """Класс Meta для модели Ingredient."""
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_fields',
                violation_error_message=(
                    {'name, measurement_unit': 'Поля не уникальны'}
                )
            ),
        )

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Представляет модель тегов, используемую для категоризации рецептов."""
    name = models.CharField(
        max_length=constants.TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Наименование тэга'
    )
    color = ColorField(
        unique=True,
        verbose_name='Цвет'
    )
    slug = models.SlugField(
        max_length=constants.TAG_SLUG_LENGTH
    )

    class Meta:
        """Класс Meta для модели Tag."""
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:20]


class Recipe(models.Model):
    """Модель рецепта"""
    name = models.CharField(
        max_length=constants.RECIPE_NAME_LENGTH,
        verbose_name='Наименование'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    text = models.TextField(verbose_name='Текст')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='recipeingredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                constants.COOKING_TIME_MIN_VALUE,
                message=f'Мининимально {constants.COOKING_TIME_MIN_VALUE}'
            ),
            MaxValueValidator(
                constants.COOKING_TIME_MAX_VALUE,
                message=f'Максимально {constants.COOKING_TIME_MAX_VALUE}'
            ),
        ),
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        """Метакласс модели рецепта."""
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает название рецепта."""
        return self.name[:20]


class RecipeIngredient(models.Model):
    """
    Представляет модель M2M для ингредиентов в рецепте в
    определенном количестве.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                constants.AMOUNT_MIN_VALUE,
                message=(
                    {'amount': f'Мининимально {constants.AMOUNT_MIN_VALUE}'}
                )
            ),
            MaxValueValidator(
                constants.AMOUNT_MAХ_VALUE,
                message=(
                    {'amount': f'Максимально {constants.AMOUNT_MAХ_VALUE}'}
                )
            ),
        ),
        verbose_name='Количество'
    )

    class Meta:
        """Класс Meta модели RecipeIngredient."""
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return f'{self.ingredient.name[:20]}, кол-во: {self.amount}'


class UserRecipeModel(models.Model):
    """
    Представляет абстрактную модель M2M для моделей CustomUser.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        """Класс Meta для модели CommonUserRecipe."""
        abstract = True
        ordering = ['name']
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe',
                violation_error_message=(
                    {'user, recipe': 'Поля должны быть уникальны'}
                )
            ),
        )

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class FavoriteRecipe(UserRecipeModel):
    """
    Унаследован от CommonUserRecipeModel.
    """
    class Meta:
        """Класс Meta для модели FavoriteRecipe."""
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_recipes'

        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name=f'unique_{UserRecipeModel.__name__.lower()}_recipe',
                violation_error_message=(
                    {'user, recipe': 'Поля должны быть уникальны'}
                )
            ),
        )


class ShoppingCart(UserRecipeModel):
    """
    Унаследован от CommonUserRecipeModel.
    """
    class Meta:
        """Класс Meta для модели ShoppingCard."""
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'

    def __str__(self):
        return f'Список покупок {self.user[:20]}'
