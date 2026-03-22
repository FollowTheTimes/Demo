from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class UserTests(TestCase):
    """用户相关测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123456',
            first_name='测试',
            last_name='用户'
        )
        
        # 创建超级用户
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
    
    def test_user_creation(self):
        """测试用户创建"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='new123456'
        )
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_superuser_creation(self):
        """测试超级用户创建"""
        superuser = User.objects.create_superuser(
            username='newadmin',
            email='newadmin@example.com',
            password='newadmin123'
        )
        
        self.assertEqual(superuser.username, 'newadmin')
        self.assertEqual(superuser.email, 'newadmin@example.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_user_authentication(self):
        """测试用户认证"""
        # 测试正确的密码
        self.assertTrue(self.client.login(username='testuser', password='test123456'))
        
        # 测试错误的密码
        self.assertFalse(self.client.login(username='testuser', password='wrongpassword'))
        
        # 测试不存在的用户
        self.assertFalse(self.client.login(username='nonexistent', password='test123456'))
    
    def test_user_str_method(self):
        """测试用户的 __str__ 方法"""
        # 测试有中文名字的用户
        self.assertEqual(str(self.user), '测试')
        
        # 测试没有中文名字的用户
        user_without_name = User.objects.create_user(
            username='nonymous',
            email='nonymous@example.com',
            password='test123456'
        )
        self.assertEqual(str(user_without_name), 'nonymous')
    
    def test_user_profile_view(self):
        """测试用户个人资料视图"""
        # 登录用户
        self.client.login(username='testuser', password='test123456')
        
        # 访问个人资料页面
        response = self.client.get(reverse('users:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'test@example.com')
    
    def test_login_attempt_limit_middleware(self):
        """测试登录尝试限制中间件"""
        # 尝试多次错误登录
        for i in range(5):
            response = self.client.post('/admin/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # 第6次尝试应该被限制
        response = self.client.post('/admin/login/', {
            'username': 'testuser',
            'password': 'test123456'
        })
        
        # 检查是否被限制
        self.assertContains(response, '登录尝试次数过多')
