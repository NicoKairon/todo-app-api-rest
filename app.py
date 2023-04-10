from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Engels666___'
app.config['MYSQL_DB'] = 'todo-app'
CORS(app, origins=["http://localhost:3000"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE"])

db = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB'],
)

class Todo:
    def __init__(self, id, task, done):
        self.id = id
        self.task = task
        self.done = done

    def as_dict(self):
        return {
            "id": self.id,
            "task": self.task,
            "done": self.done
        }

@app.route('/api')
def home():
    return "Todo App Home Page"

@app.route("/api/todos", methods=["GET", "POST"])
def todos_list():
    if request.method == "GET":
        cursor = db.cursor()
        cursor.execute("SELECT * FROM todos")
        todos = [Todo(*row).as_dict() for row in cursor.fetchall()]
        return jsonify(todos), 200
    elif request.method == "POST":
        task = request.json["task"]
        done = False
        cursor = db.cursor()
        cursor.execute("INSERT INTO todos (task, done) VALUES (%s, %s)", (task, done))
        db.commit()
        todo_id = cursor.lastrowid
        todo = Todo(todo_id, task, done)
        return jsonify(todo.as_dict()), 201

@app.route("/api/todos/<int:index>", methods=["GET", "PUT", "DELETE"])
def todo_detail(index):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM todos WHERE id=%s", (index,))
    row = cursor.fetchone()
    if row is None:
        return "", 404
    todo = Todo(*row)
    if request.method == "GET":
        return jsonify(todo.as_dict()), 200
    elif request.method == "PUT":
        task = request.json["task"]
        done = request.json["done"]
        cursor.execute("UPDATE todos SET task=%s, done=%s WHERE id=%s", (task, done, index))
        db.commit()
        todo.task = task
        todo.done = done
        return jsonify(todo.as_dict()), 200
    elif request.method == "DELETE":
        cursor.execute("DELETE FROM todos WHERE id=%s", (index,))
        db.commit()
        return "succes", 204

@app.route("/api/todos/<int:todo_id>", methods=["PATCH"])
def update_todo_state(todo_id):
    # Get the todo item from the database
    todo = Todo.query.get_or_404(todo_id)
    # Get the "done" field from the request payload
    done = request.json.get("done")
    # Update the "done" attribute of the todo item
    if done is not None:
        todo.done = bool(done)
        db.session.commit()

    # Return the updated todo item as JSON
    return jsonify(todo.as_dict()), 200

if __name__ == "__main__":
      app.run()
