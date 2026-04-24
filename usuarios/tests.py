from django.test import TestCase
from django.contrib.auth import authenticate
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Usuario, UserAudit
from .services import (
    create_admin,
    edit_admin,
    deactivate_admin,
    activate_admin,
    login_usuario
)


class UserAuditModelTest(TestCase):
    """Test UserAudit model."""

    def setUp(self):
        self.actor = Usuario.objects.create_user(
            correo='actor@example.com',
            username='actor',
            nombre='Actor User',
            password='testpass123',
            rol='superadministrador',
            estado='activo'
        )
        self.target = Usuario.objects.create_user(
            correo='target@example.com',
            username='target',
            nombre='Target User',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

    def test_create_audit_record(self):
        """Test creating an audit record."""
        audit = UserAudit.objects.create(
            actor=self.actor,
            target_user=self.target,
            action_type='create',
            details={'nombre': 'Test User', 'correo': 'test@example.com'}
        )
        self.assertEqual(audit.action_type, 'create')
        self.assertEqual(audit.actor, self.actor)
        self.assertEqual(audit.target_user, self.target)

    def test_audit_str_representation(self):
        """Test audit string representation."""
        audit = UserAudit.objects.create(
            actor=self.actor,
            target_user=self.target,
            action_type='deactivate'
        )
        self.assertIn('deactivate', str(audit))
        self.assertIn('target@example.com', str(audit))


class AdminServiceTest(TestCase):
    """Test admin service functions."""

    def setUp(self):
        self.superadmin = Usuario.objects.create_user(
            correo='superadmin@example.com',
            username='superadmin',
            nombre='Super Admin',
            password='testpass123',
            rol='superadministrador',
            estado='activo'
        )

    def test_create_admin_success(self):
        """Test successful admin creation."""
        data = {
            'nombre': 'New Admin',
            'correo': 'newadmin@example.com',
            'rol': 'administrador',
            'password': 'SecurePass123!',
            'estado': 'activo'
        }
        admin = create_admin(data, actor=self.superadmin)

        self.assertEqual(admin.nombre, 'New Admin')
        self.assertEqual(admin.correo, 'newadmin@example.com')
        self.assertEqual(admin.rol, 'administrador')
        self.assertTrue(admin.check_password('SecurePass123!'))

    def test_create_admin_duplicate_email(self):
        """Test that duplicate emails raise error."""
        Usuario.objects.create_user(
            correo='existing@example.com',
            username='existing',
            nombre='Existing User',
            password='testpass123',
            rol='administrador'
        )

        data = {
            'nombre': 'Duplicate Email',
            'correo': 'existing@example.com',
            'rol': 'administrador',
            'password': 'SecurePass123!',
            'estado': 'activo'
        }
        with self.assertRaises(ValueError) as context:
            create_admin(data, actor=self.superadmin)

        self.assertIn('ya está registrado', str(context.exception))

    def test_create_admin_audit_log(self):
        """Test that admin creation is logged in audit."""
        data = {
            'nombre': 'Audit Test',
            'correo': 'audit@example.com',
            'rol': 'administrador',
            'password': 'SecurePass123!',
            'estado': 'activo'
        }
        admin = create_admin(data, actor=self.superadmin)

        audit = UserAudit.objects.filter(target_user=admin).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action_type, 'create')
        self.assertEqual(audit.actor, self.superadmin)

    def test_edit_admin_success(self):
        """Test successful admin editing."""
        admin = Usuario.objects.create_user(
            correo='admin@example.com',
            username='admin',
            nombre='Original Name',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        updated = edit_admin(
            admin.id,
            {'nombre': 'Updated Name', 'estado': 'activo'},
            actor=self.superadmin
        )

        self.assertEqual(updated.nombre, 'Updated Name')

    def test_edit_admin_duplicate_email(self):
        """Test that duplicate emails raise error on edit."""
        Usuario.objects.create_user(
            correo='taken@example.com',
            username='taken',
            nombre='Taken',
            password='testpass123',
            rol='administrador'
        )

        admin = Usuario.objects.create_user(
            correo='admin@example.com',
            username='admin',
            nombre='Admin',
            password='testpass123',
            rol='administrador'
        )

        with self.assertRaises(ValueError) as context:
            edit_admin(admin.id, {'correo': 'taken@example.com'}, actor=self.superadmin)

        self.assertIn('ya está registrado', str(context.exception))

    def test_deactivate_admin_success(self):
        """Test successful admin deactivation."""
        admin = Usuario.objects.create_user(
            correo='active@example.com',
            username='active',
            nombre='Active Admin',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        deactivated = deactivate_admin(admin.id, actor=self.superadmin)

        self.assertEqual(deactivated.estado, 'inactivo')

    def test_deactivate_admin_audit_log(self):
        """Test that deactivation is logged."""
        admin = Usuario.objects.create_user(
            correo='admin@example.com',
            username='admin',
            nombre='Admin',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        deactivate_admin(admin.id, actor=self.superadmin)

        audit = UserAudit.objects.filter(
            target_user=admin,
            action_type='deactivate'
        ).first()

        self.assertIsNotNone(audit)

    def test_deactivate_self_raises_error(self):
        """Test that admin cannot deactivate self."""
        with self.assertRaises(ValueError) as context:
            deactivate_admin(self.superadmin.id, actor=self.superadmin)

        self.assertIn('propia', str(context.exception))

    def test_deactivate_already_inactive_raises_error(self):
        """Test that deactivating inactive user raises error."""
        admin = Usuario.objects.create_user(
            correo='inactive@example.com',
            username='inactive',
            nombre='Inactive Admin',
            password='testpass123',
            rol='administrador',
            estado='inactivo'
        )

        with self.assertRaises(ValueError) as context:
            deactivate_admin(admin.id, actor=self.superadmin)

        self.assertIn('inactivo', str(context.exception))

    def test_activate_admin_success(self):
        """Test successful admin activation."""
        admin = Usuario.objects.create_user(
            correo='inactive@example.com',
            username='inactive',
            nombre='Inactive Admin',
            password='testpass123',
            rol='administrador',
            estado='inactivo'
        )

        activated = activate_admin(admin.id, actor=self.superadmin)

        self.assertEqual(activated.estado, 'activo')

    def test_activate_already_active_raises_error(self):
        """Test that activating active user raises error."""
        admin = Usuario.objects.create_user(
            correo='active@example.com',
            username='active',
            nombre='Active Admin',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        with self.assertRaises(ValueError) as context:
            activate_admin(admin.id, actor=self.superadmin)

        self.assertIn('activo', str(context.exception))


class LoginUserTest(TestCase):
    """Test login functionality."""

    def test_login_active_user_success(self):
        """Test successful login of active user."""
        Usuario.objects.create_user(
            correo='active@example.com',
            username='active',
            nombre='Active User',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        user = login_usuario('active@example.com', 'testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user.correo, 'active@example.com')

    def test_login_inactive_user_fails(self):
        """Test that inactive users cannot login."""
        Usuario.objects.create_user(
            correo='inactive@example.com',
            username='inactive',
            nombre='Inactive User',
            password='testpass123',
            rol='administrador',
            estado='inactivo'
        )

        user = login_usuario('inactive@example.com', 'testpass123')
        self.assertIsNone(user)

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        Usuario.objects.create_user(
            correo='user@example.com',
            username='user',
            nombre='Test User',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

        user = login_usuario('user@example.com', 'wrongpassword')
        self.assertIsNone(user)


class AdminAPITest(APITestCase):
    """Test Admin API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.superadmin = Usuario.objects.create_user(
            correo='superadmin@example.com',
            username='superadmin',
            nombre='Super Admin',
            password='testpass123',
            rol='superadministrador',
            estado='activo'
        )
        self.regular_admin = Usuario.objects.create_user(
            correo='admin@example.com',
            username='admin',
            nombre='Regular Admin',
            password='testpass123',
            rol='administrador',
            estado='activo'
        )

    def test_list_admins_requires_auth(self):
        """Test that listing admins requires authentication."""
        response = self.client.get('/api/admins/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_admins_requires_superadmin(self):
        """Test that only superadmin can list admins."""
        self.client.force_authenticate(user=self.regular_admin)
        response = self.client.get('/api/admins/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_admins_success(self):
        """Test successful admin listing."""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/admins/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_admin_success(self):
        """Test successful admin creation via API."""
        self.client.force_authenticate(user=self.superadmin)

        data = {
            'nombre': 'New Admin',
            'correo': 'newadmin@example.com',
            'rol': 'administrador',
            'password': 'SecurePass123!',
            'estado': 'activo'
        }

        response = self.client.post('/api/admins/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['correo'], 'newadmin@example.com')

    def test_create_admin_duplicate_email(self):
        """Test that duplicate emails are rejected."""
        self.client.force_authenticate(user=self.superadmin)

        data = {
            'nombre': 'Duplicate',
            'correo': 'admin@example.com',
            'rol': 'administrador',
            'password': 'SecurePass123!',
            'estado': 'activo'
        }

        response = self.client.post('/api/admins/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivate_admin_success(self):
        """Test successful admin deactivation via API."""
        self.client.force_authenticate(user=self.superadmin)

        response = self.client.post(f'/api/admins/{self.regular_admin.id}/deactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('desactivado', response.data['message'])

    def test_activate_admin_success(self):
        """Test successful admin activation via API."""
        self.regular_admin.estado = 'inactivo'
        self.regular_admin.save()

        self.client.force_authenticate(user=self.superadmin)

        response = self.client.post(f'/api/admins/{self.regular_admin.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activado', response.data['message'])

    def test_update_admin_success(self):
        """Test successful admin update via API."""
        self.client.force_authenticate(user=self.superadmin)

        data = {'nombre': 'Updated Name'}
        response = self.client.patch(
            f'/api/admins/{self.regular_admin.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Updated Name')

    def test_get_audit_log(self):
        """Test getting admin audit log."""
        self.client.force_authenticate(user=self.superadmin)

        # Perform some action
        self.client.post(f'/api/admins/{self.regular_admin.id}/deactivate/')

        # Get audit log
        response = self.client.get(f'/api/admins/{self.regular_admin.id}/audit-log/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['usuario'], self.regular_admin.correo)
        self.assertGreater(len(response.data['historial']), 0)

    def test_inactive_user_cannot_access_admin_endpoints(self):
        """Test that inactive users cannot access admin endpoints."""
        self.superadmin.estado = 'inactivo'
        self.superadmin.save()

        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/admins/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)