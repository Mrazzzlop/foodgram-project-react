from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny
)
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

from users.models import CustomUser
from recipes.models import (
    FavoriteRecipe, Ingredient,
    Recipe, RecipeIngredient,
    ShoppingCart, Tag
)

from .filters import IngredientSearchFilter, RecipeFilterBackend
from .paginators import PageLimitPagination
from .permissions import isAdminOrAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer, FavoriteRecipeSerializer,
    IngredientSerializer, RecipeAddSerializer,
    RecipeListSerializer, ShoppingCartSerializer,
    SubscriptionCreateSerializer, TokenSerializer,
    SubscriptionListSerializer, TagSerializer
)


class CustomUserViewSet(UserViewSet):
    """Вьюсет юзера."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request, pk=None):
        queryset = CustomUser.objects.filter(
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
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = request.user
        following = get_object_or_404(CustomUser, pk=id)
        serializer = SubscriptionCreateSerializer(
            data={
                'user': user.id,
                'following': following.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        following = get_object_or_404(CustomUser, pk=id)

        delete_cnt, _ = (
            request.user
            .follower.filter(following=following)
            .delete()
        )
        if not delete_cnt:
            return Response(
                {'subscribe': 'Нет подписки.'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthToken(ObtainAuthToken):
    """Авторизация пользователя."""

    serializer_class = TokenSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингридиента."""
    queryset = Ingredient.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = IngredientSerializer
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецепта."""
    queryset = Recipe.objects.all()
    filterset_class = RecipeFilterBackend
    serializer_class = RecipeListSerializer
    pagination_class = PageLimitPagination
    permission_classes = [isAdminOrAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('list', 'retrive'):
            return RecipeListSerializer
        return RecipeAddSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        serializer = FavoriteRecipeSerializer(
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

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        get_object_or_404(Recipe, id=pk)
        user_id = request.user.id
        delete_cnt, _ = FavoriteRecipe.objects.filter(
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
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        user = request.user
        serializer = ShoppingCartSerializer(
            data={
                'user': user.id,
                'recipe': pk
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        get_object_or_404(ShoppingCart, recipe_id=pk)
        delete_cnt, _ = ShoppingCart.objects.filter(
            user__id=request.user.id,
            recipe__id=pk
        ).delete()
        if not delete_cnt:
            return Response(
                {'subcribe': 'Нет покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        ).annotate(total_sum=Sum('amount'))
        wishlist = '\n'.join([
            f'{ingredient["ingredient__name"]}: '
            f'{ingredient["total_sum"]} '
            f'{ingredient["ingredient__measurement_unit"]}.'
            for ingredient in ingredients
        ])
        response = HttpResponse(wishlist, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=wishlist.txt'
        return response
