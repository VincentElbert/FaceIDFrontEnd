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
            encoding = []
            for i in range(len(encodingTxt)):
                encoding.append(float(encodingTxt[i]))
            encodings.append(encoding)

    X_train, X_test, y_train, y_test = train_test_split(encodings, names, test_size=0.3, random_state=42, stratify=names)
    clf = multiclass.OneVsRestClassifier(linear_model.SGDClassifier(loss='log_loss'))
    clf.fit(X_train, y_train)

    p = clf.predict_proba(X_test)
    labels = np.argmax(p, axis=1)
    labels = [clf.classes_[i] for i in labels]

    with open('face_classifier.pkl', 'wb') as fid:
        pickle.dump(clf, fid)


