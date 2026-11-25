"""Mock in-memory data for Binghomestay."""
from datetime import date

ROOMS = {
    "Garden Room": {"price_per_night": 65, "capacity": 2,
                    "amenities": ["Queen bed", "Garden view", "Private bathroom", "Air conditioning"]},
    "Family Suite": {"price_per_night": 120, "capacity": 5,
                     "amenities": ["2 bedrooms", "Kitchenette", "Private bathroom", "Balcony", "Air conditioning"]},
    "Cozy Single": {"price_per_night": 40, "capacity": 1,
                    "amenities": ["Single bed", "Shared bathroom", "Desk", "Fan"]},
    "Deluxe Loft": {"price_per_night": 150, "capacity": 3,
                    "amenities": ["King bed", "Sofa bed", "Rooftop access", "Private bathroom", "Mini fridge"]},
}

# Existing reservations: (room, check_in, check_out) -- check_out exclusive
RESERVATIONS = [
    ("Garden Room", date(2026, 12, 20), date(2026, 12, 27)),
    ("Family Suite", date(2026, 12, 24), date(2027, 1, 2)),
    ("Deluxe Loft", date(2026, 12, 1), date(2026, 12, 5)),
]

POLICIES = {
    "check-in/out times": "Check-in is from 2:00 PM to 9:00 PM. Check-out is by 11:00 AM. Early check-in or late check-out may be arranged on request, subject to availability.",
    "cancellation": "Free cancellation up to 7 days before check-in. Within 7 days, the first night is charged. No-shows are charged in full.",
    "house rules": "Quiet hours 10:00 PM - 7:00 AM. No smoking indoors. No parties or events. Pets are allowed only with prior approval. Please remove shoes indoors.",
    "wifi": "Free fibre WiFi throughout the property. Network: Binghomestay-Guest. The password is shown on the card in your room.",
    "payments": "We accept credit/debit cards, bank transfer and cash on arrival. A 30% deposit secures your booking; the balance is due at check-in.",
}

BOOKINGS = {
    "BH1001": {"guest": "Alice Tan", "room": "Garden Room", "check_in": "2026-12-20", "check_out": "2026-12-27", "status": "confirmed", "total": 455},
    "BH1002": {"guest": "Ben Lee", "room": "Family Suite", "check_in": "2026-12-24", "check_out": "2027-01-02", "status": "confirmed", "total": 1080},
    "BH1003": {"guest": "Chloe Wong", "room": "Cozy Single", "check_in": "2026-11-30", "check_out": "2026-12-02", "status": "cancelled", "total": 80},
}

TICKETS: list[dict] = []
