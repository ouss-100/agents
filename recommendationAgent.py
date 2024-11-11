import psycopg2
from psycopg2.extras import DictCursor
import ollama
import ast
import pickle




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


def get_filtered_courses(preferred_languages, preferred_categories):
    db = connect_to_db()
    cursor = db.cursor(cursor_factory=DictCursor)
    try:
        # Dynamic placeholders for the SQL query
        language_placeholders = ', '.join(['%s'] * len(preferred_languages))
        category_placeholders = ', '.join(['%s'] * len(preferred_categories))
        
        # Query to filter courses
        query = f"""
            SELECT * FROM courses
            WHERE language IN ({language_placeholders})
            AND category IN ({category_placeholders})
        """
        
        # Execute query with preferred languages and categories as parameters
        cursor.execute(query, (*preferred_languages, *preferred_categories))
        filtered_courses = cursor.fetchall()
        return [dict(course) for course in filtered_courses]
    finally:
        cursor.close()
        db.close()


def get_all_courses():
    db = connect_to_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT * FROM courses"
        
        # Execute query with preferred languages and categories as parameters
        cursor.execute(query)
        filtered_courses = cursor.fetchall()
        return filtered_courses
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




def update_Recommendation_Q_table(course_id, feedback, user_id):
    state_action = (user_id, course_id)

    # If Q-value for this state-action pair is not initialized, set it to 0
    if state_action not in Q_table:
        Q_table[state_action] = 0

    # Calculate the updated Q-value
    old_value = Q_table[state_action]
    reward = feedback  # Treat feedback as the reward
    best_future_q = max(Q_table.get((user_id, c["course_id"]), 0) for c in get_all_courses())
    new_value = old_value + learning_rate * (reward + discount_factor * best_future_q - old_value)

    # Update Q-table with the new Q-value
    Q_table[state_action] = new_value
    print(f"Updated Q-value for user {user_id} and course {course_id}: {Q_table[state_action]}")
    save_q_table("Recommendation_Q_table.pkl")









def llama_recommendation(user_id):
    load_q_table("Recommendation_Q_table.pkl")

    user_info = get_user_info(user_id)
    preferred_languages = user_info.get("preferredLanguages", [])
    preferred_categories = user_info.get("preferredCategories", [])


    filtered_courses= get_filtered_courses(preferred_languages, preferred_categories)
    filtered_data = {key: value for key, value in Q_table.items() if key[0] == user_id}


    prompt = (
        f"Based on the user profile: {user_info} and provided Q-values: {filtered_data}, "
        f"select up to 3 ideal courses from the course list: {filtered_courses}. "
        "Provide recommendations in the following format: "
        "{course ID: 'description of focus for user in this course', course ID: 'description of focus for user in this course'} "
        "with no additional text, explanations, or formatting."
    )




    # Generate recommendations using LLaMA
    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    recommended_content = response["message"]["content"].strip()
    print(recommended_content)
    try:
        recommendations = ast.literal_eval(recommended_content)
    except (ValueError, SyntaxError) as e:
        return {"error": f"Failed to parse recommendation: {e}"}

    return recommendations




