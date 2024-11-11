import pickle
from flask import Flask, render_template, request, jsonify
import ollama  # Assuming the ollama package is installed and properly configured
import psycopg2
from psycopg2.extras import DictCursor




def connect_to_db():
    # Replace with your actual PostgreSQL database URL
    db_url = "postgresql://postgres.uhwjxhfreuaqitwkoblg:MouhibNaffeti070@@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)

# Function to get user info by user_id
def get_user_info(user_id):
    db = connect_to_db()
    cursor = db.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user_info = cursor.fetchone()
        return dict(user_info) if user_info else None
    finally:
        cursor.close()
        db.close()









# Q-learning parameters
learning_rate = 0.1       # Determines how much new information overrides the old
discount_factor = 0.9     # Value placed on future rewards
epsilon = 0.2             # Probability of choosing exploration over exploitation

# Initialize a Q-table as a dictionary where keys are (user_id, course_id) pairs, values are Q-values
Q_table = {}

# Function to save the Q-table to a file
def save_q_table(filename):
    with open(f'tables/{filename}', "wb") as f:
        pickle.dump(Q_table, f)
    print("Q-table saved to", f'tables/{filename}')


# Function to load the Q-table from a file
def load_q_table(filename):
    global Q_table
    try:
        with open(f'tables/{filename}', "rb") as f:
            Q_table = pickle.load(f)
        print("Q-table loaded from", f'tables/{filename}')
    except FileNotFoundError:
        print("No Q-table found. Starting with an empty Q-table.")
        Q_table = {}





def llama_assessment(user_id):
    load_q_table("Assessment_Q_table")
    filtered_data = {key: value for key, value in Q_table.items() if key[0] == user_id}
    user = get_user_info(user_id)
    prompt = (
        f"Hey there! Based on the user's profile: {user} and the following Q-values: {filtered_data}, "
        "please offer helpful and personalized feedback to guide their improvement. "
        "Keep it friendly and concise, using no more than 30 words."
    )

    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()




def update_Q_value(assessments, feedback, user_id):
    state_action = (user_id, assessments)
    
    # Initialize Q-value if not present
    if state_action not in Q_table:
        Q_table[state_action] = 0
    
    # Retrieve the old Q-value
    old_value = Q_table[state_action]
    reward = feedback  # Feedback is treated as the reward
    
    # Get the best Q-value for future states
    future_q_values = [Q_table.get((user_id, next_action), 0) for next_action in Q_table]
    best_future_q = max(future_q_values) if future_q_values else 0  # Use 0 if no future Q-values exist
    
    # Calculate the updated Q-value
    new_value = old_value + learning_rate * (reward + discount_factor * best_future_q - old_value)
    
    # Update the Q-table with the new Q-value
    Q_table[state_action] = new_value
    print(f"Updated Q-value for user {user_id} and assessment {assessments}: {Q_table[state_action]}")
    save_q_table("Assessment_Q_table")


















