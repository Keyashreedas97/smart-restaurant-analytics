# Database Schema

## User
id, name, email, password_hash, role, created_at

## Restaurant
id, name, city, manager_name, active

## Employee
id, name, department, restaurant_id, performance_score

## Review
id, user_id, restaurant_id, food_rating, service_rating, ambience_rating, cleanliness_rating, speed_rating, overall_rating, comment, sentiment, sentiment_score, created_at

## Order
id, restaurant_id, amount, order_type, created_at

Relationships:
User 1---N Review
Restaurant 1---N Review
Restaurant 1---N Employee
Restaurant 1---N Order
