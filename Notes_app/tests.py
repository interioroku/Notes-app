from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from .models import Note

class PersonalNotesAPITests(APITestCase):

    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create a note for user1
        self.note1 = Note.objects.create(
            user=self.user1,
            title='User 1 Note 1',
            description='This is user1\'s note'
        )

    def test_user_registration_success(self):
        """Test user registration endpoint with valid data."""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')

    def test_user_registration_missing_email(self):
        """Test registration fails if email is missing."""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_login_success(self):
        """Test user login endpoint returns token."""
        url = reverse('login')
        data = {
            'username': 'user1',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['token'], self.token1.key)

    def test_user_login_invalid_credentials(self):
        """Test login fails with incorrect password."""
        url = reverse('login')
        data = {
            'username': 'user1',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_create_note_authenticated(self):
        """Test that authenticated users can create notes."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        url = reverse('note-list')
        data = {
            'title': 'New Note Title',
            'description': 'New Note Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Note Title')
        self.assertEqual(response.data['user'], 'user1')

    def test_create_note_unauthenticated(self):
        """Test note creation fails without authentication."""
        url = reverse('note-list')
        data = {
            'title': 'Unauthorized Note',
            'description': 'No auth header'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_own_notes(self):
        """Test that a user can see only their own notes."""
        # Authenticate user1
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        url = reverse('note-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'User 1 Note 1')

        # Authenticate user2 (has no notes)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token2.key)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_retrieve_own_note(self):
        """Test retrieving a specific note belonging to the user."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        url = reverse('note-detail', kwargs={'pk': self.note1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'User 1 Note 1')

    def test_retrieve_other_user_note_fails(self):
        """Test retrieving another user's note returns 404 (Not Found)."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token2.key)
        url = reverse('note-detail', kwargs={'pk': self.note1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_note(self):
        """Test updating a note belonging to the user."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        url = reverse('note-detail', kwargs={'pk': self.note1.id})
        data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        
        # Verify db updated
        self.note1.refresh_from_db()
        self.assertEqual(self.note1.title, 'Updated Title')

    def test_delete_own_note(self):
        """Test deleting a note belonging to the user."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        url = reverse('note-detail', kwargs={'pk': self.note1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Note.objects.filter(id=self.note1.id).exists())
