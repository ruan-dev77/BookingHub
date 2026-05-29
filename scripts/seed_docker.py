"""
Booking System — Seed via psycopg2
Conecta direto no PostgreSQL dentro do Docker e insere ~15.000 registros.
"""

import random
import psycopg2
from psycopg2.extras import execute_values
from datetime import date, datetime, timedelta
from faker import Faker

# ── Configuração de conexão ──────────────────────────────────────
DB = dict(
    host     = "localhost",
    port     = 5432,
    dbname   = "projeto_bd",
    user     = "admin",
    password = "admin123",
)

fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)

# ════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════
def log(msg):
    print(f"  {msg}")

def section(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")

# ════════════════════════════════════════════════════════════════
# Dados base
# ════════════════════════════════════════════════════════════════
AIRPORTS = [
    ("GRU","Aeroporto Int. de Guarulhos","São Paulo","Brasil"),
    ("CGH","Aeroporto de Congonhas","São Paulo","Brasil"),
    ("SDU","Aeroporto Santos Dumont","Rio de Janeiro","Brasil"),
    ("GIG","Aeroporto Int. do Galeão","Rio de Janeiro","Brasil"),
    ("BSB","Aeroporto Int. de Brasília","Brasília","Brasil"),
    ("CNF","Aeroporto Int. de Confins","Belo Horizonte","Brasil"),
    ("SSA","Aeroporto Int. de Salvador","Salvador","Brasil"),
    ("FOR","Aeroporto Int. Pinto Martins","Fortaleza","Brasil"),
    ("REC","Aeroporto Int. do Recife","Recife","Brasil"),
    ("POA","Aeroporto Int. Salgado Filho","Porto Alegre","Brasil"),
    ("CWB","Aeroporto Int. Afonso Pena","Curitiba","Brasil"),
    ("VCP","Aeroporto Int. de Viracopos","Campinas","Brasil"),
    ("MAO","Aeroporto Int. de Manaus","Manaus","Brasil"),
    ("BEL","Aeroporto Int. Val de Cans","Belém","Brasil"),
    ("CGB","Aeroporto Int. de Cuiabá","Cuiabá","Brasil"),
    ("MCZ","Aeroporto Int. Zumbi dos Palmares","Maceió","Brasil"),
    ("NAT","Aeroporto Int. São Gonçalo do Amarante","Natal","Brasil"),
    ("THE","Aeroporto Int. de Teresina","Teresina","Brasil"),
    ("JPA","Aeroporto Castro Pinto","João Pessoa","Brasil"),
    ("AJU","Aeroporto Int. de Aracaju","Aracaju","Brasil"),
    ("PMW","Aeroporto de Palmas","Palmas","Brasil"),
    ("PVH","Aeroporto Int. Gov. Jorge Teixeira","Porto Velho","Brasil"),
    ("MCP","Aeroporto Int. de Macapá","Macapá","Brasil"),
    ("BVB","Aeroporto Int. de Boa Vista","Boa Vista","Brasil"),
    ("RBR","Aeroporto Int. de Rio Branco","Rio Branco","Brasil"),
    ("GYN","Aeroporto Santa Genoveva","Goiânia","Brasil"),
    ("SLZ","Aeroporto Int. de São Luís","São Luís","Brasil"),
    ("VIX","Aeroporto Eurico de Aguiar Salles","Vitória","Brasil"),
    ("FLN","Aeroporto Int. Hercílio Luz","Florianópolis","Brasil"),
    ("IGU","Aeroporto Int. de Foz do Iguaçu","Foz do Iguaçu","Brasil"),
    ("JFK","John F. Kennedy International","Nova York","EUA"),
    ("MIA","Miami International Airport","Miami","EUA"),
    ("LAX","Los Angeles International","Los Angeles","EUA"),
    ("ORD","O'Hare International Airport","Chicago","EUA"),
    ("LHR","Heathrow Airport","Londres","Reino Unido"),
    ("CDG","Charles de Gaulle Airport","Paris","França"),
    ("MAD","Adolfo Suárez Barajas","Madri","Espanha"),
    ("FCO","Aeroporto Leonardo da Vinci","Roma","Itália"),
    ("AMS","Aeroporto de Amsterdã Schiphol","Amsterdã","Holanda"),
    ("FRA","Aeroporto de Frankfurt","Frankfurt","Alemanha"),
    ("LIS","Aeroporto Humberto Delgado","Lisboa","Portugal"),
    ("EZE","Aeroporto Int. de Ezeiza","Buenos Aires","Argentina"),
    ("SCL","Aeroporto Int. Arturo Merino Benítez","Santiago","Chile"),
    ("BOG","El Dorado International","Bogotá","Colômbia"),
    ("LIM","Aeroporto Int. Jorge Chávez","Lima","Peru"),
    ("DXB","Dubai International Airport","Dubai","Emirados Árabes"),
    ("SIN","Changi Airport","Singapura","Singapura"),
    ("NRT","Narita International Airport","Tóquio","Japão"),
    ("SYD","Kingsford Smith Airport","Sydney","Austrália"),
]

HOTEL_PREFIXES = ["Grand","Royal","Palace","Vista","Plaza","Premier",
                  "Golden","Blue","Green","Sunset","Star","City","Park","Ocean","Lake"]
HOTEL_SUFFIXES = ["Hotel","Resort","Inn","Suites","Lodge","Boutique","Hostel"]
BR_CITIES      = ["São Paulo","Rio de Janeiro","Brasília","Salvador","Fortaleza",
                  "Belo Horizonte","Curitiba","Manaus","Recife","Belém",
                  "Porto Alegre","Goiânia","Florianópolis","Maceió","Natal",
                  "Teresina","Campo Grande","João Pessoa","Aracaju","Palmas",
                  "São Luís","Vitória","Porto Velho","Macapá","Boa Vista",
                  "Foz do Iguaçu","Campinas","Uberlândia","Londrina","Joinville"]
AIRLINES       = ["LA","G3","AD","AA","AF","IB","TP","BA","LH","KL"]
ROOM_TYPES     = ["single","double","suite"]
ROOM_PRICE     = {"single":(150,350),"double":(250,600),"suite":(500,2000)}
ROOM_CAP       = {"single":1,"double":2,"suite":4}
METHODS        = ["credit_card","debit_card","pix","bank_transfer","paypal"]
BASE_DATE      = date(2025, 1, 1)

# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
def main():
    print("\n" + "═"*50)
    print("  Booking System — Seed (psycopg2 + Faker)")
    print("═"*50)

    conn = psycopg2.connect(**DB)
    conn.autocommit = False
    cur  = conn.cursor()

    try:

        # ── 1. AIRPORTS ─────────────────────────────────────────
        section("1/8 · Airports")
        execute_values(cur,
            "INSERT INTO airports (code, name, city, country) VALUES %s "
            "ON CONFLICT (code) DO NOTHING",
            AIRPORTS
        )
        cur.execute("SELECT id FROM airports ORDER BY id")
        airport_ids = [r[0] for r in cur.fetchall()]
        log(f"{len(airport_ids)} aeroportos inseridos.")

        # ── 2. HOTELS ───────────────────────────────────────────
        section("2/8 · Hotels")
        hotels = []
        for _ in range(150):
            name  = f"{random.choice(HOTEL_PREFIXES)} {random.choice(HOTEL_SUFFIXES)} {fake.last_name()}"
            city  = random.choice(BR_CITIES)
            state = fake.state()
            hotels.append((name, city, "Brasil", state))
        execute_values(cur,
            "INSERT INTO hotels (name, city, country, state) VALUES %s",
            hotels
        )
        cur.execute("SELECT id FROM hotels ORDER BY id")
        hotel_ids = [r[0] for r in cur.fetchall()]
        log(f"{len(hotel_ids)} hotéis inseridos.")

        # ── 3. FLIGHTS ──────────────────────────────────────────
        section("3/8 · Flights")
        flights = []
        for _ in range(800):
            number  = f"{random.choice(AIRLINES)}{random.randint(1000,9999)}"
            origin  = random.choice(airport_ids)
            dest    = random.choice([a for a in airport_ids if a != origin])
            dep_day = BASE_DATE + timedelta(days=random.randint(0, 364))
            dep_dt  = datetime(dep_day.year, dep_day.month, dep_day.day,
                               random.randint(5,22), random.choice([0,15,30,45]))
            arr_dt  = dep_dt + timedelta(hours=random.randint(1,12),
                                         minutes=random.choice([0,30]))
            total   = random.choice([100,120,150,180,200,220,250])
            avail   = random.randint(0, total)
            price   = round(random.uniform(199, 4500), 2)
            status  = random.choices(
                        ["scheduled","boarding","in_flight","landed","cancelled"],
                        weights=[70,5,10,10,5])[0]
            flights.append((number, origin, dest, dep_dt, arr_dt,
                            total, avail, price, status))
        execute_values(cur,
            """INSERT INTO flights
               (number, origin_airport_id, destination_airport_id,
                departure_time, arrival_time, total_seats,
                available_seats, price, status)
               VALUES %s""",
            flights
        )
        cur.execute("SELECT id, total_seats FROM flights ORDER BY id")
        rows         = cur.fetchall()
        flight_ids   = [r[0] for r in rows]
        flight_seats = {r[0]: r[1] for r in rows}
        log(f"{len(flight_ids)} voos inseridos.")

        # ── 4. ROOMS ────────────────────────────────────────────
        section("4/8 · Rooms")
        rooms = []
        for h_id in hotel_ids:
            for _ in range(4):
                rtype = random.choice(ROOM_TYPES)
                lo, hi = ROOM_PRICE[rtype]
                rooms.append((
                    h_id, rtype, ROOM_CAP[rtype],
                    round(random.uniform(lo, hi), 2),
                    random.choices([True, False], weights=[75, 25])[0]
                ))
        execute_values(cur,
            "INSERT INTO rooms (hotel_id, type, capacity, price_per_night, available) VALUES %s",
            rooms
        )
        cur.execute("SELECT id, hotel_id FROM rooms ORDER BY id")
        room_rows   = cur.fetchall()
        room_ids    = [r[0] for r in room_rows]
        room_hotel  = {r[0]: r[1] for r in room_rows}
        log(f"{len(room_ids)} quartos inseridos.")

        # ── 5. CUSTOMERS ────────────────────────────────────────
        section("5/8 · Customers")
        customers    = []
        used_emails  = set()
        c_count      = 0
        while c_count < 2000:
            name  = fake.name()
            email = fake.email()
            if email in used_emails:
                email = f"u{c_count}_{email}"
            used_emails.add(email)
            phone = fake.phone_number()[:30]
            ts    = fake.date_time_between(start_date="-3y", end_date="now")
            customers.append((name, email, phone, ts))
            c_count += 1
        execute_values(cur,
            "INSERT INTO customers (name, email, phone, created_at) VALUES %s",
            customers
        )
        cur.execute("SELECT id FROM customers ORDER BY id")
        customer_ids = [r[0] for r in cur.fetchall()]
        log(f"{len(customer_ids)} clientes inseridos.")

        # ── 6. FLIGHT RESERVATIONS ──────────────────────────────
        section("6/8 · Flight Reservations")
        fr_rows    = []
        seats_used = {fid: 0 for fid in flight_ids}
        attempts   = 0
        while len(fr_rows) < 4000 and attempts < 20000:
            attempts += 1
            cust   = random.choice(customer_ids)
            flt    = random.choice(flight_ids)
            seats  = random.randint(1, 3)
            if seats_used[flt] + seats > flight_seats[flt]:
                continue
            status = random.choices(
                        ["pending","confirmed","cancelled"],
                        weights=[20,60,20])[0]
            if status != "cancelled":
                seats_used[flt] += seats
            price = round(random.uniform(199, 4500) * seats, 2)
            ts    = fake.date_time_between(start_date="-2y", end_date="now")
            fr_rows.append((cust, flt, seats, status, price, ts))

        execute_values(cur,
            """INSERT INTO flight_reservations
               (customer_id, flight_id, num_seats, status, total_price, created_at)
               VALUES %s""",
            fr_rows
        )
        cur.execute("SELECT id FROM flight_reservations ORDER BY id")
        fr_ids = [r[0] for r in cur.fetchall()]
        log(f"{len(fr_ids)} reservas de voo inseridas.")

        # ── 7. HOTEL RESERVATIONS ───────────────────────────────
        section("7/8 · Hotel Reservations")
        hr_rows      = []
        room_periods = {rid: [] for rid in room_ids}

        def overlaps(periods, ci, co):
            return any(ci < b and co > a for a, b in periods)

        attempts = 0
        while len(hr_rows) < 2000 and attempts < 30000:
            attempts += 1
            cust   = random.choice(customer_ids)
            room   = random.choice(room_ids)
            h_id   = room_hotel[room]
            ci     = BASE_DATE + timedelta(days=random.randint(0, 364))
            nights = random.randint(1, 14)
            co     = ci + timedelta(days=nights)
            status = random.choices(
                        ["pending","confirmed","cancelled"],
                        weights=[15,65,20])[0]
            if status != "cancelled" and overlaps(room_periods[room], ci, co):
                continue
            if status != "cancelled":
                room_periods[room].append((ci, co))
            price = round(random.uniform(150, 2000) * nights, 2)
            ts    = fake.date_time_between(start_date="-2y", end_date="now")
            hr_rows.append((cust, room, h_id, ci, co, price, status, ts))

        execute_values(cur,
            """INSERT INTO hotel_reservations
               (customer_id, room_id, hotel_id, check_in, check_out,
                total_price, status, created_at)
               VALUES %s""",
            hr_rows
        )
        cur.execute("SELECT id FROM hotel_reservations ORDER BY id")
        hr_ids = [r[0] for r in cur.fetchall()]
        log(f"{len(hr_ids)} reservas de hotel inseridas.")

        # ── 8. PAYMENTS ─────────────────────────────────────────
        section("8/8 · Payments")
        pay_rows = []
        PAY_W    = [10, 75, 10, 5]
        PAY_ST   = ["pending","completed","refunded","failed"]

        for frid in random.sample(fr_ids, k=int(len(fr_ids) * 0.9)):
            ts = fake.date_time_between(start_date="-2y", end_date="now")
            pay_rows.append((
                "flight", frid, None,
                round(random.uniform(199, 9000), 2),
                random.choice(METHODS),
                random.choices(PAY_ST, weights=PAY_W)[0],
                ts
            ))

        for hrid in random.sample(hr_ids, k=int(len(hr_ids) * 0.9)):
            ts = fake.date_time_between(start_date="-2y", end_date="now")
            pay_rows.append((
                "hotel", None, hrid,
                round(random.uniform(150, 15000), 2),
                random.choice(METHODS),
                random.choices(PAY_ST, weights=PAY_W)[0],
                ts
            ))

        random.shuffle(pay_rows)
        execute_values(cur,
            """INSERT INTO payments
               (reservation_type, flight_reservation_id, hotel_reservation_id,
                amount, payment_method, status, created_at)
               VALUES %s""",
            pay_rows
        )
        log(f"{len(pay_rows)} pagamentos inseridos.")

        # ── COMMIT ──────────────────────────────────────────────
        conn.commit()

        # ── VALIDAÇÃO FINAL ─────────────────────────────────────
        print("\n" + "═"*50)
        print("  Validação final")
        print("═"*50)
        tabelas = [
            "airports","hotels","flights","rooms",
            "customers","flight_reservations",
            "hotel_reservations","payments"
        ]
        total = 0
        for t in tabelas:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            n = cur.fetchone()[0]
            total += n
            print(f"  {t:<30} {n:>6,}")
        print(f"  {'─'*38}")
        print(f"  {'TOTAL':<30} {total:>6,}")
        print("═"*50)
        print("\n  ✓ Seed concluído com sucesso!\n")

    except Exception as e:
        conn.rollback()
        print(f"\n  ✗ ERRO — rollback executado.\n  {e}\n")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
