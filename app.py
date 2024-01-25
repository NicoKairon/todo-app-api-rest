import json
from flask import Flask, jsonify, make_response, request, session
from flask_cors import CORS
import mysql.connector
from webauthn import generate_authentication_options, generate_registration_options, verify_registration_response
import base64

app = Flask(__name__)
app.secret_key = 'Password123___'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Engels666___'
app.config['MYSQL_DB'] = 'todo-app'
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
# CORS(app, supports_credentials=True, origins=["http://localhost:3000"],
#      allow_headers=["Content-Type", "Authorization"],
#      methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
# CORS(app, supports_credentials=True)

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

USER_STORE = {}
print("USER_STORE:", USER_STORE)

@app.route('/register', methods=['POST'])
def register():
    print("Request received in /register")
    # Extract user information from the request
    username = request.json['username']

    # Convert username to bytes for user_id
    # user_id_bytes = username.encode()

    # Generate registration options
    options = generate_registration_options(
        rp_name='Fingerprint App',
        # rp_id='fingerprint-pwa-6m38.vercel.app',
        rp_id='localhost',
        # user_id=user_id_bytes,    # User ID in bytes
        user_name=username,       # User's name
    )

    # Serialize options to a JSON compatible format
    options_dict = {
        'rp': {'name': options.rp.name, 'id': options.rp.id},
        'user': {
            'id': base64.b64encode(options.user.id).decode('utf-8'),
            'name': options.user.name,
            'display_name': options.user.display_name
        },
        'challenge': base64.b64encode(options.challenge).decode('utf-8'),
        'pub_key_cred_params': [{'type': p.type, 'alg': p.alg.value} for p in options.pub_key_cred_params],
        'timeout': options.timeout,
        'exclude_credentials': [{'id': base64.b64encode(c.id).decode('utf-8'), 'type': c.type} for c in options.exclude_credentials],
        'authenticator_selection': options.authenticator_selection,
        'attestation': options.attestation.value if options.attestation else None,
        # 'user_id': base64.b64encode(user_id_bytes).decode('utf-8')
    }

     # Convert options_dict to a JSON string for the cookie
    options_json = json.dumps(options_dict)

    # Create the response object with JSON data
    response = make_response(jsonify(options_dict))

    # Set the cookie with options_dict data
    response.set_cookie('registration_options', options_json)
    # response.set_cookie('test_cookie', 'test_value')
    print("Cookie 'registration_options' set on response")

    return response

# @app.route('/register/verify', methods=['POST'])
# def verify_register():
#     print("Request received in /register/verify")

#     # Get the response from the client
#     response = request.json
#     print("Response from frontend:", response)

#     # options_json = request.
#     options_json = request.cookies.get('registration_options')
#     print("Options JSON from cookie:", options_json)

#     try:
#         # Retrieve the stored options

#         if not options_json:
#             print("No options JSON found in cookie.")
#             return jsonify({'error': 'Missing options data'}), 400
#         else:
#             print("Options JSON successfully retrieved from cookie.")

#         # Simplified response for debugging
#         return jsonify({'status': 'ok', 'message': 'Endpoint triggered successfully'})

#     except Exception as e:
#         print("Error during processing:", e)  # Log the exception
#         # Return a JSON response with the error message
#         return jsonify({'status': 'failed', 'message': str(e)}), 500


@app.route('/register/verify', methods=['POST'])
def verify_register():
    # Get the response from the client
    response = request.json
    print("Response:", response)

    try:
        # Retrieve the stored options
        options_json = request.cookies.get('registration_options')
        print("options_json:", options_json)

        if not options_json:
            return jsonify({'error': 'Missing options data'}), 400

        # Convert the JSON string back to a dictionary
        options_dict = json.loads(options_json)
        print("options_dict:", options_dict)

        challenge_value = options_dict['challenge']
        print("challenge_value:", challenge_value)

        # # Perform the WebAuthn verification
        verification = verify_registration_response(
            credential=response,
            expected_challenge=options_dict['challenge'],
            expected_origin='localhost',
            # expected_rp_id='fingerprint-pwa-6m38.vercel.app',
            expected_rp_id='localhost',
            require_user_verification=True
        )
        print('verification:' ,verification)

        # Decode user_id from Base64 back to bytes
        user_id_bytes = base64.b64decode(options_dict['user_id'])
        # Convert bytes to string assuming it was originally UTF-8 encoded
        username = user_id_bytes.decode('utf-8')

        # Store user's registration information
        # Make sure to store only JSON serializable data
        USER_STORE[verification.credential_id] = {
            'username': username,
            # Store other necessary details from 'verification' as needed
            # Make sure they are JSON serializable
        }

        return jsonify({'status': 'ok', 'message': 'Registration successful'})

    except Exception as e:
        print("Error during verification:", e)  # Log the exception
        # Handle exceptions and return an appropriate response
        return jsonify({'status': 'failed', 'message': str(e)}), 400


# @app.route('/login', methods=['POST'])
# def initiate_login():
#     username = request.json['username']

#     # Assuming user_id is derived from username
#     user_id_bytes = username.encode()

#     # Generate authentication options
#     options = generate_authentication_options(
#         rp_id='localhost',  # Change to your domain in production
#         user_id=user_id_bytes,
#         # ... other necessary parameters ...
#     )

#     # Serialize options to a JSON compatible format
#     options_dict = {
#         'challenge': base64.b64encode(options.challenge).decode('utf-8'),
#         # ... serialize other fields as needed ...
#         'allow_credentials': [{'id': base64.b64encode(cred.id).decode('utf-8'), 'type': cred.type, 'transports': cred.transports} for cred in options.allow_credentials],
#         'user_verification': options.user_verification,
#         # ... add other necessary fields from the options ...
#     }

#     # Store the serialized options in the session
#     session['authentication_options'] = options_dict

#     return jsonify(options_dict)


################################################################################
################################################################################
################################################################################

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
        return "success", 204

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
