import pickle
import os
import numpy as np
import face_recognition
import face_to_encoding

def infer(imgpath):
    if not face_to_encoding.checkFace(imgpath):
        return None
    else:
        face = face_recognition.load_image_file(imgpath)
        face_enc = face_recognition.face_encodings(face)[0]
        with open('face_classifier.pkl', 'rb') as fid:
            clf = pickle.load(fid)
            p = clf.predict_proba(face_enc.reshape(1, -1))
            print(p)
            label_i = np.argmax(p, axis=1)
            if p[0][label_i] >= 0.95:
                return clf.predict(face_enc.reshape(1, -1))
            else:
                return "No Match"

def loginInfer(imgdir, label):
    matching_count = 0
    pix = os.listdir(imgdir)
    for img in pix:
        if infer(imgdir + '/' + img) == label:
            matching_count += 1
    return matching_count >= 9

