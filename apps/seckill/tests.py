from django.test import TestCase
from django.utils import timezone
from apps.seckill.models import Product, SeckillActivity, Order
from apps.users.models import User
import json

class SeckillTests(TestCase):
    """秒杀功能测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123456'
        )
        
        # 创建测试商品
        self.product = Product.objects.create(
            name='测试商品',
            original_price=1000.00,
            seckill_price=699.00,
            stock=10
        )
        
        # 创建测试秒杀活动
        self.activity = SeckillActivity.objects.create(
            product=self.product,
            start_time=timezone.now() - timezone.timedelta(days=1),
            end_time=timezone.now() + timezone.timedelta(days=1),
            status='active'
        )
        
        # 更新商品的秒杀价格
        self.product.seckill_price = 699.00
        self.product.save()
    
    def test_create_activity(self):
        """测试创建秒杀活动"""
        # 测试创建活动的API
        response = self.client.post('/api/create_activity/', {
            'product_id': self.product.id,
            'seckill_price': '699.00',
            'start_time': (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            'end_time': (timezone.now() + timezone.timedelta(days=1)).isoformat()
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertIn('activity_id', data)
    
    def test_seckill(self):
        """测试秒杀功能"""
        # 测试秒杀API
        response = self.client.post('/api/seckill/', {
            'user_id': self.user.id,
            'activity_id': self.activity.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertIn('秒杀成功', data['message'])
    
    def test_order_status(self):
        """测试订单状态查询"""
        # 先创建一个订单
        order = Order.objects.create(
            user=self.user,
            activity=self.activity,
            status='pending'
        )
        
        # 测试订单状态查询API
        response = self.client.get(f'/api/order/status/?order_id={order.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['data']['order_id'], order.id)
        self.assertEqual(data['data']['status'], 'pending')
    
    def test_seckill_price_validation(self):
        """测试秒杀价格验证"""
        # 测试秒杀价格不足300元优惠的情况
        response = self.client.post('/api/create_activity/', {
            'product_id': self.product.id,
            'seckill_price': '900.00',  # 只优惠100元，不足300元
            'start_time': (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            'end_time': (timezone.now() + timezone.timedelta(days=1)).isoformat()
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 400)
        self.assertIn('秒杀价优惠太低', data['message'])
    
    def test_activity_time_validation(self):
        """测试活动时间验证"""
        # 测试开始时间晚于结束时间的情况
        response = self.client.post('/api/create_activity/', {
            'product_id': self.product.id,
            'seckill_price': '699.00',
            'start_time': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'end_time': (timezone.now() - timezone.timedelta(days=1)).isoformat()
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 400)
        self.assertIn('开始时间不能晚于结束时间', data['message'])

class ProductTests(TestCase):
    """商品模型测试"""
    
    def test_product_creation(self):
        """测试商品创建"""
        product = Product.objects.create(
            name='测试商品',
            original_price=1000.00,
            seckill_price=699.00,
            stock=10
        )
        
        self.assertEqual(product.name, '测试商品')
        self.assertEqual(product.original_price, 1000.00)
        self.assertEqual(product.seckill_price, 699.00)
        self.assertEqual(product.stock, 10)

class UserTests(TestCase):
    """用户模型测试"""
    
    def test_user_creation(self):
        """测试用户创建"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='test123456',
            first_name='测试',
            last_name='用户'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, '测试')
        self.assertEqual(user.last_name, '用户')
        self.assertTrue(user.check_password('test123456'))
