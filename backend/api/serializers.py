from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.serializers import CustomUserSerializer
from recipes.models import (Tag, Ingredient, Recipe, IngredientAmount,
                            Favorite, ShoppingCartItem)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(IngredientSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['amount'] = (
            IngredientAmount.objects.filter(ingredient=instance)
            .values('amount')[0]['amount']
        )
        return representation


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name',
                  'text', 'image', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCartItem.objects.filter(
            user=request.user, recipe=obj).exists()


class IngredientAmountPostSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipePostSerializer(serializers.ModelSerializer):
    # tags = serializers.PrimaryKeyRelatedField(
    #    queryset=Tag.objects.all(), many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountPostSerializer(many=True)
    image = Base64ImageField()

    def to_representation(self, recipe):
        return RecipeGetSerializer(
            recipe,
            context={'request': self.context.get('request')},
        ).data

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'tags', 'author', 'ingredients',
                  'image', 'text', 'cooking_time')


class RecipeSnippetSerializer(serializers.ModelSerializer):
    pass