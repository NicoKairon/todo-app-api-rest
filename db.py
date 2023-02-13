from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120))
    done = db.Column(db.Boolean)

    def __repr__(self):
        return "<Todo %r>" % self.task

db.create_all()

@app.route("/todos", methods=["GET", "POST"])
def todos_list():
    if request.method == "GET":
        todos = Todo.query.all()
        return jsonify([t.__dict__ for t in todos]), 200
    elif request.method == "POST":
        todo = Todo(task=request.json["task"], done=False)
        db.session.add(todo)
        db.session.commit()
        return jsonify(todo.__dict__), 201

@app.route("/todos/<int:index>", methods=["GET", "PUT", "DELETE"])
def todo_detail(index):
    todo = Todo.query.get(index)
    if todo is None:
        return "", 404
    if request.method == "GET":
        return jsonify(todo.__dict__), 200
    elif request.method == "PUT":
        todo.task = request.json["task"]
        todo.done = request.json["done"]
        db.session.commit()
        return jsonify(todo.__dict__), 200
    elif request.method == "DELETE":
        db.session.delete(todo)
        db.session.commit()
        return "", 204

if __name__ == "__main__":
    app.run()