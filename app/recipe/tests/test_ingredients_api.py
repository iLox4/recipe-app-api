from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    """Returns a url for getting ingredient detail"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@test.test', password='testpass123'):
    """Creates and returns a user"""
    user = get_user_model().objects.create_user(
            email=email,
            password=password
    )
    return user


class PublicIngredientsAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_list_ingredients_unauth(self):
        """API must return 401 if user is not authorized"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()

        self.client.force_authenticate(user=self.user)

    def test_list_ingredients_auth(self):
        """API must return a list of the ingredients created by user"""
        another_user = create_user(email='user2@test.test')

        Ingredient.objects.create(name='rice', user=self.user)
        Ingredient.objects.create(name='wine', user=self.user)
        Ingredient.objects.create(name='ham', user=another_user)

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.filter(user=self.user).order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_ingredient_auth(self):
        """Test updating an ingredient"""
        payload = {
            'name': 'rice'
        }
        ingredient = Ingredient.objects.create(name='ryce', user=self.user)

        res = self.client.patch(detail_url(ingredient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient_auth(self):
        """Test deleting an ingredient"""
        ingredient = Ingredient.objects.create(name='milk', user=self.user)

        res = self.client.delete(detail_url(ingredient.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())


