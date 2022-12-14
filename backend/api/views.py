import io

import reportlab
from django.conf import settings
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCartItem, Tag)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.permissions import IsAuthor

from .filters import IngredientSearchFilter, RecipeFilter
from .mixins import CreateDestroyViewSet, ListViewSet
from .serializers import (IngredientSerializer, RecipeGetSerializer,
                          RecipePostSerializer, RecipeSnippetSerializer,
                          TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny, ]
        elif self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, ]
        elif self.request.method == 'PATCH' or 'DELETE':
            self.permission_classes = [IsAuthor, ]
        return super(RecipeViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostSerializer

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            IngredientAmount.objects.bulk_create(
                [IngredientAmount(
                    ingredient=ingredient_id,
                    recipe=recipe, amount=amount
                )]
            )

    def perform_create(self, serializer):
        author = self.request.user
        ingredients = serializer.validated_data.pop('ingredients')
        recipe = serializer.save(author=author)
        self.create_ingredients(ingredients, recipe)

    def perform_update(self, serializer):
        data = serializer.validated_data
        ingredients = data.pop('ingredients')
        tags = data.pop('tags')
        instance = serializer.save()
        if ingredients:
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if tags:
            instance.tags.set(tags)


class FavoriteViewSet(CreateDestroyViewSet):

    def get_object(self):
        return get_object_or_404(Recipe, id=self.kwargs['recipe_id'])

    def create(self, request, model=Favorite,
               message='Recipe already in favorites',
               *args, **kwargs):
        instance = self.get_object()
        favorite = model.objects.filter(user=request.user, recipe=instance)
        if favorite:
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=request.user, recipe=instance)
        serializer = RecipeSnippetSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, model=Favorite,
                message='Recipe not in favorites',
                *args, **kwargs):
        instance = self.get_object()
        favorite = model.objects.filter(user=request.user, recipe=instance)
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(FavoriteViewSet):

    def create(self, request, *args, **kwargs):
        return FavoriteViewSet.create(
            self, request, model=ShoppingCartItem,
            message='Recipe already in shopping cart',
            *args, **kwargs
        )

    def destroy(self, request, *args, **kwargs):
        return FavoriteViewSet.destroy(
            self, request, model=ShoppingCartItem,
            message='Recipe not in shopping cart',
            *args, **kwargs
        )


class DownloadShoppingList(ListViewSet):
    permission_classes = [IsAuthenticated, ]

    def download_shopping_list(self, request):
        reportlab.rl_config.TTFSearchPath.append(
            str(settings.BASE_DIR) + '/data/')
        pdfmetrics.registerFont(TTFont(
            'ClearSans', 'ClearSans-Regular.ttf'))
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setFont(psfontname='ClearSans', size=12)
        left_margin = 100
        bottom_margin = 700

        shopping_list = (
            IngredientAmount.objects
            .filter(recipe__recipe_to_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        if not shopping_list:
            pdf.drawString(left_margin - 25, bottom_margin + 40,
                           'Shopping List is empty. Add some'
                           ' recipes to shopping cart:)')
        else:
            pdf.drawString(left_margin - 25, bottom_margin + 40,
                           'Shopping List')
            for recipe in shopping_list:
                pdf.drawString(
                    left_margin, bottom_margin,
                    f'{recipe["ingredient__name"]}, '
                    f'{recipe["ingredient__measurement_unit"]} :   '
                    f'{recipe["total_amount"]}'
                )
                bottom_margin -= 20
                if bottom_margin == 100:
                    pdf.showPage()
                    pdf.setFont(psfontname='ClearSans', size=12)
                    bottom_margin = 740

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='Shopping_list.pdf')
