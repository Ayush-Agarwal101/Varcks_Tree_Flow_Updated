# project_blueprint/backend
## Purpose
The backend folder contains the server-side logic and API endpoints for the online bakery shop project, built using Python and FastAPI.

## Responsibilities
* Handle requests from the frontend
* Process data and return responses
* Interact with the database to store and retrieve data
* Provide a scalable and maintainable API

## Key Functions (Conceptual)
* get_baked_goods(category, limit) -> list of baked goods
  Description: Retrieves a list of baked goods based on category and limit.
* create_order(customer_id, items) -> order_id
  Description: Creates a new order for a customer with the given items.
* update_product(product_id, new_data) -> success status
  Description: Updates the data of a product with the given ID.

## Interactions
* Receives requests from the frontend
* Sends responses to the frontend
* Interacts with the database to store and retrieve data

## Future Extensibility
* Add new API endpoints for additional features
* Integrate with other services, such as payment gateways
* Implement authentication and authorization for secure access to API endpoints