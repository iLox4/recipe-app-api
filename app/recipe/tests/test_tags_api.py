from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe
)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """Returns a url for getting tag detail"""
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@test.test', password='testpass123'):
    """Creates and returns a user"""
    user = get_user_model().objects.create_user(
            email=email,
            password=password
    )
    return user


class PublicTagsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_tags_unauth(self):
        """API must returns 401 if user is not authorized"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()

        self.client.force_authenticate(user=self.user)

    def test_list_tags_auth(self):
        """API must return a list of tags that was created by user"""
        Tag.objects.create(name='Test Tag', user=self.user)
        Tag.objects.create(name='Test Tag2', user=self.user)

        another_user = create_user(
            email='another@test.test',
            password='testpass123'
        )
        Tag.objects.create(name='Another Tag', user=another_user)

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.filter(user=self.user).order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag_auth(self):
        """Tests updating a tag"""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        res = self.client.patch(detail_url(tag.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag_auth(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name='Tag to delete')

        res = self.client.delete(detail_url(tag.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Cheap')
        tag2 = Tag.objects.create(user=self.user, name='Fast')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list"""
        tag = Tag.objects.create(user=self.user, name='Fast')
        recipe1 = Recipe.objects.create(
            title='Fried Eggs',
            time_minutes=5,
            price=Decimal('3.00'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Boiled Eggs',
            time_minutes=10,
            price=Decimal('2.00'),
            user=self.user
        )

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)

