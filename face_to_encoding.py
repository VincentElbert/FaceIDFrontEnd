from PIL import Image
import numpy as np
import face_recognition
import os
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'image')
def encodeSet(imgpath, txtpath):
    train_dir = os.listdir(imgpath)
    encodings = []  # Accumulate encodings in a list
    
    # Loop through each person in the training directory
    for person in train_dir:
        for person_img in person:
            encodingLine = encodeByPerson(person_img)
            if encodingLine:
                encodings.append(person + encodingLine)

    # Open the file once and write encodings in batches
    with open(txtpath, "a") as file:
        file.write("\n")
        file.write("\n".join(encodings))

def encodeByPerson(imgpath):
    # Get the face encodings for the face in each image file
    img = Image.open(imgpath)
    img.save(UPLOAD_FOLDER)
    img_arr = np.array(img)
    face_locations = face_recognition.face_locations(img_arr)

    if len(face_locations) == 1:
        encoding = face_recognition.face_encodings(img_arr, face_locations)[0]
        return  ":" + ",".join(str(val) for val in encoding)

def checkFace(imgpath):
    return len(face_recognition.face_locations(imgpath)) == 1

def checkValidCamInput(imgpath, acceptableNum):
    valid_counter = 0
    pix = os.listdir(imgpath)
    for img in pix:
        if checkFace(imgpath + '/' + img):
            valid_counter += 1
    return valid_counter >= acceptableNum