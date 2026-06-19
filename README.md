# Enma Shop

Enma Shop is a modular e-commerce backend built with Django and Django REST Framework. It provides the core building blocks of an online marketplace, including authentication, shop and product management, address handling, cart and order flows, and ZarinPal sandbox payment integration.

## Highlights

- Phone-based user authentication with JWT
- Seller-ready shop and product management
- Product catalog and public shop catalog APIs
- Cart, checkout, order lifecycle, and payment retry flow
- ZarinPal sandbox payment integration
- Order audit logs for payment and status tracking
- Redis-backed caching and JWT blacklist support
- Celery workers for background SMS and email notifications
- Elasticsearch integration for search capabilities
- Arvan S3-compatible object storage support for media files

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Elasticsearch
- Docker Compose
- ZarinPal Sandbox
- Arvan Cloud S3 Storage

## Project Structure

- `Accounts`: custom user model, authentication, OTP/JWT-related flows
- `Addresses`: user address management
- `Shops`: seller shops and shop media
- `Products`: categories, products, and product media
- `Orders`: cart, checkout, payment, order status, and audit logs
- `Core`: shared utilities, base models, tasks, and helpers

## Running Locally

### Prerequisites

- Docker and Docker Compose
- A configured `Enma_Shop/.env` file

### Start services

```bash
docker compose up --build
```

Main local services:

- API: `http://127.0.0.1:8018`
- PostgreSQL: `127.0.0.1:5433`
- Redis: `127.0.0.1:6380`
- Elasticsearch: `http://127.0.0.1:9200`
- Kibana: `http://127.0.0.1:5601`

## Environment Notes

The project reads its configuration from `Enma_Shop/.env`, including:

- Django secret key and debug mode
- PostgreSQL connection settings
- Redis and Celery settings
- Elasticsearch host
- Arvan S3 storage credentials
- ZarinPal payment settings
- Email and SMS provider credentials
- Shipping-related order settings

## Current Scope

This project is intentionally focused on core backend commerce workflows and clean service structure. It is suitable as a portfolio project for demonstrating backend API design, payment flow handling, asynchronous task processing, and modular Django application architecture.
