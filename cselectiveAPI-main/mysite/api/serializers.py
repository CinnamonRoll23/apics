from rest_framework import serializers
from .models import User, Order, CartItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'address', 'phone_number']
        read_only_fields = ['id']

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'order', 'product_name', 'quantity', 'price']
        read_only_fields = ['id']

    def validate_quantity(self, value):
        """Ensure quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)  # Nested representation
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'created_at', 'updated_at', 'cart_items']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Ensure a user can only have one pending order."""
        if data.get('status') == 'Pending':
            user = data.get('user')
            if user and Order.objects.filter(user=user, status='Pending').exclude(id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError("This user already has a pending order.")
        return data
