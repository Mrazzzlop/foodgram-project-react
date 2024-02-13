import contextlib
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from users.models import CustomUser, Subscription
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


class CustomUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follower.filter(user=obj).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class RecipeListSerializer(serializers.ModelSerializer):

    author = CustomUserSerializer(
        read_only=True
    )
    tags = TagSerializer(
        many=True,
        read_only=True,
    )
    ingredients = RecipeIngredientAmountSerializer(
        many=True,
        source='recipe'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.favorite_recipes.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.shopping_carts.filter(recipe=obj).exists()
        )


class RecipeAddSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = AddIngredientSerializer(
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate(self, attrs):
        tags = attrs.get('tags')
        ingredients = attrs.get('ingredients')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Поле отсутствует'}
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Поле отсуствует'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не уникальны'}
            )

        unique_ingr = {item['id'] for item in ingredients}
        if len(unique_ingr) != len(ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'Дублирование ингредиентов'}
            )

        if not attrs.get('image'):
            raise serializers.ValidationError(
                {'image': 'Нет картинки'}
            )

        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        request = self.context.get('request')
        recipe = Recipe.objects.create(
            author=request.user,
            **validated_data
        )
        recipe.tags.set(tags)
        return self._make_recipe(ingredients, recipe)

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()

        super().update(instance, validated_data)

        return self._make_recipe(ingredients, instance)

    @staticmethod
    def _make_recipe(ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )
        return recipe

    def to_representation(self, instance):
        return RecipeListSerializer(instance).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionListSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if recipes_limit := request.query_params.get('recipes_limit'):
            with contextlib.suppress(ValueError):
                recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = (
            'user',
            'following'
        )

    def validate(self, attrs):
        user = attrs['user']
        following = attrs['following']
        if user == following:
            raise serializers.ValidationError(
                {'following': 'Нельзя подписаться на себя.'}
            )

        if user.follower.filter(following=following).exists():
            raise serializers.ValidationError(
                {'following': 'Уже подписан.'}
            )

        return attrs

    def to_representation(self, instance):
        return SubscriptionListSerializer(
            instance.following,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']

        if user.shopping_carts.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                {'recipe': 'Уже в корзине.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']

        if user.favorite_recipes.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                {'recipe': 'Уже добавлен.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data