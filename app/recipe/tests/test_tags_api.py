from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

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

