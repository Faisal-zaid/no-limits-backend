# No Limit Brands

Date, 2026/09/07
By Faisal Ali Zaid

## Description

No Limit Brands is an e-commerce web application built to provide users with a platform where they can browse and purchase products from different categories.

The project was developed as part of my software engineering journey and to use it to learn more production needed skills that i didnt get to learn at school and demonstrate the skills I have gained in both frontend and backend development.

The application allows users to create accounts, log in, browse products, search for products, view product details, add products to their cart, provide custom product information where required, and place orders.

The system also includes an admin dashboard where administrators can manage categories, products, product fields, users, and orders. Products can have customizable fields depending on the type of product being sold, including text, number, dropdown, date, textarea, and image fields.

The application also integrates M-Pesa payments through the Safaricom Daraja API, allowing customers to make payments directly from the checkout process.

The project focuses on building a complete e-commerce system with a separate frontend and backend, database management, authentication, product management, order processing, stock management, and online payments.

## Installation

You use git clone to be able to download the repository from GitHub.

## Installation Requirements

Git

## Installation instruction

Clone the repository:

```bash
git clone https://github.com/Faisal-zaid/no-limits-backend
```



Install the frontend dependencies:

```bash
npm install
```

Install the backend dependencies:

```bash
pipenv install
```

Activate the backend virtual environment:

```bash
pipenv shell
```

Create and configure the required environment variables for the frontend and backend.

Run the backend:

```bash
uvicorn app:app --reload
```

Run the frontend:

```bash
npm run dev
```

The frontend will then be available on:

```text
http://localhost:3000
```

## Technologies used

Github
Next.js
React
JavaScript
Tailwind CSS
Python
FastAPI
SQLAlchemy
PostgreSQL
Alembic
JWT Authentication
Cloudinary
M-Pesa Daraja API
Redis

## Features

### Customer Features

User registration and login
JWT-based authentication
Product browsing
Product search
Product categories
Product customization
Shopping cart
Order creation
Stock validation
M-Pesa payments
Order and payment status tracking

### Admin Features

Admin authentication
Admin dashboard
Product management
Category management
Custom product field management
Product field option management
Order management
User management
Admin role management
Stock management

## Backend

The backend is built using FastAPI and provides REST API endpoints for authentication, products, categories, product customization, orders, checkout, and M-Pesa payments.

SQLAlchemy is used to communicate with the PostgreSQL database, while Alembic is used for database migrations.

## Payment Integration

The project integrates M-Pesa using the Safaricom Daraja API.

During checkout, an order is created and the customer's requested stock is reserved. The customer can then initiate an M-Pesa STK Push from the checkout page.

Once the payment is completed, Safaricom sends a callback to the backend. The backend processes the callback and updates the order's payment status and stock accordingly.

## Support and contact details

https://github.com/Faisal-zaid


