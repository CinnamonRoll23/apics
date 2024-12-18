import uuid
from django.db import models
from django.core.exceptions import ValidationError

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def clean(self):
        """Ensures only one pending order exists for the user."""
        if Order.objects.filter(user=self, status='Pending').exists():
            raise ValidationError("User already has a pending order.")

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processed', 'Processed'),
        ('Cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Prevents updating an order to pending if one already exists."""
        if self.status == 'Pending':
            if Order.objects.filter(user=self.user, status='Pending').exclude(pk=self.pk).exists():
                raise ValidationError("User can only have one pending order.")

    def __str__(self):
        return f"Order {self.id} ({self.status})"

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cart_items')
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        """Validates quantity and price."""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"

