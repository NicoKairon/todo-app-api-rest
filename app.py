import json
from flask import Flask, jsonify, make_response, request, session
from flask_cors import CORS
import mysql.connector
from webauthn import generate_authentication_options, generate_registration_options, verify_authentication_response, verify_registration_response
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

@app.route('/register/verify', methods=['POST'])
def verify_register():
    # Get the response from the client
    response = request.json
    print("Response:", response)

    try:
        # Retrieve the stored options
        options_json = request.cookies.get('registration_options')
        print("registration_options_json:", options_json)

        if not options_json:
            return jsonify({'error': 'Missing options data'}), 400

        # Convert the JSON string back to a dictionary
        options_dict = json.loads(options_json)
        print("options_dict:", options_dict)

        challenge_value_base64 = options_dict['challenge']
        print("challenge_value:", challenge_value_base64)
        challenge_value_bytes = base64.urlsafe_b64decode(challenge_value_base64)
        print("Challenge value (bytes):", challenge_value_bytes)

        # # Perform the WebAuthn verification
        verification = verify_registration_response(
            credential=response,
            expected_challenge=challenge_value_bytes,
            expected_origin='http://localhost:3000',
            # expected_rp_id='fingerprint-pwa-6m38.vercel.app',
            expected_rp_id='localhost',
            require_user_verification=False,
        )
        print('verification:' ,verification)

        # Retrieve the public key from the verification result
        public_key = verification.credential_public_key
        encoded_public_key = base64.b64encode(public_key).decode('utf-8')  # Convert bytes to Base64 string
        print('encoded_public_key', encoded_public_key)

        response = make_response(jsonify({'status': 'ok', 'message': 'Registration successful'}))
        # Set a cookie with public_key ALERT HERE IS THE ERROR, NOT SETTING COOKIE CORRECTLY
        response.set_cookie('public_key_cookie', encoded_public_key)

        # # Decode user_id from Base64 back to bytes?
        # user_id_bytes = options_dict['user']['id'] # This is not in bytes
        # print("user_id_bytes:", user_id_bytes)
        # # Convert bytes to string assuming it was originally UTF-8 encoded
        # # username = user_id_bytes.decode('utf-8')
        # username = user_id_bytes
        # print("username:", username)
        # # Store user's registration information
        # # Make sure to store only JSON serializable data
        # USER_STORE[verification.credential_id] = {
        #     'username': username,
        #     'public_key': public_key
        # }

        return response

    except Exception as e:
        print("Error during verification:", e)  # Log the exception
        # Handle exceptions and return an appropriate response
        return jsonify({'status': 'failed', 'message': str(e)}), 400

@app.route('/login', methods=['POST'])
def initiate_login():
    print('username reached login endpoint')
    username = request.json
    print('Username:', username)

    # Generate authentication options
    options = generate_authentication_options(
        rp_id='localhost'
    )

    # Serialize options to a JSON compatible format
    options_dict = {
    'challenge': base64.urlsafe_b64encode(options.challenge).decode('utf-8'),
    'timeout': options.timeout,
    'rp_id': options.rp_id,
    'allow_credentials': [],  # Assuming this is empty as per your example
    'user_verification': options.user_verification.value
    }
    print('options_dict', options_dict)

    # Convert options_dict to a JSON string for the cookie
    options_json = json.dumps(options_dict)

    # Create the response object with JSON data
    response = make_response(jsonify(options_dict))

    # Set the cookie with options_dict data
    response.set_cookie('verification_options', options_json)
    # response.set_cookie('test_cookie', 'test_value')
    print("Cookie 'verification_options' set on response")

    # Return JSON response
    return response

print('USER STORE', USER_STORE)

@app.route('/login_verify', methods=['POST'])
def verify_login():
    print('Login verify reached successfully')

    # Get the response from the client
    assertion_response = request.json
    print("Assertion Response:", assertion_response)

    try:
         # Retrieve the public key
        public_key_json = request.cookies.get('public_key_cookie')
        print("public_key_json:", public_key_json)

        if not public_key_json:
            return jsonify({'error': 'Missing public key'}), 400

        public_key_bytes = base64.urlsafe_b64decode(public_key_json)
        print("public key bytes", public_key_bytes)

        #Retrieve the stored options
        verification_options_json = request.cookies.get('verification_options')
        print('verification_options', verification_options_json)

        if not verification_options_json:
            return jsonify({'error': 'Missing options data no cookies'}), 400

        # Convert the JSON string back to a dictionary
        verification_options_dict = json.loads(verification_options_json)
        print("verification_options_dict:", verification_options_dict)

        challenge_value_base64 = verification_options_dict['challenge']
        print("challenge_value:", challenge_value_base64)
        challenge_value_bytes = base64.urlsafe_b64decode(challenge_value_base64)
        print("Challenge value (bytes):", challenge_value_bytes)

        # Extract the necessary data from assertion_response
        credential = {
            "id": assertion_response["id"],
            "rawId": assertion_response["rawId"],
            "response": {
                "authenticatorData": assertion_response["response"]["authenticatorData"],
                "clientDataJSON": assertion_response["response"]["clientDataJSON"],
                "signature": assertion_response["response"]["signature"],
                "userHandle": assertion_response["response"]["userHandle"] if assertion_response["response"]["userHandle"] else None
            },
            "type": assertion_response["type"]
        }
        print('credential', credential)

        # Retrieve the expected challenge, rp_id, origin, and public key
        expected_challenge = challenge_value_bytes
        expected_rp_id = 'localhost'
        expected_origin = 'http://localhost:3000' #?
        credential_public_key = public_key_bytes
        credential_current_sign_count = 0 #this is a hack

        # Perform authentication verification
        verification_result = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=expected_rp_id,
            expected_origin=expected_origin,
            credential_public_key=credential_public_key,
            credential_current_sign_count=credential_current_sign_count,
        )
        print("\n[Authentication Verification]")
        print('verification result', verification_result)

        # Check verification result and handle accordingly
        if verification_result:  # Assuming a successful verification returns a truthy value
            # Login success logic here (e.g., creating session)
            return jsonify({'status': 'ok', 'message': 'Login successful'})
        else:
            # Login failure logic here
            return jsonify({'status': 'failed', 'message': 'Login failed'}), 401

    except Exception as e:
        print("Error during login verification:", e)
        return jsonify({'status': 'failed', 'message': str(e)}), 500


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
