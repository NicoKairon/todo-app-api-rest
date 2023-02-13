from configparser import ConfigParser
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
config = ConfigParser()
config.read("config.ini")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CORS_HEADERS"] = "Content-Type"
CORS(app, supports_credentials=True)

# todos = [{
# 	"done": False,
# 	"task": "Learn React atm"
# }]

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)

    def as_dict(self):
        return {
            "id": self.id,
            "task": self.task,
            "done": self.done
        }

with app.app_context():
  db.create_all()

  @app.route("/todos", methods=["GET", "POST"])
  def todos_list():
      if request.method == "GET":
          todos = Todo.query.all()
          return jsonify([todo.as_dict() for todo in todos]), 200
      elif request.method == "POST":
          todo = Todo(task=request.json["task"])
          db.session.add(todo)
          db.session.commit()
          return jsonify(todo.as_dict()), 201

  @app.route("/todos/<int:index>", methods=["GET", "PUT", "DELETE"])
  def todo_detail(index):
      todo = Todo.query.get(index)
      if todo is None:
          return "", 404
      if request.method == "GET":
          return jsonify(todo.as_dict()), 200
      elif request.method == "PUT":
          todo.task = request.json["task"]
          todo.done = request.json["done"]
          db.session.commit()
          return jsonify(todo.as_dict()), 200
      elif request.method == "DELETE":
          db.session.delete(todo)
          db.session.commit()
          return "", 204

  if __name__ == "__main__":
      app.run()