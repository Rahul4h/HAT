# 🛒 HAT – E-commerce Web Application

HAT is a **Django-based e-commerce platform** designed for small online business owners.  
It provides product management, shopping cart, order delivery, secure checkout, and delivery management in a simple and scalable way.  

---

## 🚀 Features

- 🔑 **User Authentication**
  - Signup / Login / Logout
  - Email verification & account activation

- 🛍 **Product Management**
  - Browse products by category
  - Product detail pages
  - Add to cart / remove from cart
  - Re-order previous items

- 🛒 **Shopping Cart & Checkout**
  - Update cart quantity
  - Secure checkout flow
  - Payment integration (Stripe / SSLCommerz)

- 📦 **Order & Delivery**
  - Track orders
  - Cancel orders
  - Delivery boy login & task assignment
  - Return requests and management

- 🔎 **Other Features**
  - Product search
  - Blog section (list + details)
  - My Orders page for users
  - Dual confirmation of deliveryboy and customer before a =n order marked as delivered

---

## 🏗️ Tech Stack

- **Backend:** Django, Django ORM  
- **Frontend:** HTML, CSS, Bootstrap, JavaScript  
- **Database:** SQLite (can be upgraded to PostgreSQL/MySQL)  
- **Payment Gateway:** Stripe & SSLCommerz  
- **Authentication:** Django Allauth (email verification, login, signup)  

---

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/HAT.git
   cd HAT
2.Create a virtual environment
python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows
3.Run Migrations
python manage.py migrate
4.Create Super user
python manage.py createsuperuser
5.Run the Server
python manage.py runserver


