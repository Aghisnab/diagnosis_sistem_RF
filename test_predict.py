# test_predict.py

import joblib
import numpy as np
import pandas as pd
import sys
from models.custom_transformer import FeatureSelector

# Supaya bisa load model yang menyimpan FeatureSelector
sys.modules['__main__'].FeatureSelector = FeatureSelector

model = joblib.load('ml_model/best_rf_model.pkl')
label_encoder = joblib.load('ml_model/label_encoder.pkl')
selected_features = joblib.load('ml_model/selected_features.pkl')

# Gejala khas Flu / Selesma
input_symptoms = [
    'batuk',
    'bersin',
    'sakit kepala',
    'hidung tersumbat',
    'demam'
]

input_data = {feature: [1 if feature in input_symptoms else 0] for feature in selected_features}
df_input = pd.DataFrame(input_data)

# Prediksi
prediction_encoded = model.predict(df_input)
predicted_label = label_encoder.inverse_transform(prediction_encoded)[0]
print("🔮 Prediksi:", predicted_label)

# Probabilitas top-3
proba = model.predict_proba(df_input)[0]
top_idx = np.argsort(proba)[::-1][:3]
for idx in top_idx:
    print(f"{label_encoder.inverse_transform([idx])[0]}: {proba[idx]*100:.2f}%")
