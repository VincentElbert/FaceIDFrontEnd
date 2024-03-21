from PIL import Image
import numpy as np
import face_recognition
import os

def encodeSet(imgpath, txtpath):

    train_dir = os.listdir(imgpath)
    
    # Loop through each person in the training directory
    for person in train_dir:
        file = open(txtpath, "a")
        for person_img in person:
            encodingLine = encodeByPerson(person_img)
            if encodingLine:
                file.write("\n" + person + encodingLine)
        file.close()
        encodeByPerson(imgpath, person, txtpath)

def encodeByPerson(imgpath):
    # Get the face encodings for the face in each image file
    img = Image.open(imgpath)
    img_arr = np.array(img)
    if checkFace(img_arr):
        encoding = face_recognition.face_encodings(img_arr)[0]
        return  ":" + ",".join(str(val) for val in encoding)

def checkFace(imgpath):
    face_bounding_boxes = face_recognition.face_locations(imgpath)
    # If training image contains exactly one face
    if len(face_bounding_boxes) == 1:
        return True
    else:
        print("Image does not contain one face; it contains: " + str(len(face_bounding_boxes)))
        return False

def checkValidCamInput(imgpath, acceptableNum):
    valid_counter = 0
    pix = os.listdir(imgpath)
    for img in pix:
        if checkFace(imgpath + '/' + img):
            valid_counter += 1
    return valid_counter >= acceptableNum


