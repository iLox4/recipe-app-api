import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """Create and return an image upload URL"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@test.test',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'password123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99')
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)

        for tag in payload['tags']:
            exists = recipes[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')

        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Breakfast'}, {'name': 'Teasty'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)

        for tag in payload['tags']:
            exists = recipes[0].tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

        tags = Tag.objects.filter(user=self.user)
        self.assertEqual(tags.count(), 2)

        exists = Tag.objects.filter(user=tag_breakfast.user, name=tag_breakfast.name).exists()
        self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {
            'tags': [{'name': 'Thai'}]
        }
        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for tag in payload['tags']:
            new_tag = Tag.objects.get(name=tag['name'], user=self.user)
            self.assertIsNotNone(new_tag)
            # We do not need to refresh if we are using recipe.tags.all()
            # because we set the relation as many to many =>
            # when we call it, it would perform a new query
            # so it must get all new tags
            self.assertIn(new_tag, recipe.tags.all())

    def test_assign_tag_on_update(self):
        """Test assigning tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name='Fast')

        payload = {
            'tags': [{'name': 'Fast'}]
        }
        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Tag.objects.get(id=tag.id))
        self.assertIn(tag, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating recipe with new ingredients"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'ingredients': [{'name': 'rice'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes[0].ingredients.count(), 1)

        for payload_ingredient in payload['ingredients']:
            ingredient = Ingredient.objects.get(name=payload_ingredient['name'], user=self.user)
            self.assertIsNotNone(ingredient)
            self.assertIn(ingredient, recipes[0].ingredients.all())

    def test_create_recipe_with_existing_ingredients(self):
        """Test assigning existing ingredients to the new recipe"""
        ingredient = Ingredient.objects.create(name='rice', user=self.user)

        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'ingredients': [{'name': 'rice'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Ingredient.objects.filter(id=ingredient.id).exists())

        recipes = Recipe.objects.filter(user=self.user)
        self.assertIn(ingredient, recipes[0].ingredients.all())

    def test_create_ingredient_on_update(self):
        """Test creating new ingredients with recipe update"""
        recipe = create_recipe(user=self.user)

        payload = {
            'ingredients': [{'name': 'rice'}]
        }

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient = Ingredient.objects.get(user=self.user, name=payload['ingredients'][0]['name'])
        self.assertIsNotNone(ingredient)
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_assign_ingredient_on_update(self):
        """Test assigning ingredients to the recipe on recipe update"""
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='water')

        payload = {
            'ingredients': [{'name': 'water'}]
        }

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient_db = Ingredient.objects.filter(id=ingredient.id)
        self.assertTrue(ingredient_db.exists())

        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title='Thai Curry')
        r2 = create_recipe(user=self.user, title='Aubergine with tahini')

        tag1 = Tag.objects.create(user=self.user, name='Thai')
        tag2 = Tag.objects.create(user=self.user, name='Vegeterian')

        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_recipe(user=self.user, title='Fish and chips')

        params = {
            'tags': f'{tag1.id},{tag2.id}'
        }
        res = self.client.get(RECIPES_URL, params)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients"""
        r1 = create_recipe(user=self.user, title='Thai Curry')
        r2 = create_recipe(user=self.user, title='Aubergine with tahini')

        ing1 = Ingredient.objects.create(user=self.user, name='Rice')
        ing2 = Ingredient.objects.create(user=self.user, name='Tahini')

        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)

        r3 = create_recipe(user=self.user, title='Fish and chips')

        parameters = {
            'ingredients': f'{ing1.id},{ing2.id}'
        }
        res = self.client.get(RECIPES_URL, parameters)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)



class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@test.test',
            'password123'
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {
                'image': image_file
            }
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)

        payload = {
            'image': 'notanimage'
        }
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)





