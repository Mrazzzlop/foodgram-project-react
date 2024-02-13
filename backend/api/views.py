import io

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from users.models import CustomUser
from .filters import IngredientSearchFilter, RecipeFilterBackend
from .paginators import PageLimitPagination
from .permissions import isAdminOrAuthorOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteRecipeSerializer,
                          IngredientSerializer, RecipeAddSerializer,
                          RecipeListSerializer, ShoppingCartSerializer,
                          SubscriptionCreateSerializer,
                          SubscriptionListSerializer, TagSerializer)


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
    serializer_class = RecipeListSerializer
    pagination_class = PageLimitPagination
    permission_classes = [isAdminOrAuthorOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RecipeFilterBackend

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
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, pk=None):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        pdfmetrics.registerFont(
            TTFont(
                'Arial',
                str(settings.BASE_DIR / 'data/ArialRegular.ttf')
            )
        )
        p.setFont('Arial', 16)
        x, y = 100, 750

        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values_list(
                'ingredient__name',
                'ingredient__measurement_unit',
                'amount'
            )
        )
        shop_list = {}
        for ingredient in ingredients:
            name = ingredient[0]
            if name not in shop_list:
                shop_list[name] = {
                    'measurement_unit': ingredient[1],
                    'amount': ingredient[2]
                }
            shop_list[name]['amount'] += ingredient[2]

        for item, value in shop_list.items():
            p.drawString(
                x,
                y,
                f'{item} {value["amount"]} {value["measurement_unit"]}'
            )
            y -= 24
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_cart.pdf',
        )
