import sys
import os
import dlib
import glob
from skimage import io
import numpy as np
import pickle as pk
import cv2

from config import BASE_DIR


class FaceRecognition():
    
    def _get_dlib_coords(self, detection, image):
        """ Obtem as coordenadas de uma deteccao convertendo-as em coordenada absoluta
        Args:
            detecction (dict int) = dict com as coordenadas relativas
            image (ndarray): imagem em que foi encontrada a deteccao

        Returns:
            retorna as coordenadas absolutadas da deteccao
        """
        height, width, _ = image.shape

        left = detection['left'] * width
        top = detection['top'] * height
        right = left + detection['width'] * width
        bottom = top + detection['height'] * height

        return int(left), int(top), int(right), int(bottom)


    def __init__(self):
        self.predictor_path = BASE_DIR + "/data/alinhador/shape_predictor_68_face_landmarks.dat"  # http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
        self.face_rec_model_path = BASE_DIR + "/data/alinhador/dlib_face_recognition_resnet_model_v1.dat"  # http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2
        
        #self.detector = dlib.cnn_face_detection_model_v1(BASE_DIR + "/data/alinhador/mmod_human_face_detector.dat")
        self.detector = dlib.get_frontal_face_detector()
       
        self.sp = dlib.shape_predictor(self.predictor_path)  #shapes
        
        self.facerec = dlib.face_recognition_model_v1(self.face_rec_model_path)  # face recognition
        

    def escrever_arquivo(self, texto, nome_arquivo):
        f = open(nome_arquivo, 'w')
        f.write(texto)
        f.close()


    

    def _make_detection(self, ltwh, image):
        """ Constroi um dicionario de deteccao
        Args:
            ltwh (list int): lista contendo a localizacao de uma deteccao
            image: imagem em que foi encontrada a deteccao

        Returns:
            retorna o dicionario representando uma deteccao
        """
        height_img, width_img = image.shape[:2]
        left, top, width, height = ltwh

        return dict(
            classname='face',
            left=left/width_img,
            top=top/height_img,
            width=width/width_img,
            height=height/height_img)


    
    

    def detect_hog(self, image):
        faces = self.detector(image, 0)
        face_rects = [(f.left(), f.top(), f.width(), f.height()) for f in faces]
        return [self._make_detection(face_rect, image) for face_rect in face_rects]

    def get_embedding(self, detection , image):
        dlib_rect = dlib.rectangle(*self._get_dlib_coords(detection, image))
        shape = self.sp(image, dlib_rect)
        embedding = self.facerec.compute_face_descriptor(image, shape)
        return embedding

    
    def comparar_pessoas_google_imagens(self, img_bbox, nome_pessoa):
           
        database = {}  #armazena as imagens da pasta do nome da pessoa
        
        nome_pessoa = nome_pessoa.replace(" ", "_")
        database = pk.load(open(BASE_DIR + "/data/alinhador/database_g_image.pk", "rb"))
        
        img = io.imread(img_bbox)  # pega a imagem da Bbox
        detections = self.detect_hog(img)
        min_dist = 1
        for detection in detections:
            embedding = self.get_embedding(detection, img)
            embedding = np.array(embedding)
            closest = None
            for emb in database:
                dist = np.linalg.norm(np.array(emb) - embedding)
                if dist < min_dist:
                    min_dist = dist
                    closest = database[emb]
                    #print(closest, min_dist)
            print(closest, min_dist, nome_pessoa)
        return min_dist

    
    def comparar_pessoas(self, img_bbox, nome_pessoa):
        database = {}  #armazena as imagens da pasta do nome da pessoa
        nome_pessoa = nome_pessoa.replace(" ", "_")
        for f in glob.glob(BASE_DIR + "/data/alinhador/faceDB/lfw/" + nome_pessoa + "/*.jpg"):
            img = io.imread(f)
            label = f.split("/")[-1]
            detections = self.detect_hog(img)
           
            
            for detection in detections:
                embedding = self.get_embedding(detection, img)
                database[embedding] = label

        img = io.imread(img_bbox)
        detections = self.detect_hog(img)
        
        min_dist = 1
        print("FACES DETECTADAS: "+str(len(detections)))
        for detection in detections:
            embedding = self.get_embedding(detection, img)
            embedding = np.array(embedding)

            min_dist = np.inf
            closest = None
            for emb in database:
                dist = np.linalg.norm(np.array(emb) - embedding)
                if dist < min_dist:
                    min_dist = dist
                    closest = database[emb]
                    print(closest, min_dist)
            print(closest, min_dist)
            return min_dist


    def criar_db_g_images(self, folder):
        database = {}
        lst_nomes = []
        text_nomes = ""
        count = 0
        print(folder)
        for f in glob.glob(folder + "*.jpg"):
            count = count + 1
            m_img = cv2.imread(f)
            img =  cv2.resize(m_img, (300, 300)) 
            cv2.imwrite(f, img)
            # img = io.imread(f)
            label = f.split("/")[-1]
            detections = self.detect_hog(img)
            min_dist = 1
         
            
            if len(detections) == 1:  # se houver apenas uma face na imagem
                detection = detections[0]
                embedding = self.get_embedding(detection, img)
                database[embedding] = label
        pk.dump(database, open(BASE_DIR + "/data/alinhador/database_g_image.pk", "wb"))


    #     print(f)

    ## COMPARAR UMA FOTO COM O DATABASE
    '''
    database = pk.load(open("database_faces.pk", "rb"))

    img = io.imread("temer.jpg")
    dets = detector(img, 1)
    print(len(dets))
    for d in dets:
        shape = sp(img, d)
        embedding = facerec.compute_face_descriptor(img, shape, 100)
        embedding = np.array(embedding)

        min_dist = np.inf
        closest = None
        for emb in database:
            dist = np.linalg.norm(np.array(emb) - embedding)
            if dist < min_dist:
                min_dist = dist
                closest = database[emb]
                #print(closest, min_dist)
        print(closest, min_dist)
    '''