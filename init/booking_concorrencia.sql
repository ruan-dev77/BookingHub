-- ================================================================
-- Booking System - Controle de Concorrência (PostgreSQL)
-- ================================================================
-- Observações atendidas:
--   1. flights        → available_seats com controle de concorrência (SELECT FOR UPDATE)
--   2. customers      → email com constraint UNIQUE
--   3. flight_reservations → status: CHECK (pending/confirmed/cancelled)
--   4. hotel_reservations  → verificação de conflito de datas (EXCLUDE + trigger)
--   5. payments       → reservation_type: CHECK (flight/hotel) + integridade
-- ================================================================


-- ----------------------------------------------------------------
-- EXTENSÃO: necessária para EXCLUDE com range de datas
-- ----------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS btree_gist;


-- ----------------------------------------------------------------
-- TABELAS BASE (sem alteração de estrutura)
-- ----------------------------------------------------------------

CREATE TABLE airports (
    id      SERIAL PRIMARY KEY,
    code    CHAR(3)       NOT NULL UNIQUE,
    name    VARCHAR(150)  NOT NULL,
    city    VARCHAR(100)  NOT NULL,
    country VARCHAR(100)  NOT NULL
);

CREATE TABLE hotels (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(150)  NOT NULL,
    city    VARCHAR(100)  NOT NULL,
    country VARCHAR(100)  NOT NULL,
    state   VARCHAR(100)
);

CREATE TABLE flights (
    id                     SERIAL PRIMARY KEY,
    number                 VARCHAR(20)   NOT NULL,
    origin_airport_id      INT           NOT NULL REFERENCES airports(id),
    destination_airport_id INT           NOT NULL REFERENCES airports(id),
    departure_time         TIMESTAMP     NOT NULL,
    arrival_time           TIMESTAMP     NOT NULL,
    total_seats            INT           NOT NULL CHECK (total_seats > 0),
    available_seats        INT           NOT NULL CHECK (available_seats >= 0),
    price                  NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    status                 VARCHAR(30)   NOT NULL DEFAULT 'scheduled',

    CONSTRAINT chk_seats_consistency
        CHECK (available_seats <= total_seats)
);

CREATE TABLE rooms (
    id              SERIAL PRIMARY KEY,
    hotel_id        INT           NOT NULL REFERENCES hotels(id),
    type            VARCHAR(50)   NOT NULL,
    capacity        INT           NOT NULL CHECK (capacity > 0),
    price_per_night NUMERIC(10,2) NOT NULL CHECK (price_per_night >= 0),
    available       BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ----------------------------------------------------------------
-- OBS 2: customers → email UNIQUE (já garante unicidade)
-- ----------------------------------------------------------------
CREATE TABLE customers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(150)  NOT NULL,
    email      VARCHAR(255)  NOT NULL,
    phone      VARCHAR(30),
    created_at TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_customers_email UNIQUE (email)
);

-- ----------------------------------------------------------------
-- OBS 3: flight_reservations → status restrito a valores válidos
-- ----------------------------------------------------------------
CREATE TABLE flight_reservations (
    id          SERIAL PRIMARY KEY,
    customer_id INT           NOT NULL REFERENCES customers(id),
    flight_id   INT           NOT NULL REFERENCES flights(id),
    num_seats   INT           NOT NULL DEFAULT 1 CHECK (num_seats > 0),
    status      VARCHAR(30)   NOT NULL DEFAULT 'pending',
    total_price NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_flight_reservation_status
        CHECK (status IN ('pending', 'confirmed', 'cancelled'))
);

-- ----------------------------------------------------------------
-- OBS 4: hotel_reservations → conflito de datas bloqueado por
--         EXCLUDE USING gist  (impede overlap de datas por quarto)
--         + CHECK de integridade das datas
-- ----------------------------------------------------------------
CREATE TABLE hotel_reservations (
    id          SERIAL PRIMARY KEY,
    customer_id INT           NOT NULL REFERENCES customers(id),
    room_id     INT           NOT NULL REFERENCES rooms(id),
    hotel_id    INT           NOT NULL REFERENCES hotels(id),
    check_in    DATE          NOT NULL,
    check_out   DATE          NOT NULL,
    total_price NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    status      VARCHAR(30)   NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_hotel_reservation_status
        CHECK (status IN ('pending', 'confirmed', 'cancelled')),

    CONSTRAINT chk_checkin_before_checkout
        CHECK (check_in < check_out),

    -- Impede dois quartos iguais com datas sobrepostas (exceto canceladas)
    CONSTRAINT no_date_overlap
        EXCLUDE USING gist (
            room_id WITH =,
            daterange(check_in, check_out, '[)') WITH &&
        ) WHERE (status <> 'cancelled')
);

-- ----------------------------------------------------------------
-- OBS 5: payments → reservation_type restrito a 'flight' ou 'hotel'
--         + integridade: exatamente uma FK deve estar preenchida
-- ----------------------------------------------------------------
CREATE TABLE payments (
    id                    SERIAL PRIMARY KEY,
    reservation_type      VARCHAR(10)   NOT NULL,
    flight_reservation_id INT           REFERENCES flight_reservations(id),
    hotel_reservation_id  INT           REFERENCES hotel_reservations(id),
    amount                NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    payment_method        VARCHAR(50)   NOT NULL,
    status                VARCHAR(30)   NOT NULL DEFAULT 'pending',
    created_at            TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_payment_reservation_type
        CHECK (reservation_type IN ('flight', 'hotel')),

    -- Garante que apenas a FK correspondente ao tipo está preenchida
    CONSTRAINT chk_payment_fk_consistency CHECK (
        (reservation_type = 'flight'
            AND flight_reservation_id IS NOT NULL
            AND hotel_reservation_id  IS NULL)
        OR
        (reservation_type = 'hotel'
            AND hotel_reservation_id  IS NOT NULL
            AND flight_reservation_id IS NULL)
    )
);


-- ================================================================
-- OBS 1: flights → available_seats com controle de concorrência
--
-- Estratégia: SELECT FOR UPDATE trava a linha do voo enquanto
-- a transação calcula e decrementa os assentos disponíveis,
-- evitando race condition entre reservas simultâneas.
-- ================================================================

CREATE OR REPLACE FUNCTION reservar_assento(
    p_customer_id INT,
    p_flight_id   INT,
    p_num_seats   INT
)
RETURNS INT   -- retorna o id da reserva criada
LANGUAGE plpgsql AS
$$
DECLARE
    v_price          NUMERIC(10,2);
    v_avail          INT;
    v_reservation_id INT;
BEGIN
    -- 1. Trava exclusiva na linha do voo (bloqueia outras transações
    --    concorrentes que tentarem reservar o mesmo voo ao mesmo tempo)
    SELECT available_seats, price
      INTO v_avail, v_price
      FROM flights
     WHERE id = p_flight_id
       FOR UPDATE;           -- ← controle de concorrência

    -- 2. Verifica disponibilidade APÓS obter o lock
    IF v_avail IS NULL THEN
        RAISE EXCEPTION 'Voo % não encontrado.', p_flight_id;
    END IF;

    IF v_avail < p_num_seats THEN
        RAISE EXCEPTION
            'Assentos insuficientes. Disponíveis: %, solicitados: %.',
            v_avail, p_num_seats;
    END IF;

    -- 3. Decrementa assentos disponíveis
    UPDATE flights
       SET available_seats = available_seats - p_num_seats
     WHERE id = p_flight_id;

    -- 4. Cria a reserva
    INSERT INTO flight_reservations
        (customer_id, flight_id, num_seats, status, total_price)
    VALUES
        (p_customer_id, p_flight_id, p_num_seats, 'confirmed',
         v_price * p_num_seats)
    RETURNING id INTO v_reservation_id;

    RETURN v_reservation_id;
END;
$$;


-- ================================================================
-- TRIGGER: devolve assentos ao cancelar uma reserva de voo
-- ================================================================

CREATE OR REPLACE FUNCTION trg_devolver_assentos()
RETURNS TRIGGER LANGUAGE plpgsql AS
$$
BEGIN
    IF NEW.status = 'cancelled' AND OLD.status <> 'cancelled' THEN
        UPDATE flights
           SET available_seats = available_seats + OLD.num_seats
         WHERE id = OLD.flight_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_flight_reservation_cancel
AFTER UPDATE ON flight_reservations
FOR EACH ROW
EXECUTE FUNCTION trg_devolver_assentos();


-- ================================================================
-- EXEMPLOS DE USO
-- ================================================================

-- Reservar 2 assentos no voo 1 para o cliente 1:
--   SELECT reservar_assento(1, 1, 2);

-- Cancelar reserva (trigger devolve assentos automaticamente):
--   UPDATE flight_reservations SET status = 'cancelled' WHERE id = 1;

-- Tentativa de reserva com sobreposição de datas em hotel
-- será rejeitada pelo EXCLUDE USING gist automaticamente.
