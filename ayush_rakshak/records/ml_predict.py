import os
import joblib
from django.conf import settings

# 1. Models ko global variables mein rakho (Starting mein khali rakhenge)
_heart_model = None
_diabetes_model = None

def load_models_if_needed():
    """Ye function sir dard bachayega. Models ko memory mein sirf 1 baar load karega."""
    global _heart_model, _diabetes_model
    
    # Heart model caching
    if _heart_model is None:
        try:
            heart_path = os.path.join(settings.BASE_DIR, 'saved_models', 'heart_model.joblib')
            if os.path.exists(heart_path):
                _heart_model = joblib.load(heart_path)
        except Exception as e:
            print(f"Bhai heart model load hone mein error aagaya: {e}")

    # Diabetes model caching
    if _diabetes_model is None:
        try:
            path_1 = os.path.join(settings.BASE_DIR, 'saved_models', 'diabetes_model.joblib')
            current_dir = os.path.dirname(os.path.abspath(__file__))
            path_2 = os.path.join(current_dir, 'saved_models', 'diabetes_model.joblib')

            if os.path.exists(path_1):
                _diabetes_model = joblib.load(path_1)
            elif os.path.exists(path_2):
                _diabetes_model = joblib.load(path_2)
        except Exception as e:
            print(f"Diabetes model error: {e}")

def get_heart_risk(input_data):
    # Engine check karo: Agar model loaded nahi hai, toh load karo (Sirf pehli baar)
    load_models_if_needed()
    
    if _heart_model is None:
        print("Heart model file mili nahi!")
        return None
        
    try:
        # Prediction nikalna (Machine Learning hamesha 2D array [[]] mangti hai)
        result = _heart_model.predict([input_data])
        return result[0]
    except Exception as e:
        print(f"Heart prediction mein error: {e}")
        return None

def get_diabetes_risk(input_data):
    # Engine check karo
    load_models_if_needed()
    
    if _diabetes_model is None:
        print("Diabetes model file mili nahi!")
        return None
        
    try:
        result = _diabetes_model.predict([input_data])
        return result[0]
    except Exception as e:
        print(f"Diabetes prediction mein error: {e}")
        return None