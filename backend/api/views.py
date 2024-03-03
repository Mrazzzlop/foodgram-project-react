from django.db.models import Sum
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from users.models import User
from recipes.models import (
    FavoriteRecipe, Ingredient,
    Recipe, RecipeIngredient,
    ShoppingCart, Tag
)
from .services import generate_wishlist_file
from .filters import IngredientSearchFilter, RecipeFilterBackend
from .paginators import PageLimitPagination
from .permissions import AuthorOrReadOnly
from .serializers import (
    UserSerializer, FavoriteRecipeSerializer,
    IngredientSerializer, RecipeAddSerializer,
    RecipeListSerializer, ShoppingCartSerializer,
    SubscriptionCreateSerializer,
    SubscriptionListSerializer, TagSerializer
)


class UserViewSet(UserViewSet):
    """Вьюсет юзера."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, pk=None):
        queryset = User.objects.filter(
            following__user=self.request.user
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionListSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        user = request.user
        serializer = SubscriptionCreateSerializer(
            data={
                'user': user.id,
                'following': id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):

        delete_cnt, _ = (
            request.user
            .follower.filter(following=id)
            .delete()
        )
        if not delete_cnt:
            return Response(
                {'subscribe': 'Нет подписки.'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингридиента."""

    queryset = Ingredient.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецепта."""

    queryset = Recipe.objects.all().select_related('author').prefetch_related('tags', 'ingredients')
    filterset_class = RecipeFilterBackend
    serializer_class = RecipeListSerializer
    pagination_class = PageLimitPagination
    permission_classes = (AuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrive'):
            return RecipeListSerializer
        return RecipeAddSerializer

    @staticmethod
    def add_method(serializer, request, pk):
        serializer = serializer(
            data={
                'user': request.user.id,
                'recipe': pk
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def delete_method(model, request, pk):
        user_id = request.user.id
        delete_cnt, _ = model.objects.filter(
            user__id=user_id,
            recipe__id=pk
        ).delete()
        if not delete_cnt:
            return Response(
                {'subcribe': 'Нет избранного.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.add_method(FavoriteRecipeSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_method(FavoriteRecipe, request, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.add_method(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_method(ShoppingCart, request, pk)

    @action(
        methods=('get',),
        url_path='download_shopping_cart',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_sum=Sum('amount')).order_by('total_sum')

        return generate_wishlist_file(ingredients)
