import face_recognition
import os


def encodingToLine(name, encoding):
    line = name + ":"
    for i in range(len(encoding)):
        line += str(encoding[i])
        if i < len(encoding) - 1:
            line += ","
    return line + "\n"

def encodeSet(imgpath, txtpath):

    train_dir = os.listdir(imgpath)

    # Loop through each person in the training directory
    for person in train_dir:
        encodeByPerson(imgpath, person, txtpath)

def encodeByPerson(imgpath, person, txtpath):
    encodings = []
    names = []

    pix = os.listdir(imgpath + '/' + person)
    for person_img in pix:
        # Get the face encodings for the face in each image file
        face = face_recognition.load_image_file(imgpath + '/' + person + "/" + person_img)
        if checkFace(imgpath + '/' + person + "/" + person_img):
            face_enc = face_recognition.face_encodings(face)[0]
            # Add face encoding for current image with corresponding label (name) to the training data
            encodings.append(face_enc)
            names.append(person)


    # Clear file and write new encodings


    file = open(txtpath, "a")
    for (name, encoding) in zip(names, encodings):
        print(encodingToLine(name, encoding))
        file.write(encodingToLine(name, encoding))

    file.close()

def checkFace(imgpath):
    face = face_recognition.load_image_file(imgpath)
    face_bounding_boxes = face_recognition.face_locations(face)
    # If training image contains exactly one face
    if len(face_bounding_boxes) == 1:
        return True
    else:
        print(imgpath + "does not contain one face")
        return False

def checkValidCamInput(imgpath, acceptableNum):
    valid_counter = 0
    pix = os.listdir(imgpath)
    for img in pix:
        if checkFace(imgpath + '/' + img):
            valid_counter += 1
    return valid_counter >= acceptableNum


