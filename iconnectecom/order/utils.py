# utils.py
import uuid
from django.conf import settings

def generate_order_number(prefix="ORD"):
    unique_id = str(uuid.uuid4().int)[:6]  # Get the first 6 digits of the UUID
    return f"{prefix}{unique_id}"

