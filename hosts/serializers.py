from rest_framework import serializers
from .models import City, Datacenter, Host, HostCount

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class DatacenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datacenter
        fields = '__all__'

class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ['id', 'hostname', 'ip_address', 'datacenter', 'is_active', 'created_at', 'updated_at']

class HostDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ['id', 'hostname', 'ip_address', 'datacenter', 'root_password', 'is_active', 'created_at', 'updated_at']

class HostCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostCount
        fields = '__all__'
