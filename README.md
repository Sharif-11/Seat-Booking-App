# YatraBD — Bus Seat Booking System

> A full-stack intercity bus ticket booking platform for Bangladesh, built with React + Vite + TypeScript on the frontend and a FastAPI backend.

---

## Table of Contents

1. [Business Requirements](#1-business-requirements)
2. [User Flows](#2-user-flows)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Database Schema](#4-database-schema)
5. [API Reference](#5-api-reference)
6. [Getting Started](#6-getting-started)

---

## 1. Business Requirements

### 1.1 Overview

YatraBD allows passengers in Bangladesh to search for inter-city bus trips, view real-time seat availability on a visual bus map, reserve seats, and complete payment via mobile wallet (bKash, Nagad, Rocket, Upay). An admin panel lets operators create and update trip schedules.

### 1.2 Actors

| Actor | Description |
|-------|-------------|
| **Guest** | Unauthenticated visitor who can browse and search trips |
| **Passenger** | Authenticated user who can book seats and make payments |
| **Admin** | Operator who can create and update trip schedules (demo, no auth guard on frontend) |

### 1.3 Functional Requirements

#### Search & Discovery
- A user can search trips by entering a **From** and **To** location
- Locations can be selected from a **pre-populated dropdown** listing all 8 Bangladesh divisions (Dhaka, Chittagong, Sylhet, Rajshahi, Khulna, Barishal, Mymensingh, Rangpur) plus popular cities (Cox's Bazar, Comilla, Gazipur, Narayanganj, Tangail, Bogura, Jessore, Brahmanbaria)
- A user may also **type freely** to search or use a location not in the list
- After submitting a search the page **smoothly scrolls** to the results section
- Each trip card shows: route (from → to), bus/service name, departure time, date, and price per seat
- Clicking a trip navigates to the seat selection page

#### Seat Selection
- The seat map is fetched live from the backend on page load
- Seats are rendered as a **top-down bus illustration** with rows of 4 seats (2 left, aisle, 2 right), a driver area, windshield, and rear lights
- Each seat displays one of three statuses:
  - **AVAILABLE** — green, selectable
  - **RESERVED** — amber, not selectable (temporarily held by another user)
  - **BOOKED** — red, not selectable (paid and confirmed)
- A user can **toggle selection** on available seats (click to select, click again to deselect)
- A **checkout panel** appears as soon as at least one seat is selected, showing: route, bus name, departure time, selected seat labels, per-seat price, and total amount
- A **refresh button** re-fetches the live seat map without navigating away

#### Authentication
- Authentication uses **phone-number OTP** (no passwords)
- The user enters an 11-digit Bangladeshi mobile number and requests an OTP
- The system handles three cases transparently:
  1. **Already verified user** — the server returns a token on `request-otp` directly; the user is logged in immediately without needing to enter an OTP
  2. **OTP already in-flight** — the server returns `remaining_seconds`; the frontend starts a countdown from that value and shows the OTP input
  3. **Fresh OTP** — standard flow; 60-second resend cooldown starts
- OTP entry uses a **6-box split input** with auto-advance on digit entry, backspace-to-previous navigation, and auto-submit when all 6 digits are filled
- The login modal is **continuous** (not stepped) — the phone field stays visible at all times; the OTP section slides in below it
- JWT token is stored in `localStorage` and attached to all subsequent requests via an Axios interceptor
- A **Sign In** button in the navbar opens the modal at any time
- If an unauthenticated user clicks **Proceed to Pay**, the login modal opens; after successful login the booking proceeds **automatically** without the user needing to click again

#### Booking
- Booking is created server-side, which **temporarily reserves** the selected seats
- The booking has an **expiry time** (server-defined, typically ~10 minutes); if payment is not completed before expiry, seats are released automatically
- After a successful booking creation the user is redirected to the Payment page

#### Payment (Demo)
- The payment page is a **demo simulation** — no real money moves
- The user selects a mobile wallet gateway: **bKash**, **Nagad**, **Rocket**, or **Upay**
- The user enters the wallet mobile number (11 digits)
- Two buttons allow simulating **Success** or **Failure**:
  - **Success** calls `POST /booking/{id}/success` — confirms the booking and creates a payment record; seats are permanently marked BOOKED
  - **Failure** calls `POST /booking/{id}/failed` — marks the booking failed and releases seats back to AVAILABLE
- On success a confirmation screen shows booking ID, transaction ID, gateway used, and total amount

#### Admin Panel
- Accessible via `/admin` route — no authentication gate (demo purposes)
- Two modes: **Create Trip** and **Update Trip** (toggle tabs)
- Both modes use the same `LocationPicker` component for From/To fields (selectable divisions + free text)
- **Create** requires: Bus/Service Name, From, To, Departure Time (datetime-local), Price (৳), Seat Count (default 28)
- **Update** requires: Trip ID, then same fields as Create (minus Seat Count)
- Seat layout is auto-generated by the backend from `seat_count` using the pattern: rows A–Z, columns 1–4 (last row may have fewer seats)

### 1.4 Non-Functional Requirements

- **Mobile-first responsive** — all pages are designed for 375px+ viewports, expanding gracefully to desktop
- **Real-time seat data** — seat map is fetched fresh on every trip page load with a manual refresh option
- **Idempotency** — booking and payment requests include a client-generated `idempotency_key` to prevent duplicate submissions on retry
- **Token persistence** — JWT survives page refresh via `localStorage`; auto-loaded on app mount
- **Graceful degradation** — all API errors surface as toast notifications; the UI never crashes silently

---

## 2. User Flows

### 2.1 Happy Path — Guest Books a Seat

```
Home page
  └─ Enter From (e.g. Chittagong) + To (e.g. Dhaka)
  └─ Click "Search Trips"
  └─ Page scrolls to results
  └─ Click a trip card
       └─ Seat map loads (TripDetail page)
       └─ Click one or more AVAILABLE seats
       └─ Checkout panel appears
       └─ Click "Proceed to Pay"
            └─ Not authenticated → Login modal opens
            └─ Enter 11-digit phone → "Send OTP"
                 ├─ Already verified  → auto-login, booking proceeds
                 └─ OTP sent          → enter 6-digit code → verify
                      └─ Authenticated → booking API called automatically
                           └─ Redirect to Payment page
                                └─ Select gateway (e.g. bKash)
                                └─ Enter wallet number
                                └─ Click "Simulate Success"
                                     └─ Success screen with transaction ID
```

### 2.2 Already-Logged-In User Books a Seat

```
Home → Search → Click Trip → Select Seats → "Proceed to Pay"
  └─ Authenticated → booking API called immediately
  └─ Redirect to Payment page → complete payment
```

### 2.3 OTP Already Sent

```
Login modal → enter phone → "Send OTP"
  └─ Server responds: "OTP already sent, valid for 73 more seconds"
  └─ OTP input appears, cooldown timer starts at 73s
  └─ User enters OTP → verified
```

### 2.4 Payment Failure

```
Payment page → select gateway → wallet number → "Simulate Failure"
  └─ POST /booking/{id}/failed called
  └─ Seats released back to AVAILABLE
  └─ Failure screen shown
  └─ User can navigate back and re-select seats
```

---

## 3. Frontend Architecture

```
src/
├── api/
│   └── index.ts          # Axios instance + all API functions
├── components/
│   ├── LocationPicker.tsx # Searchable dropdown with division chips
│   ├── LoginModal.tsx     # OTP authentication modal
│   ├── Navbar.tsx         # Top navigation with auth state
│   └── SeatMap.tsx        # Bus illustration with interactive seats
├── context/
│   └── AuthContext.tsx    # Global auth state (user, token, login, logout)
├── data/
│   └── locations.ts       # BD divisions + popular cities data
├── pages/
│   ├── Home.tsx           # Search form + trip results
│   ├── TripDetail.tsx     # Seat map + checkout panel
│   ├── Payment.tsx        # Gateway selection + payment simulation
│   └── Admin.tsx          # Create/update trip admin panel
├── types/
│   └── index.ts           # Shared TypeScript interfaces
├── App.tsx                # Router setup
└── main.tsx               # Entry point
```

**Tech Stack**

| Concern | Library |
|---------|---------|
| Framework | React 18 + Vite 5 |
| Language | TypeScript (strict, verbatimModuleSyntax) |
| Routing | React Router DOM v6 |
| HTTP | Axios |
| Notifications | react-hot-toast |
| Icons | lucide-react |
| Styling | CSS Modules (per-component scoped) |
| Fonts | Fraunces (display) + Plus Jakarta Sans (body) |

---

## 4. Database Schema

The backend is a FastAPI application. The inferred relational schema from API behavior is:

### 4.1 Entity Relationship Overview

```
users ──< bookings >── shows
              │
         booking_seats >── seats ──< shows
              │
           payments
```

### 4.2 Table Definitions

#### `users`

Stores registered passengers identified by phone number.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | Internal user ID |
| `phone` | VARCHAR(11) | UNIQUE, NOT NULL | 11-digit Bangladeshi mobile number |
| `is_verified` | BOOLEAN | DEFAULT FALSE | Whether the user has completed OTP verification |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration timestamp |

#### `otp_requests`

Tracks OTP issuance per phone number with TTL.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | |
| `phone` | VARCHAR(11) | NOT NULL | Target phone number |
| `otp_code` | VARCHAR(6) | NOT NULL | 6-digit OTP |
| `expires_at` | TIMESTAMP | NOT NULL | OTP validity deadline (~60–120s after issue) |
| `used` | BOOLEAN | DEFAULT FALSE | Consumed flag — OTP invalid after first use |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Issue time |

> **Note:** `remaining_seconds` in API responses is derived as `EXTRACT(EPOCH FROM (expires_at - NOW()))`.

#### `shows` (Trips)

A *show* is a scheduled bus trip on a specific route at a specific time.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | Trip ID |
| `title` | VARCHAR(255) | NOT NULL | Bus/service name (e.g. "Ena Paribahan") |
| `from_location` | VARCHAR(100) | NOT NULL | Departure city (stored lowercase) |
| `to_location` | VARCHAR(100) | NOT NULL | Destination city (stored lowercase) |
| `departure_time` | TIMESTAMP | NOT NULL | Scheduled departure (UTC stored, local displayed) |
| `price` | NUMERIC(10,2) | NOT NULL | Price per seat in BDT (৳) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

#### `seats`

Auto-generated when a show is created. Each row is one physical seat on the bus.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | Seat ID |
| `show_id` | INTEGER | FK → shows.id, NOT NULL | Parent trip |
| `seat_label` | VARCHAR(4) | NOT NULL | Human label: row letter + column number (e.g. `A1`, `F5`) |
| `status` | ENUM | DEFAULT `AVAILABLE` | `AVAILABLE` \| `RESERVED` \| `BOOKED` |

> **Seat label generation rule:** Given `seat_count`, seats are labelled in order: A1, A2, A3, A4, B1, B2, B3, B4, … Each row has 4 seats; the last row may have 1–4 seats depending on the remainder.

> **Status transitions:**
> - `AVAILABLE` → `RESERVED` when a booking is created (pending payment)
> - `RESERVED` → `BOOKED` when payment succeeds
> - `RESERVED` → `AVAILABLE` when booking expires or payment fails

#### `bookings`

A booking ties a user to one or more seats on a show.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | Booking ID |
| `user_id` | INTEGER | FK → users.id, NOT NULL | Passenger |
| `show_id` | INTEGER | FK → shows.id, NOT NULL | Trip |
| `status` | ENUM | DEFAULT `PENDING` | `PENDING` \| `CONFIRMED` \| `FAILED` \| `EXPIRED` |
| `total_amount` | NUMERIC(10,2) | NOT NULL | Sum of seat prices at time of booking |
| `idempotency_key` | VARCHAR(64) | UNIQUE, NOT NULL | Prevents duplicate bookings on retry |
| `expires_at` | TIMESTAMP | NOT NULL | Auto-computed (e.g. NOW() + 10 minutes); after this, seats are released |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |

#### `booking_seats`

Junction table linking a booking to its specific seats.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | |
| `booking_id` | INTEGER | FK → bookings.id, NOT NULL | |
| `seat_id` | INTEGER | FK → seats.id, NOT NULL | |

> **Unique constraint:** `(booking_id, seat_id)` — a seat cannot be in the same booking twice.

#### `payments`

Payment record created on successful payment confirmation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO INCREMENT | Payment ID |
| `booking_id` | INTEGER | FK → bookings.id, NOT NULL | Associated booking |
| `wallet_name` | VARCHAR(50) | NOT NULL | Gateway used: `BKASH` \| `NAGAD` \| `ROCKET` \| `UPAY` |
| `wallet_phone` | VARCHAR(11) | NOT NULL | User's wallet number |
| `transaction_id` | UUID | DEFAULT gen_random_uuid() | Unique transaction reference |
| `idempotency_key` | VARCHAR(64) | UNIQUE, NOT NULL | Prevents duplicate payment records |
| `status` | ENUM | NOT NULL | `SUCCESS` \| `FAILED` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |

---

## 5. API Reference

**Base URL:** `http://localhost:8000`

All request/response bodies are `application/json`.  
Authenticated endpoints require: `Authorization: Bearer <jwt_token>`

---

### 5.1 Authentication

#### `POST /auth/request-otp`

Request an OTP for a given phone number. Handles three scenarios in a single endpoint.

**Request body:**
```json
{ "phone": "01865926160" }
```

**Response — Case 1: User already verified (returns token immediately)**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "User already verified",
  "data": {
    "user_id": 1,
    "phone": "01865926160",
    "token": "<jwt>"
  }
}
```
> Frontend behaviour: call `login()` immediately, skip OTP input entirely.

**Response — Case 2: Fresh OTP sent**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "OTP sent successfully"
}
```
> `data` is absent. Frontend starts a 60-second resend cooldown.

**Response — Case 3: OTP already in-flight**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "OTP already sent. Please wait. OTP valid for 73 more seconds.",
  "data": {
    "remaining_seconds": 73
  }
}
```
> Frontend starts cooldown timer from `remaining_seconds`, shows OTP input.

---

#### `POST /auth/verify-otp`

Verify the 6-digit OTP and receive a JWT.

**Request body:**
```json
{
  "phone": "01844841934",
  "otp": "981118"
}
```

**Response — Success**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "Verification successful",
  "data": {
    "user_id": 2,
    "phone": "01844841934",
    "token": "<jwt>"
  }
}
```

**Response — Invalid OTP**
```json
{
  "status": "error",
  "status_code": 400,
  "message": "Invalid OTP"
}
```

**Response — Expired OTP**
```json
{
  "status": "error",
  "status_code": 410,
  "message": "OTP expired. Please request a new OTP. (Valid for 0 more seconds)"
}
```

> **Frontend behaviour:** On `status === "error"` or `status_code >= 400`, clear the OTP boxes and focus the first box. Prompt user to resend.

---

### 5.2 Shows (Trips)

#### `GET /shows/list`

Search for trips by route.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_location` | string | ✅ | Departure city (case-insensitive, lowercase recommended) |
| `to_location` | string | ✅ | Destination city (case-insensitive, lowercase recommended) |

**Example:** `GET /shows/list?from_location=chittagong&to_location=dhaka`

**Response:**
```json
{
  "status": "success",
  "status_code": 200,
  "data": [
    {
      "id": 1,
      "title": "Ena Paribahan",
      "from_location": "chittagong",
      "to_location": "dhaka",
      "departure_time": "2026-04-25T17:37:43.221000",
      "price": 650,
      "created_at": "2026-04-25T17:38:14.592807"
    }
  ]
}
```

> Returns an empty array `[]` if no trips match (not a 404).

---

#### `GET /shows/{show_id}/seats`

Fetch the live seat map for a specific trip.

**Path parameter:** `show_id` — integer, the trip ID.

**Response:**
```json
{
  "status": "success",
  "status_code": 200,
  "data": [
    { "id": 1, "seat_label": "A1", "status": "AVAILABLE" },
    { "id": 2, "seat_label": "A2", "status": "AVAILABLE" },
    { "id": 3, "seat_label": "A3", "status": "RESERVED" },
    { "id": 4, "seat_label": "A4", "status": "BOOKED"    },
    { "id": 5, "seat_label": "B1", "status": "AVAILABLE" }
  ]
}
```

**Seat status values:**

| Status | Meaning | UI |
|--------|---------|-----|
| `AVAILABLE` | Free to book | Green — clickable |
| `RESERVED` | Held by pending booking | Amber — not clickable |
| `BOOKED` | Paid and confirmed | Red — not clickable |

---

#### `POST /shows/create` 🔒 Admin

Create a new trip schedule. Seats are auto-generated from `seat_count`.

**Request body:**
```json
{
  "title": "Ena Paribahan",
  "from_location": "chittagong",
  "to_location": "dhaka",
  "departure_time": "2026-04-25T11:37:43.221Z",
  "price": 650,
  "seat_count": 28
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `title` | string | ✅ | Bus/service name |
| `from_location` | string | ✅ | Store lowercase |
| `to_location` | string | ✅ | Store lowercase |
| `departure_time` | ISO 8601 string | ✅ | UTC datetime |
| `price` | number | ✅ | Price per seat in BDT |
| `seat_count` | integer | ✅ | Number of seats to generate (1–60) |

**Response:**
```json
{
  "status": "success",
  "status_code": 201,
  "message": "Show created successfully",
  "data": {
    "id": 1,
    "title": "Ena Paribahan",
    "from_location": "chittagong",
    "to_location": "dhaka",
    "departure_time": "2026-04-25T17:37:43.221000",
    "price": 650,
    "created_at": "2026-04-25T17:38:14.592807"
  }
}
```

---

#### `PUT /shows/update/{show_id}` 🔒 Admin

Update an existing trip's details. Does **not** change seat count or regenerate seats.

**Path parameter:** `show_id` — integer.

**Request body:**
```json
{
  "title": "Ena Paribahan Express",
  "from_location": "chittagong",
  "to_location": "dhaka",
  "departure_time": "2026-04-25T17:15:46.589Z",
  "price": 700
}
```

**Response:**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "Show updated successfully",
  "data": {
    "id": 1,
    "title": "Ena Paribahan Express",
    "from_location": "chittagong",
    "to_location": "dhaka",
    "departure_time": "2026-04-25T17:15:46.589000",
    "price": 700,
    "created_at": "2026-04-25T17:38:14.592807"
  }
}
```

---

### 5.3 Booking

#### `POST /booking/` 🔒 Authenticated

Create a booking for one or more seats. Seats are immediately set to `RESERVED`.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "show_id": 1,
  "seat_ids": [1, 2],
  "idempotency_key": "bk_1_1745600000000_x8f2z9ab"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `show_id` | integer | ✅ | Trip ID |
| `seat_ids` | integer[] | ✅ | Array of seat IDs to book (must all be AVAILABLE) |
| `idempotency_key` | string | ✅ | Client-generated unique key (max 64 chars); prevents duplicate bookings on retry |

> **Frontend key format:** `bk_{show_id}_{Date.now()}_{random 8 chars}` — guaranteed unique per attempt.

**Response:**
```json
{
  "status": "success",
  "status_code": 201,
  "data": {
    "booking_id": 22,
    "seat_ids": [1, 2],
    "show_id": 1,
    "total_amount": 1300,
    "expires_at": "2026-04-25T17:44:19.077950"
  }
}
```

> `total_amount` = number of seats × show price.  
> `expires_at` is the UTC deadline before which payment must be completed.

**Error — seat already reserved/booked:**
```json
{
  "status": "error",
  "status_code": 409,
  "message": "One or more seats are not available"
}
```

---

### 5.4 Payment

#### `POST /booking/{booking_id}/success` 🔒 Authenticated

Confirm successful payment. Sets booking status to `CONFIRMED`, all seats to `BOOKED`, and creates a payment record.

**Path parameter:** `booking_id` — integer.

**Headers:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "status": "SUCCESS",
  "wallet_name": "BKASH",
  "wallet_phone": "01808496319",
  "idempotency_key": "pay_22_1745600123456"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | string | ✅ | Always `"SUCCESS"` for this endpoint |
| `wallet_name` | string | ✅ | `BKASH` \| `NAGAD` \| `ROCKET` \| `UPAY` |
| `wallet_phone` | string | ✅ | 11-digit wallet number |
| `idempotency_key` | string | ✅ | Unique per payment attempt (max 64 chars) |

**Response:**
```json
{
  "status": "success",
  "message": "Booking confirmed + payment created",
  "data": {
    "booking_id": 22,
    "payment_id": 5,
    "transaction_id": "1e2de449-9648-4659-85c3-a4d40cffc04f"
  }
}
```

> `transaction_id` is a UUID generated server-side, shown to the user as proof of payment.

---

#### `POST /booking/{booking_id}/failed` 🔒 Authenticated

Record a failed payment. Sets booking status to `FAILED` and releases all seats back to `AVAILABLE`.

**Path parameter:** `booking_id` — integer.

**Headers:** `Authorization: Bearer <token>`

**Request body:** *(same shape as success)*
```json
{
  "status": "SUCCESS",
  "wallet_name": "BKASH",
  "wallet_phone": "01438923272",
  "idempotency_key": "pay_22_1745600789012"
}
```

> Note: `status` field is still `"SUCCESS"` in the body — this is the wallet transaction status format. The endpoint path `/failed` determines the business outcome.

**Response:**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "Booking marked as failed and seats released"
}
```

---

### 5.5 API Summary Table

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/request-otp` | ❌ | Request OTP (or get token if already verified) |
| `POST` | `/auth/verify-otp` | ❌ | Verify OTP, receive JWT |
| `GET`  | `/shows/list` | ❌ | Search trips by route |
| `GET`  | `/shows/{id}/seats` | ❌ | Get live seat map for a trip |
| `POST` | `/shows/create` | ❌* | Create new trip (admin) |
| `PUT`  | `/shows/update/{id}` | ❌* | Update trip details (admin) |
| `POST` | `/booking/` | ✅ | Reserve seats, create pending booking |
| `POST` | `/booking/{id}/success` | ✅ | Confirm payment success |
| `POST` | `/booking/{id}/failed` | ✅ | Record payment failure, release seats |

> *Admin endpoints have no auth guard in the current backend (demo purposes).

---

### 5.6 JWT Structure

The token is a standard HS256 JWT. Decoded payload example:
```json
{
  "user_id": 1,
  "phone": "01865926160",
  "exp": 1777744110
}
```

Tokens are long-lived (expiry is ~1 year in the demo backend). In production, access tokens should expire in 15–60 minutes with a refresh token mechanism.

---

## 6. Getting Started

### Prerequisites

- Node.js ≥ 18
- Backend running at `http://localhost:8000`

### Install & Run

```bash
# Unzip (if needed)
unzip yatra-bd.zip && cd yatra-bd

# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:5173

# Production build
npm run build
npm run preview
```

### Environment

The API base URL is hardcoded to `http://localhost:8000` in `src/api/index.ts`. To change it for production, extract it to an env variable:

```ts
// src/api/index.ts
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
```

Then create `.env.local`:
```
VITE_API_URL=https://api.yourdomain.com
```

### Project Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | TypeScript check + production bundle |
| `npm run preview` | Preview production build locally |

---

## Appendix — Seat Label Examples

Given `seat_count = 25`:

```
Row A: A1  A2 │ A3  A4
Row B: B1  B2 │ B3  B4
Row C: C1  C2 │ C3  C4
Row D: D1  D2 │ D3  D4
Row E: E1  E2 │ E3  E4
Row F: F1  F2 │ F3  F4
Row G: G1  G2 │ G3  G4  (only 1 seat would overflow here)
```

Each row has 4 seats split as **2 left** (columns 1–2) | **aisle** | **2 right** (columns 3–4). The frontend detects this split using `parseInt(seat_label.slice(1)) <= 2`.

---

*YatraBD — Making Bangladesh travel smarter, one seat at a time. 🚌🇧🇩*