from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.models import User, Subscription
from foodgram import constants
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
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
    amount = serializers.IntegerField(
        min_value=constants.INGREDIENT_MIN, max_value=constants.INGREDIENT_MAX,
        error_messages={
            'invalid':
                f'Кол-во должно быть в диапазоне от {constants.INGREDIENT_MIN} до {constants.INGREDIENT_MAX}'
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class RecipeListSerializer(serializers.ModelSerializer):

    author = UserSerializer(
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
    author = UserSerializer(
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = AddIngredientSerializer(
        many=True,
    )
    image = Base64ImageField(allow_null=False, allow_empty_file=False)

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
        self._make_recipe(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()

        self._make_recipe(ingredients, instance)
        return super().update(instance, validated_data)

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
        return RecipeListSerializer(instance, context=self.context).data


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


class SubscriptionListSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except (ValueError, TypeError):
                recipes_limit = None
            if recipes_limit is not None:
                recipes = recipes[:recipes_limit]

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
            context=self.context
        ).data


class BaseRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        model = None
        fields = (
            'user',
            'recipe'
        )

    def validate(self, attrs):
        user = attrs['user']
        recipe = attrs['recipe']
        existing_check = self.Meta.model.objects.filter(user=user, recipe=recipe).exists()

        if existing_check:
            raise serializers.ValidationError(
                {'recipe': 'Уже существует.'}
            )
        return attrs

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context
        ).data


class ShoppingCartSerializer(BaseRecipeSerializer):
    class Meta(BaseRecipeSerializer.Meta):
        model = ShoppingCart


class FavoriteRecipeSerializer(BaseRecipeSerializer):
    class Meta(BaseRecipeSerializer.Meta):
        model = FavoriteRecipe
