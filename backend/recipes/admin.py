from django.contrib import admin

from .models import (
    Ingredient,
    FavoriteRecipe,
    RecipeIngredient,
    Recipe,
    Tag,
    ShoppingCart
)


class IngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'pub_date',
        'added_in_favorites',
        'display_ingredients',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )
    inlines = (IngredientInline,)

    @admin.display(description='В избранном')
    def added_in_favorites(self, obj):
        return obj.favorite_recipes.count()

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()]
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_filter = ('name', 'color')
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = '-пусто-'


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = '-пусто-'
