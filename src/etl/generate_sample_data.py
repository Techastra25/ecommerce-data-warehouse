"""
generate_sample_data.py
------------------------
Simulates raw e-commerce order data (orders, order_items, customers, products)
as CSV extracts, the entry point for building a dimensional warehouse.

Run:
    python src/etl/generate_sample_data.py --orders 50000
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

CATEGORIES = ["Electronics", "Books", "Apparel", "Home & Kitchen", "Toys", "Sports"]
CITIES = [
    ("Mumbai", "Maharashtra"), ("Delhi", "Delhi"), ("Bengaluru", "Karnataka"),
    ("Hyderabad", "Telangana"), ("Chennai", "Tamil Nadu"), ("Pune", "Maharashtra"),
]


def generate_customers(n):
    path = os.path.join(RAW_DIR, "customers")
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "customers.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "signup_date", "city", "state", "email"])
        for i in range(1, n + 1):
            city, state = random.choice(CITIES)
            signup = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 800))
            w.writerow([f"CUST{i:06d}", signup.strftime("%Y-%m-%d"), city, state, f"user{i}@example.com"])
    print(f"Generated {n} customers")
    return n


def generate_products(n):
    path = os.path.join(RAW_DIR, "products")
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "products.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "product_name", "category", "list_price", "cost_price"])
        for i in range(1, n + 1):
            cat = random.choice(CATEGORIES)
            list_price = round(random.uniform(10, 800), 2)
            cost_price = round(list_price * random.uniform(0.4, 0.7), 2)
            w.writerow([f"PROD{i:05d}", f"{cat} Item {i}", cat, list_price, cost_price])
    print(f"Generated {n} products")
    return n


def generate_orders(n_orders, n_customers, n_products):
    orders_path = os.path.join(RAW_DIR, "orders")
    items_path = os.path.join(RAW_DIR, "order_items")
    os.makedirs(orders_path, exist_ok=True)
    os.makedirs(items_path, exist_ok=True)

    start = datetime(2024, 1, 1)
    statuses = ["DELIVERED", "DELIVERED", "DELIVERED", "CANCELLED", "RETURNED", "PENDING"]

    with open(os.path.join(orders_path, "orders.csv"), "w", newline="") as fo, \
         open(os.path.join(items_path, "order_items.csv"), "w", newline="") as fi:

        ow = csv.writer(fo)
        iw = csv.writer(fi)
        ow.writerow(["order_id", "customer_id", "order_date", "status", "shipping_city"])
        iw.writerow(["order_item_id", "order_id", "product_id", "quantity", "unit_price"])

        item_counter = 1
        for i in range(1, n_orders + 1):
            order_id = f"ORD{i:07d}"
            customer_id = f"CUST{random.randint(1, n_customers):06d}" if random.random() > 0.03 else ""  # ~3% missing
            order_date = start + timedelta(days=random.randint(0, 540), hours=random.randint(0, 23))
            status = random.choice(statuses)
            city, _ = random.choice(CITIES)

            ow.writerow([order_id, customer_id, order_date.strftime("%Y-%m-%d %H:%M:%S"), status, city])

            # 1-5 line items per order
            for _ in range(random.randint(1, 5)):
                product_id = f"PROD{random.randint(1, n_products):05d}"
                qty = random.randint(1, 4)
                unit_price = round(random.uniform(10, 800), 2)
                iw.writerow([f"ITEM{item_counter:08d}", order_id, product_id, qty, unit_price])
                item_counter += 1

    print(f"Generated {n_orders} orders with line items -> {orders_path}, {items_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=50000)
    parser.add_argument("--customers", type=int, default=8000)
    parser.add_argument("--products", type=int, default=1500)
    args = parser.parse_args()

    generate_customers(args.customers)
    generate_products(args.products)
    generate_orders(args.orders, args.customers, args.products)
