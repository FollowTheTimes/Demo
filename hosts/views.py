from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import City, Datacenter, Host
from .serializers import CitySerializer, DatacenterSerializer, HostSerializer, HostDetailSerializer
import subprocess

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class DatacenterViewSet(viewsets.ModelViewSet):
    queryset = Datacenter.objects.all()
    serializer_class = DatacenterSerializer

class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'create' or self.action == 'update':
            return HostDetailSerializer
        return HostSerializer
    
    @action(detail=True, methods=['get'])
    def ping(self, request, pk=None):
        """探测主机是否 ping 可达"""
        host = self.get_object()
        ip_address = host.ip_address
        
        # 使用 subprocess 执行 ping 命令
        try:
            # 发送 3 个 ping 包，超时 2 秒
            output = subprocess.run(
                ['ping', '-c', '3', '-W', '2', ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 检查返回码，0 表示成功
            if output.returncode == 0:
                return Response({'status': 'reachable', 'ip': ip_address}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'unreachable', 'ip': ip_address}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
