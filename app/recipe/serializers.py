from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient

from typing import TypeVar

T = TypeVar('T', Tag, Ingredient)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag object"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient object"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe object"""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def _get_or_create_objects(self, objects: list[T], recipe_objects: list[T], ObjectClass: T):
        """Gets or creats objects as needed"""
        auth_user = self.context['request'].user
        for object in objects:
            object_obj, _ = ObjectClass.objects.get_or_create(
                user=auth_user,
                **object
            )
            recipe_objects.add(object_obj)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_objects(tags, recipe.tags, Tag)
        self._get_or_create_objects(ingredients, recipe.ingredients, Ingredient)

        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_objects(tags, instance.tags, Tag)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_objects(ingredients, instance.ingredients, Ingredient)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes"""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}

