"""
Test for models
"""
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
# We could import model directly, but it is a better practice to import it like this
from django.contrib.auth import get_user_model

from core import models


class UserModelTests(TestCase):
    def test_user_has_all_fields(self):
        """
        Tests if UserProfile model has fields: name, email, is_staff, is_active
        And if they are set correctly
        """
        password = 'testPass123'
        email = 'test-req-fields@email.test'
        name = 'Test Name'

        user = get_user_model().objects.create_user(email=email, password=password, name=name)

        self.assertEqual(user.name, name)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.email, email)
        self.assertIs(user.is_active, True)
        self.assertIs(user.is_staff, False)

    def test_user_email_as_required_field(self):
        """
        If email is not provided, UserProfile must raised an Exception
        """
        password = 'testPass123'
        name = 'Test Name'
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(password=password, name=name)

    def test_user_email_must_be_valid(self):
        """
        Users email must be valid, if not it must raise an ValidationError
        """
        password = 'testPass123'
        invalid_emails = ['', ' ', None, 'invalid_email.com', 'invalidEmail.com']

        for invalid_email in invalid_emails:
            with self.assertRaises(ValidationError):
                get_user_model().objects.create_user(email=invalid_email, password=password)

    def test_user_has_normalized_email(self):
        """
        Tests if UserProfile model normalizes email
        """
        email = 'test-normal@Email.TesT'
        normalized_email = 'test-normal@email.test'
        password = 'testPass123'

        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, normalized_email)

    def test_users_has_same_email_error(self):
        """
        Email must be a unique field, so two users cannot have same email
        """
        password = 'testPass123'
        password2 = 'testPass675'
        email = 'test-same@email.test'

        get_user_model().objects.create_user(email=email, password=password)
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(email=email, password=password2)

    def test_create_superuser_successfuly(self):
        """
        Superuser must be created a User with property is_staff equals True
        """
        password = 'testPass123'
        email = 'test-super@email.test'
        name = 'Test Name'

        superuser = get_user_model().objects.create_superuser(email=email, password=password, name=name)

        self.assertEqual(superuser.name, name)
        self.assertTrue(superuser.check_password(password))
        self.assertEqual(superuser.email, email)
        self.assertIs(superuser.is_active, True)
        self.assertIs(superuser.is_staff, True)
        self.assertIs(superuser.is_superuser, True)


class RecipeModelTests(TestCase):
    def test_create_recipe(self):
        """Test creating a recipe is successful"""
        user = get_user_model().objects.create_user(
            email='user@test.test',
            password='testpass123'
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description'
        )

        self.assertEqual(str(recipe), recipe.title)


class TagModelTests(TestCase):
    def test_create_tag(self):
        """Test creating a tag is successful"""
        user = get_user_model().objects.create_user(
                email='user@test.test',
                password='testpass123'
            )
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)
