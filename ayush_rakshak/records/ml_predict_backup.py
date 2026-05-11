import os
import joblib
from django.conf import settings


def get_heart_risk(input_data):
    try:
        # Django ko batana ki tera model kahan rakha hai
        model_path = os.path.join(settings.BASE_DIR, 'saved_models', 'heart_model.joblib')
        
        # Model ko load karna (Start the engine!)
        model = joblib.load(model_path)
        
        # Prediction nikalna (Machine Learning hamesha 2D array [[]] mangti hai)
        # input_data kuch aisa hoga: [52, 1, 2, 120, 200, 0, 1, 160, 0, 1.5, 2, 0, 2]
        result = model.predict([input_data]) 
        
        # Result bhej do (1 = Risk, 0 = Safe)
        return result[0]
        
    except Exception as e:
        print(f"Bhai model load hone mein error aagaya: {e}")
        return None
    
def get_diabetes_risk(input_data):
    try:
        path_1 = os.path.join(settings.BASE_DIR, 'saved_models', 'diabetes_model.joblib')
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_2 = os.path.join(current_dir, 'saved_models', 'diabetes_model.joblib')

        if os.path.exists(path_1):
            final_path = path_1
        elif os.path.exists(path_2):
            final_path = path_2
        else:
            return None

        # Diabetes Model Load Karo
        model = joblib.load(final_path)
        
        # Diabetes array: [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DPF, Age]
        result = model.predict([input_data]) 
        return result[0]
        
    except Exception as e:
        print(f" Diabetes model error: {e}")
        return None