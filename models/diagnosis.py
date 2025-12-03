import joblib
import sys
import numpy as np
import pandas as pd
from models.penyakit import Penyakit
import json  # ✅ Tambahan

# Import custom transformer
from models.custom_transformer import FeatureSelector
sys.modules['__main__'].FeatureSelector = FeatureSelector

# Load model dan tools
model = joblib.load('ml_model/best_rf_model.pkl')
label_encoder = joblib.load('ml_model/label_encoder.pkl')
selected_features = joblib.load('ml_model/selected_features.pkl')

def predict_disease(input_symptoms):
    print("🩺 Gejala dari frontend (ID):", input_symptoms)

    # Mapping ID ke nama gejala
    id_to_nama_gejala = {
        '1': 'nyeri ulu hati',
        '2': 'batuk',
        '3': 'nyeri dada tajam',
        '4': 'sakit kepala',
        '5': 'batuk dahak',
        '6': 'sakit tenggorokan',
        '7': 'kelelahan',
        '8': 'regurgitasi',
        '9': 'mual',
        '10': 'diare',
        '11': 'nafsu makan menurun',
        '12': 'dada terasa berat',
        '13': 'perut kembung',
        '14': 'mengi',
        '15': 'menggigil',
        '16': 'demam',
        '17': 'pilek',
        '18': 'muntah',
        '19': 'nyeri perut tajam',
        '20': 'nyeri perut kram',
        '21': 'bersin',
        '22': 'sesak napas',
        '23': 'nyeri perut terbakar',
        '24': 'hidung tersumbat',
        '25': 'nyeri seluruh tubuh'
    }


    gejala_nama_dipilih = [id_to_nama_gejala.get(str(gid), '') for gid in input_symptoms if str(gid) in id_to_nama_gejala]
    print("🩺 Gejala dari frontend (nama):", gejala_nama_dipilih)

    # Buat vektor fitur input
    input_data = {feature: [1 if feature in gejala_nama_dipilih else 0] for feature in selected_features}
    df_input = pd.DataFrame(input_data)

    # Prediksi probabilitas
    probabilities = model.predict_proba(df_input)[0]
    top_indices = np.argsort(probabilities)[::-1][:3]

    predictions = []
    kemungkinan_lainnya = []

    for i in top_indices:
        nama_penyakit = label_encoder.inverse_transform([i])[0]
        prob = float(probabilities[i])

        # Ambil ID penyakit dari database berdasarkan nama
        penyakit_obj = Penyakit.get_by_name(nama_penyakit)
        penyakit_id = penyakit_obj.id_penyakit if penyakit_obj else None

        predictions.append((nama_penyakit, prob, penyakit_id))
        kemungkinan_lainnya.append([nama_penyakit, round(prob, 4)])

    # Return hasil: top-1 + 2 kemungkinan lainnya (JSON)
    return predictions, json.dumps(kemungkinan_lainnya[1:])



# Fungsi utilitas untuk konversi ID ke nama gejala
def id_to_nama_gejala(ids):
    id_to_nama = {
        '1': 'nyeri ulu hati',
        '2': 'batuk',
        '3': 'nyeri dada tajam',
        '4': 'sakit kepala',
        '5': 'batuk dahak',
        '6': 'sakit tenggorokan',
        '7': 'kelelahan',
        '8': 'regurgitasi',
        '9': 'mual',
        '10': 'diare',
        '11': 'nafsu makan menurun',
        '12': 'dada terasa berat',
        '13': 'perut kembung',
        '14': 'mengi',
        '15': 'menggigil',
        '16': 'demam',
        '17': 'pilek',
        '18': 'muntah',
        '19': 'nyeri perut tajam',
        '20': 'nyeri perut kram',
        '21': 'bersin',
        '22': 'sesak napas',
        '23': 'nyeri perut terbakar',
        '24': 'hidung tersumbat',
        '25': 'nyeri seluruh tubuh'
    }
    return [id_to_nama.get(str(i), '') for i in ids]
