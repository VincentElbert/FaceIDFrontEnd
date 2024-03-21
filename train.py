import os
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn import multiclass
from sklearn.preprocessing import StandardScaler
import pickle
import numpy as np
import time


def train(encodingpath):
    encodings = []
    names = []

    with open(encodingpath, "r") as file:
        for line in file:
            if len(line.split(":", 1)) < 2:
                continue
            name, encodingTxtCommaSeparated = line.split(":", 1)
            names.append(name)
            encodingTxt = encodingTxtCommaSeparated.split(",")
            encoding = [float(value) for value in encodingTxt]
            encodings.append(encoding)

    encodings = np.array(encodings)
    names = np.array(names)

    X_train, X_test, y_train, y_test = train_test_split(encodings, names, test_size=0.3, random_state=42, stratify=names)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = multiclass.OneVsRestClassifier(linear_model.SGDClassifier(loss='log_loss'))
    clf.fit(X_train_scaled, y_train)

    p = clf.predict_proba(X_test_scaled)
    labels = np.argmax(p, axis=1)
    labels = [clf.classes_[i] for i in labels]

    with open('face_classifier.pkl', 'wb') as fid:
        pickle.dump(clf, fid)


