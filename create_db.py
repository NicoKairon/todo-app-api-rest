import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Engels666___",
    database="todo_app",
)

my_cursor = mydb.cursor()

# Create 'users' table
my_cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), last_name VARCHAR(255), email VARCHAR(255))")

# Create 'todos' table
my_cursor.execute("CREATE TABLE todos (id INT AUTO_INCREMENT PRIMARY KEY, done BOOLEAN, task VARCHAR(255))")

# Show tables in the 'todos' database
my_cursor.execute("SHOW TABLES")
for table in my_cursor:
    print(table)