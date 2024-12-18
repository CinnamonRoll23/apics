from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Order, CartItem
from .serializers import UserSerializer, OrderSerializer, CartItemSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for User.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

class OrderViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Orders.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """
        Custom action for order checkout.
        """
        try:
            order = self.get_object()
            if order.status != 'Pending':
                return Response({"error": "Only pending orders can be checked out."}, status=status.HTTP_400_BAD_REQUEST)
            
            cart_items = order.cart_items.all()
            if not cart_items.exists():
                return Response({"error": "No cart items found for this order."}, status=status.HTTP_400_BAD_REQUEST)


            order.status = 'Processed'
            order.save()
            return Response({"message": "Order successfully checked out."}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

class CartItemViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Cart Items.
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def get_queryset(self):
        """
        Optionally filter by order status = Pending.
        """
        order_id = self.request.query_params.get('order_id', None)
        if order_id:
            return CartItem.objects.filter(order__id=order_id, order__status='Pending')
        return super().get_queryset()

class OrderListView(APIView):
    """
    get:
    Retrieve a list of all orders.

    post:
    Create a new order.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Retrieve all orders for the authenticated user
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Create a new order for the authenticated user
        data = request.data
        data['user'] = request.user.id  # Attach the authenticated user to the order
        serializer = OrderSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    """
    post:
    Log in a user with their credentials.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user_id": user.id,
                "username": user.username
            }, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class CheckoutView(APIView):
    def post(self, request):
        order_id = request.data.get("orderID")
        
        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(orderID=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if order.status == "PROCESSED":
            return Response({"error": "Order is already processed"}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = "PROCESSED"
        order.save()

        return Response(
            {"message": f"Order {order_id} processed successfully", "status": order.status},
            status=status.HTTP_200_OK
        )