

DEFAULT_AMOUNT = {
    "region": 12,
    "city": 48,
    "district": 180,
    "parking": 420,
    "sc": 70,
    "car": 650,
    "employee": 55,
    "renter": 1400,
}

CAR_CLASSES = ["econom", "middle", "premium", "family"]

CAR_CLASS_INFO = {
    "econom": {
        "brands": [("Kia", "Rio"), ("Hyundai", "Solaris"), ("Volkswagen", "Polo"), ("Renault", "Logan")],
        "capacity": [4, 5],
        "engine": (1.2, 1.6),
        "fuel": (5.8, 7.6),
        "cost_min": (7, 12),
        "cost_hour": (320, 520),
    },
    "middle": {
        "brands": [("Toyota", "Corolla"), ("Skoda", "Octavia"), ("Mazda", "3"), ("Volkswagen", "Jetta")],
        "capacity": [5],
        "engine": (1.6, 2.0),
        "fuel": (6.5, 8.8),
        "cost_min": (10, 16),
        "cost_hour": (450, 780),
    },
    "premium": {
        "brands": [("BMW", "3 Series"), ("Mercedes-Benz", "C-Class"), ("Audi", "A4"), ("Lexus", "ES")],
        "capacity": [4, 5],
        "engine": (2.0, 3.5),
        "fuel": (8.0, 12.5),
        "cost_min": (18, 28),
        "cost_hour": (950, 1800),
    },
    "family": {
        "brands": [("Skoda", "Kodiaq"), ("Kia", "Carnival"), ("Volkswagen", "Caddy"), ("Toyota", "RAV4")],
        "capacity": [5, 7],
        "engine": (1.8, 2.5),
        "fuel": (7.0, 10.5),
        "cost_min": (14, 22),
        "cost_hour": (700, 1300),
    },
}

SERVICE_NAMES = [
    ("Oil change", "Engine oil and filter replacement."),
    ("Brake inspection", "Inspection of brake pads, discs and fluid."),
    ("Tire fitting", "Seasonal tire replacement and balancing."),
    ("Diagnostics", "Computer diagnostics of vehicle systems."),
    ("Suspension repair", "Repair of shock absorbers, arms and bushings."),
    ("Battery service", "Battery diagnostics and replacement."),
    ("Engine repair", "Minor and major engine repair services."),
    ("Body repair", "Bodywork, painting and polishing."),
    ("Car wash", "Exterior and interior cleaning."),
    ("Air conditioning service", "Refill, cleaning and diagnostics of AC system."),
]

ROLE_NAMES = ["renter", "employee", "administration"]

PAYMENT_SYSTEMS = ["VISA", "MASTERCARD", "MIR"]

ACTION_TYPES = ["insert", "update", "delete"]

BOOKING_TYPES = ["mins", "hours"]

VISIT_STATUSES = ["planned", "in_progress", "done", "cancelled"]

CAR_COLORS = [
    "white", "black", "gray", "silver", "blue", "red", "green", "brown"
]
