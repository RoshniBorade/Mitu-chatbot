import re
from flask import session

class EnrollmentFlow:
    # Steps
    STEP_INIT = 0
    STEP_NAME = 1
    STEP_EMAIL = 2
    STEP_PHONE = 3
    STEP_COURSE = 4
    STEP_CONFIRM = 5
    
    COURSES = [
        "Data Science & AI",
        "Python Programming",
        "Linux Administration",
        "Cloud Computing",
        "IoT & Raspberry Pi",
        "Full Stack Web Dev"
    ]

    @staticmethod
    def start_flow():
        session['flow'] = 'enrollment'
        session['step'] = EnrollmentFlow.STEP_NAME
        session['enroll_data'] = {}
        return {
            "reply": "Great! Let's get you enrolled. May I know your **Full Name**?",
            "progress": "Step 1 of 5"
        }

    @staticmethod
    def handle_input(user_input):
        step = session.get('step')
        data = session.get('enroll_data', {})

        if step == EnrollmentFlow.STEP_NAME:
            # Basic validation: Name should be at least 2 chars
            if len(user_input.strip()) < 2:
                return {"reply": "Please enter a valid full name (min 2 characters)."}
            
            data['name'] = user_input.strip()
            session['enroll_data'] = data
            session['step'] = EnrollmentFlow.STEP_EMAIL
            return {
                "reply": f"Thanks {data['name']}. Now, please enter your **Email Address**.",
                "progress": "Step 2 of 5"
            }

        elif step == EnrollmentFlow.STEP_EMAIL:
            # Email validation regex
            if not re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
                return {"reply": "Please enter a valid email address."}
            
            data['email'] = user_input.strip()
            session['enroll_data'] = data
            session['step'] = EnrollmentFlow.STEP_PHONE
            return {
                "reply": "Got it. What is your **Contact Number**?",
                "progress": "Step 3 of 5"
            }

        elif step == EnrollmentFlow.STEP_PHONE:
            # Basic phone validation (digits, min length)
            phone = re.sub(r'\D', '', user_input)
            if len(phone) < 10:
                return {"reply": "Please enter a valid 10-digit phone number."}
            
            data['phone'] = user_input.strip()
            session['enroll_data'] = data
            session['step'] = EnrollmentFlow.STEP_COURSE
            
            # Generate course buttons
            buttons = [{"label": c, "payload": c} for c in EnrollmentFlow.COURSES]
            return {
                "reply": "Which course are you interested in?",
                "buttons": buttons,
                "progress": "Step 4 of 5"
            }

        elif step == EnrollmentFlow.STEP_COURSE:
            # Validate course selection
            selected_course = user_input.strip()
            # If user typed something not in list, we could either be strict or loose. 
            # Let's be semi-strict but allow text entry if it matches roughly.
            
            # Let's trust the input or buttons for now.
            data['course'] = selected_course
            session['enroll_data'] = data
            session['step'] = EnrollmentFlow.STEP_CONFIRM
            
            summary = (
                f"**Please Confirm Your Details:**<br>"
                f"Name: {data.get('name')}<br>"
                f"Email: {data.get('email')}<br>"
                f"Phone: {data.get('phone')}<br>"
                f"Course: {data.get('course')}"
            )
            
            buttons = [
                {"label": "Confirm & Submit", "payload": "yes"},
                {"label": "Cancel", "payload": "cancel"}
            ]
            
            return {
                "reply": summary,
                "buttons": buttons,
                "progress": "Step 5 of 5"
            }

        elif step == EnrollmentFlow.STEP_CONFIRM:
            if user_input.lower() in ['cancel', 'no']:
                session.pop('flow', None)
                session.pop('step', None)
                session.pop('enroll_data', None)
                return {"reply": "Enrollment cancelled. Let me know if you need anything else!"}
            
            # Assuming Yes/Confirm
            final_data = session.get('enroll_data')
            
            # Return special flag to app.py to save to DB
            return {
                "reply": "Thank you! Your enrollment request has been submitted. Our team will contact you shortly.",
                "save_lead": True,
                "lead_data": final_data,
                "completed": True
            }

        return {"reply": "Something went wrong. Let's start over.", "reset": True}
