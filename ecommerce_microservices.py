"""
E-Commerce Microservices Architecture - Single Python File
===========================================================

Educational GitHub-ready prototype for Week 1 architecture assignment.

This single file simulates these microservices:
1. Auth/User Service
2. Product Service
3. Cart Service
4. Order Service
5. Payment Service
6. API Gateway

Run:
    python ecommerce_microservices.py

Optional FastAPI API:
    pip install fastapi uvicorn
    uvicorn ecommerce_microservices:app --reload

The in-memory data is for demonstration only.
A production system should use databases, authentication,
Redis, Kafka, secure payment-provider integration, etc.
"""

from typing import Dict, List, Optional
from uuid import uuid4

# -------------------------------------------------------------------
# DATA MODELS
# -------------------------------------------------------------------

class User:
    def __init__(self, user_id: int, name: str, email: str):
        self.id = user_id
        self.name = name
        self.email = email

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }


class Product:
    def __init__(
        self,
        product_id: int,
        name: str,
        price: float,
        category: str,
        stock: int
    ):
        self.id = product_id
        self.name = name
        self.price = price
        self.category = category
        self.stock = stock

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "stock": self.stock
        }


# -------------------------------------------------------------------
# AUTH / USER SERVICE
# -------------------------------------------------------------------

class AuthService:
    """Handles user registration and user lookup."""

    def __init__(self):
        self.users: Dict[int, User] = {}
        self.next_user_id = 1

    def register(self, name: str, email: str):
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return {
                    "success": False,
                    "message": "Email already registered"
                }

        user = User(
            self.next_user_id,
            name,
            email
        )

        self.users[self.next_user_id] = user
        self.next_user_id += 1

        return {
            "success": True,
            "message": "User registered successfully",
            "user": user.to_dict()
        }

    def get_user(self, user_id: int):
        user = self.users.get(user_id)

        if user is None:
            return None

        return user.to_dict()

    def list_users(self):
        return [user.to_dict() for user in self.users.values()]


# -------------------------------------------------------------------
# PRODUCT SERVICE
# -------------------------------------------------------------------

class ProductService:
    """Handles product catalog operations."""

    def __init__(self):
        self.products: Dict[int, Product] = {
            1: Product(
                1,
                "Laptop",
                65000,
                "Electronics",
                10
            ),
            2: Product(
                2,
                "Headphones",
                2500,
                "Electronics",
                25
            ),
            3: Product(
                3,
                "Keyboard",
                1500,
                "Accessories",
                30
            ),
            4: Product(
                4,
                "Mouse",
                800,
                "Accessories",
                40
            )
        }

    def list_products(self):
        return [
            product.to_dict()
            for product in self.products.values()
        ]

    def get_product(self, product_id: int):
        product = self.products.get(product_id)

        if product is None:
            return None

        return product.to_dict()

    def reduce_stock(self, product_id: int, quantity: int):
        product = self.products.get(product_id)

        if product is None:
            return False, "Product not found"

        if quantity <= 0:
            return False, "Quantity must be greater than zero"

        if product.stock < quantity:
            return False, "Insufficient stock"

        product.stock -= quantity

        return True, "Stock updated"


# -------------------------------------------------------------------
# CART SERVICE
# -------------------------------------------------------------------

class CartService:
    """Handles shopping carts for users."""

    def __init__(self):
        self.carts: Dict[int, List[dict]] = {}

    def add_to_cart(
        self,
        user_id: int,
        product_id: int,
        quantity: int
    ):
        if quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than zero"
            }

        if user_id not in self.carts:
            self.carts[user_id] = []

        for item in self.carts[user_id]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity

                return {
                    "success": True,
                    "message": "Product quantity updated",
                    "cart": self.carts[user_id]
                }

        self.carts[user_id].append({
            "product_id": product_id,
            "quantity": quantity
        })

        return {
            "success": True,
            "message": "Product added to cart",
            "cart": self.carts[user_id]
        }

    def get_cart(self, user_id: int):
        return self.carts.get(user_id, [])

    def clear_cart(self, user_id: int):
        self.carts[user_id] = []


# -------------------------------------------------------------------
# PAYMENT SERVICE
# -------------------------------------------------------------------

class PaymentService:
    """Simulates an external payment provider."""

    def __init__(self):
        self.payments = {}

    def process_payment(self, order_id: str, amount: float):
        payment_id = str(uuid4())

        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "status": "SUCCESS"
        }

        self.payments[payment_id] = payment

        return payment


# -------------------------------------------------------------------
# ORDER SERVICE
# -------------------------------------------------------------------

class OrderService:
    """Creates and manages customer orders."""

    def __init__(
        self,
        product_service: ProductService,
        cart_service: CartService,
        payment_service: PaymentService
    ):
        self.orders = {}
        self.product_service = product_service
        self.cart_service = cart_service
        self.payment_service = payment_service

    def create_order(self, user_id: int):
        cart = self.cart_service.get_cart(user_id)

        if not cart:
            return {
                "success": False,
                "message": "Cart is empty"
            }

        order_id = str(uuid4())
        order_items = []
        total_price = 0

        # Validate all cart items before changing stock.
        for item in cart:
            product = self.product_service.get_product(
                item["product_id"]
            )

            if product is None:
                return {
                    "success": False,
                    "message": (
                        f"Product {item['product_id']} "
                        "does not exist"
                    )
                }

            if product["stock"] < item["quantity"]:
                return {
                    "success": False,
                    "message": (
                        f"Insufficient stock for "
                        f"{product['name']}"
                    )
                }

            item_total = (
                product["price"] * item["quantity"]
            )

            order_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "quantity": item["quantity"],
                "unit_price": product["price"],
                "total": item_total
            })

            total_price += item_total

        # Reduce inventory after successful validation.
        for item in cart:
            self.product_service.reduce_stock(
                item["product_id"],
                item["quantity"]
            )

        order = {
            "order_id": order_id,
            "user_id": user_id,
            "items": order_items,
            "total_price": total_price,
            "status": "PAYMENT_PENDING"
        }

        self.orders[order_id] = order

        # Process payment.
        payment = self.payment_service.process_payment(
            order_id,
            total_price
        )

        if payment["status"] == "SUCCESS":
            order["status"] = "CONFIRMED"
        else:
            order["status"] = "PAYMENT_FAILED"

        self.cart_service.clear_cart(user_id)

        return {
            "success": True,
            "order": order,
            "payment": payment
        }

    def get_order(self, order_id: str):
        return self.orders.get(order_id)

    def get_user_orders(self, user_id: int):
        return [
            order
            for order in self.orders.values()
            if order["user_id"] == user_id
        ]


# -------------------------------------------------------------------
# API GATEWAY
# -------------------------------------------------------------------

class APIGateway:
    """
    Simulates an API Gateway.

    In a real microservices system, the gateway would route
    HTTP requests to independently deployed services.
    """

    def __init__(
        self,
        auth_service: AuthService,
        product_service: ProductService,
        cart_service: CartService,
        order_service: OrderService
    ):
        self.auth_service = auth_service
        self.product_service = product_service
        self.cart_service = cart_service
        self.order_service = order_service

    def register_user(self, name: str, email: str):
        return self.auth_service.register(name, email)

    def products(self):
        return self.product_service.list_products()

    def add_to_cart(
        self,
        user_id: int,
        product_id: int,
        quantity: int
    ):
        user = self.auth_service.get_user(user_id)

        if user is None:
            return {
                "success": False,
                "message": "User not found"
            }

        product = self.product_service.get_product(product_id)

        if product is None:
            return {
                "success": False,
                "message": "Product not found"
            }

        if product["stock"] < quantity:
            return {
                "success": False,
                "message": "Insufficient stock"
            }

        return self.cart_service.add_to_cart(
            user_id,
            product_id,
            quantity
        )

    def get_cart(self, user_id: int):
        return self.cart_service.get_cart(user_id)

    def checkout(self, user_id: int):
        return self.order_service.create_order(user_id)

    def get_orders(self, user_id: int):
        return self.order_service.get_user_orders(user_id)


# -------------------------------------------------------------------
# CREATE SERVICES
# -------------------------------------------------------------------

auth_service = AuthService()
product_service = ProductService()
cart_service = CartService()
payment_service = PaymentService()

order_service = OrderService(
    product_service,
    cart_service,
    payment_service
)

api_gateway = APIGateway(
    auth_service,
    product_service,
    cart_service,
    order_service
)


# -------------------------------------------------------------------
# DISPLAY FUNCTIONS
# -------------------------------------------------------------------

def display_products():
    print("\n========== PRODUCT LIST ==========")

    products = api_gateway.products()

    for product in products:
        print(
            f"ID: {product['id']} | "
            f"{product['name']} | "
            f"₹{product['price']:.2f} | "
            f"{product['category']} | "
            f"Stock: {product['stock']}"
        )


def display_cart(user_id: int):
    print("\n========== SHOPPING CART ==========")

    cart = api_gateway.get_cart(user_id)

    if not cart:
        print("Cart is empty.")
        return

    for item in cart:
        product = product_service.get_product(
            item["product_id"]
        )

        if product:
            total = (
                product["price"] *
                item["quantity"]
            )

            print(
                f"{product['name']} | "
                f"Quantity: {item['quantity']} | "
                f"Total: ₹{total:.2f}"
            )


def display_orders(user_id: int):
    print("\n========== ORDERS ==========")

    orders = api_gateway.get_orders(user_id)

    if not orders:
        print("No orders found.")
        return

    for order in orders:
        print(
            f"Order ID: {order['order_id']} | "
            f"Amount: ₹{order['total_price']:.2f} | "
            f"Status: {order['status']}"
        )


# -------------------------------------------------------------------
# INTERACTIVE CLI
# -------------------------------------------------------------------

def run_cli():
    current_user: Optional[dict] = None

    while True:
        print("\n")
        print("==========================================")
        print("     E-COMMERCE MICROSERVICES SYSTEM")
        print("==========================================")

        if current_user:
            print(
                f"Logged in user: "
                f"{current_user['name']}"
            )

        print("\n1. Register User")
        print("2. Show Products")
        print("3. Add Product to Cart")
        print("4. Show Cart")
        print("5. Checkout")
        print("6. Show Orders")
        print("7. Show Users")
        print("8. Exit")

        choice = input("\nEnter your choice: ").strip()

        # -----------------------------------------------------------
        # Register
        # -----------------------------------------------------------

        if choice == "1":
            name = input("Enter your name: ").strip()
            email = input("Enter your email: ").strip()

            result = api_gateway.register_user(
                name,
                email
            )

            print("\n", result["message"])

            if result["success"]:
                current_user = result["user"]
                print(
                    f"Welcome, {current_user['name']}!"
                )

        # -----------------------------------------------------------
        # Products
        # -----------------------------------------------------------

        elif choice == "2":
            display_products()

        # -----------------------------------------------------------
        # Add to cart
        # -----------------------------------------------------------

        elif choice == "3":

            if current_user is None:
                print(
                    "\nPlease register a user first."
                )
                continue

            display_products()

            try:
                product_id = int(
                    input(
                        "\nEnter product ID: "
                    )
                )

                quantity = int(
                    input(
                        "Enter quantity: "
                    )
                )

                result = api_gateway.add_to_cart(
                    current_user["id"],
                    product_id,
                    quantity
                )

                print("\n", result["message"])

            except ValueError:
                print(
                    "\nPlease enter valid numbers."
                )

        # -----------------------------------------------------------
        # Cart
        # -----------------------------------------------------------

        elif choice == "4":

            if current_user is None:
                print(
                    "\nPlease register a user first."
                )
                continue

            display_cart(current_user["id"])

        # -----------------------------------------------------------
        # Checkout
        # -----------------------------------------------------------

        elif choice == "5":

            if current_user is None:
                print(
                    "\nPlease register a user first."
                )
                continue

            result = api_gateway.checkout(
                current_user["id"]
            )

            print("\n========== CHECKOUT ==========")

            if not result["success"]:
                print(result["message"])
                continue

            order = result["order"]
            payment = result["payment"]

            print(
                f"Order ID: {order['order_id']}"
            )

            print(
                f"Total: ₹"
                f"{order['total_price']:.2f}"
            )

            print(
                f"Order Status: "
                f"{order['status']}"
            )

            print(
                f"Payment Status: "
                f"{payment['status']}"
            )

            print(
                "\nOrder placed successfully!"
            )

        # -----------------------------------------------------------
        # Orders
        # -----------------------------------------------------------

        elif choice == "6":

            if current_user is None:
                print(
                    "\nPlease register a user first."
                )
                continue

            display_orders(current_user["id"])

        # -----------------------------------------------------------
        # Users
        # -----------------------------------------------------------

        elif choice == "7":

            print("\n========== USERS ==========")

            users = auth_service.list_users()

            if not users:
                print("No users registered.")
            else:
                for user in users:
                    print(
                        f"ID: {user['id']} | "
                        f"{user['name']} | "
                        f"{user['email']}"
                    )

        # -----------------------------------------------------------
        # Exit
        # -----------------------------------------------------------

        elif choice == "8":
            print(
                "\nThank you for using the "
                "E-Commerce Microservices System."
            )
            break

        else:
            print(
                "\nInvalid choice. "
                "Please select 1-8."
            )


# -------------------------------------------------------------------
# OPTIONAL FASTAPI API
# -------------------------------------------------------------------
#
# This section is optional. The CLI works without FastAPI.
#
# To use the API:
#
#     pip install fastapi uvicorn
#     uvicorn ecommerce_microservices:app --reload
#
# Then open:
#
#     http://127.0.0.1:8000/docs
#

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(
        title="E-Commerce Microservices API",
        description=(
            "Educational single-file implementation "
            "of an e-commerce microservices architecture."
        ),
        version="1.0.0"
    )

    class RegisterRequest(BaseModel):
        name: str
        email: str

    class CartRequest(BaseModel):
        user_id: int
        product_id: int
        quantity: int

    @app.get("/health")
    def health():
        return {
            "status": "running",
            "architecture": "microservices",
            "implementation": "single Python file"
        }

    @app.post("/users/register")
    def register_user(request: RegisterRequest):
        return api_gateway.register_user(
            request.name,
            request.email
        )

    @app.get("/products")
    def get_products():
        return api_gateway.products()

    @app.get("/products/{product_id}")
    def get_product(product_id: int):
        product = product_service.get_product(product_id)

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return product

    @app.post("/cart/add")
    def add_to_cart(request: CartRequest):
        return api_gateway.add_to_cart(
            request.user_id,
            request.product_id,
            request.quantity
        )

    @app.get("/cart/{user_id}")
    def get_cart(user_id: int):
        return api_gateway.get_cart(user_id)

    @app.post("/checkout/{user_id}")
    def checkout(user_id: int):
        return api_gateway.checkout(user_id)

    @app.get("/orders/{user_id}")
    def get_orders(user_id: int):
        return api_gateway.get_orders(user_id)

except ImportError:
    # FastAPI is optional for the CLI version.
    app = None


# -------------------------------------------------------------------
# PROGRAM ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":
    run_cli()
