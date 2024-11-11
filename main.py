from flask import Flask, render_template, jsonify, request
from recommendationAgent import *
from AssessmentAgent import *





app = Flask(__name__)


#----------------RecommendationAgent----------------#


@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    user_id = request.json.get("user_id")
    recommendations = llama_recommendation(user_id)
    return jsonify(recommendations)



@app.route('/recommendationfeedback', methods=['POST'])
def update_feedback():
    user_id = request.json.get("user_id")
    course_id = request.json.get("course_id")
    feedback = request.json.get("feedback")

    if feedback not in [-1, 0, 1]:
        return jsonify({"error": "Invalid feedback value. Must be -1, 0, or 1."})

    update_Q_value(course_id, feedback, user_id)

    return jsonify({"message": "Feedback updated successfully."})







#----------------AssessmentAgent----------------#


@app.route('/Assessment', methods=['POST'])
def assess_user():
    user_id = request.json.get('user_id')
    assessment = llama_assessment(user_id)
    return jsonify({"assessment": assessment})



@app.route('/Assessmentfeedback', methods=['POST'])
def feedback():
    user_id = request.json.get('user_id')
    assessment = request.json.get('assessment')
    feedback_value = request.json.get('feedback')

    
    # Update Q-value based on feedback
    update_Q_value(assessment, feedback_value, user_id)
    
    return jsonify({"status": "Feedback received and Q-value updated!"})


if __name__ == '__main__':
    app.run(debug=True)