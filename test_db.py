from db import fetch_all
 
for row in fetch_all("SELECT customer_id, first_name, last_name FROM customer"):
    print(row)
print("Connected successfully!") 