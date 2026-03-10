from fastapi import FastAPI

app = FastAPI()

# Products data
products = [
    {"id":1,"name":"Wireless Mouse","price":599,"category":"Electronics","in_stock":True},
    {"id":2,"name":"Notebook","price":120,"category":"Stationery","in_stock":True},
    {"id":3,"name":"Pen Set","price":49,"category":"Stationery","in_stock":True},
    {"id":4,"name":"Laptop Bag","price":999,"category":"Electronics","in_stock":False},
    {"id":5,"name":"Laptop Stand","price":1299,"category":"Electronics","in_stock":True},
    {"id":6,"name":"Mechanical Keyboard","price":2499,"category":"Electronics","in_stock":True},
    {"id":7,"name":"Webcam","price":1899,"category":"Electronics","in_stock":False}
]

# Home endpoint
@app.get("/")
def home():
    return {"message": "Welcome to My Store API"}

# Q1 - Show all products
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }

# Q2 - Filter products by category
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):

    result = [p for p in products if p["category"] == category_name]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }

# Q3 - Show only in-stock products
@app.get("/products/instock")
def get_instock():

    available = [p for p in products if p["in_stock"] == True]

    return {
        "in_stock_products": available,
        "count": len(available)
    }

# Q4 - Store summary
@app.get("/store/summary")
def store_summary():

    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories
    }

# Q5 - Search products
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }

# Bonus - Cheapest and most expensive product
@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }
from fastapi import Query

@app.get("/products/filter")
def filter_products(min_price: int = Query(None)):

    result = products

    if min_price:
        result = [p for p in products if p["price"] >= min_price]

    return {
        "min_price": min_price,
        "products": result
    }

from fastapi import Query
from pydantic import BaseModel
from typing import Optional

# Filter products by price
@app.get("/products/filter")
def filter_products(
    min_price: int = Query(None),
    max_price: int = Query(None)
):

    result = products

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    return result


# Get only price of a product
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


# Feedback model
class CustomerFeedback(BaseModel):
    customer_name: str
    product_id: int
    rating: int
    comment: Optional[str] = None


feedback = []

# Feedback endpoint
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }
@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set([p["category"] for p in products]))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }
from pydantic import BaseModel, Field
from typing import List

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }
# Order model
from pydantic import BaseModel

class Order(BaseModel):
    product_id: int
    quantity: int


orders = []


# Create order (status starts as pending)
@app.post("/orders")
def place_order(order: Order):

    order_data = {
        "order_id": len(orders) + 1,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(order_data)

    return {
        "message": "Order placed successfully",
        "order": order_data
    }


# Get order by ID
@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}


# Confirm order
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}
