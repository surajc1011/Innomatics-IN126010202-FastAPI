from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ------------------ DATA ------------------

menu = [
    {"id": 1, "name": "Pizza", "price": 299, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Burger", "price": 149, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Pasta", "price": 199, "category": "Pizza", "is_available": False},
    {"id": 4, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 5, "name": "Ice Cream", "price": 120, "category": "Dessert", "is_available": True},
    {"id": 6, "name": "Sandwich", "price": 99, "category": "Burger", "is_available": True},
]

orders = []
order_counter = 1

cart = []

# ------------------ HELPERS ------------------

def find_menu_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type="delivery"):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

# ------------------ MODELS ------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)
    delivery_address: str = Field(min_length=5)
    order_type: str = "delivery"

class NewMenuItem(BaseModel):
    name: str = Field(min_length=2)
    price: int = Field(gt=0)
    category: str = Field(min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# ------------------ DAY 1 ------------------

@app.get("/")
def home():
    return {"message": "Welcome to Food Delivery App"}

@app.get("/menu")
def get_menu():
    return {"total": len(menu), "items": menu}

@app.get("/menu/summary")
def menu_summary():
    available = [i for i in menu if i["is_available"]]
    unavailable = [i for i in menu if not i["is_available"]]
    categories = list(set(i["category"] for i in menu))

    return {
        "total": len(menu),
        "available": len(available),
        "unavailable": len(unavailable),
        "categories": categories
    }

@app.get("/menu/filter")
def filter_menu(category: Optional[str] = None,
                max_price: Optional[int] = None,
                is_available: Optional[bool] = None):

    result = menu

    if category is not None:
        result = [i for i in result if i["category"] == category]

    if max_price is not None:
        result = [i for i in result if i["price"] <= max_price]

    if is_available is not None:
        result = [i for i in result if i["is_available"] == is_available]

    return {"count": len(result), "items": result}


# ------------------ DAY 2 & 3 ------------------

@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    item = find_menu_item(order.item_id)
    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    total = calculate_bill(item["price"], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item": item["name"],
        "quantity": order.quantity,
        "total_price": total
    }

    orders.append(new_order)
    order_counter += 1

    return new_order


# ------------------ DAY 4 ------------------

@app.post("/menu")
def add_item(item: NewMenuItem, response: Response):
    for i in menu:
        if i["name"].lower() == item.name.lower():
            return {"error": "Item already exists"}

    new_item = item.dict()
    new_item["id"] = len(menu) + 1
    menu.append(new_item)

    response.status_code = 201
    return new_item



@app.delete("/menu/{item_id}")
def delete_item(item_id: int):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    menu.remove(item)
    return {"message": "Deleted", "item": item["name"]}

# ------------------ DAY 5 ------------------

@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Updated cart", "cart": cart}

    cart.append({"item_id": item_id, "name": item["name"], "quantity": quantity})
    return {"message": "Added to cart", "cart": cart}

@app.get("/cart")
def get_cart():
    total = 0
    for c in cart:
        item = find_menu_item(c["item_id"])
        total += item["price"] * c["quantity"]

    return {"cart": cart, "grand_total": total}

@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):
    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Removed"}

    return {"error": "Item not in cart"}

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest, response: Response):
    global order_counter

    if not cart:
        return {"error": "Cart empty"}

    placed = []
    total = 0

    for c in cart:
        item = find_menu_item(c["item_id"])
        price = item["price"] * c["quantity"]

        order = {
            "order_id": order_counter,
            "customer": data.customer_name,
            "item": item["name"],
            "quantity": c["quantity"],
            "total_price": price
        }

        orders.append(order)
        placed.append(order)
        total += price
        order_counter += 1

    cart.clear()
    response.status_code = 201

    return {"orders": placed, "grand_total": total}

# ------------------ DAY 6 ------------------

@app.get("/menu/search")
def search_menu(keyword: str):
    result = [i for i in menu if keyword.lower() in i["name"].lower()
              or keyword.lower() in i["category"].lower()]

    if not result:
        return {"message": "No items found"}

    return {"total_found": len(result), "items": result}

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}

    reverse = True if order == "desc" else False

    return sorted(menu, key=lambda x: x[sort_by], reverse=reverse)

@app.get("/menu/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    data = menu[start:start + limit]

    return {
        "page": page,
        "limit": limit,
        "total": len(menu),
        "items": data
    }

@app.get("/menu/browse")
def browse_menu(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    data = menu

    # 🔹 FILTER (search)
    if keyword:
        data = [
            i for i in data
            if keyword.lower() in i["name"].lower()
            or keyword.lower() in i["category"].lower()
        ]

    # 🔹 SORT
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}

    reverse = True if order == "desc" else False
    data = sorted(data, key=lambda x: x[sort_by], reverse=reverse)

    # 🔹 PAGINATION
    total = len(data)
    start = (page - 1) * limit
    paginated = data[start:start + limit]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": paginated
    }
@app.get("/menu/{item_id}")
def get_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    return item

@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}


@app.get("/orders/search")
def search_orders(customer_name: str):
    result = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"results": result}

@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    reverse = True if order == "desc" else False
    return sorted(orders, key=lambda x: x["total_price"], reverse=reverse)
