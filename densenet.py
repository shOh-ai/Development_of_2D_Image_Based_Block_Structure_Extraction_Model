# -*- coding: utf-8 -*-
"""DenseNet & EfficientNetB3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1f-nhkUpTv_C67FrpWevwHN9uoKNqAs2c

Google Mount
"""

from google.colab import drive
drive.mount('/content/drive')

"""import Packages"""

import numpy as np
import cupy as cp
import os
import glob
import pandas as pd
import cv2
import io
import keras
import sklearn
import pydot
import graphviz
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
from torch.optim.lr_scheduler import StepLR

import seaborn as sns
import matplotlib.pyplot as plt
import tensorflow as tf

from sklearn.utils import shuffle
from keras.utils import to_categorical
from keras import Model
from keras.layers import Conv2D, MaxPooling2D, Flatten, BatchNormalization, Dropout, Dense, Activation
from keras.models import Sequential, load_model
from keras.utils import load_img
from keras.preprocessing.image import ImageDataGenerator
from PIL import Image, ImageFile
from sklearn.metrics import classification_report, confusion_matrix
from tqdm import tqdm # 반복 루프의 progress bar, 남은 시간 정보 제공 패키지
import IPython
from keras.utils import img_to_array

"""csv 파일 및 이미지 데이터 불러오기"""

df_train = pd.read_csv('/content/drive/MyDrive/train_split.csv')
df_val = pd.read_csv('/content/drive/MyDrive/validation_split.csv')
df_test = pd.read_csv('/content/drive/MyDrive/test.csv')

# 경로 수정
df_train['img_path'] = df_train['img_path'].str.replace('train', 'train_split')
df_val['img_path'] = df_val['img_path'].str.replace('train', 'train_split')

df_train['img_path'] = df_train['img_path'].str.replace('./train_split/', '')
df_val['img_path'] = df_val['img_path'].str.replace('./train_split/', '')

df_test['img_path'] = df_test['img_path'].str.replace('./test/', '')

columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# 이미지 폴더 경로
directory_train = "/content/drive/MyDrive/train_img_output"
directory_val = "/content/drive/MyDrive/validation_img_output"
directory_test = "/content/drive/MyDrive/test_img_output"

x_col = "img_path"

"""generator 생성하기"""

def get_train_generator(df_train, directory_train, x_col, columns, shuffle=True, batch_size=256, seed=30, target_w = 224, target_h = 224):
    # normalize images
    image_generator = ImageDataGenerator(
        samplewise_center=True,
        samplewise_std_normalization= True)

    generator = image_generator.flow_from_dataframe(
            dataframe = df_train,
            directory = directory_train,
            x_col = x_col,
            y_col = columns,
            class_mode="raw",
            shuffle = shuffle,
            batch_size = batch_size,
            seed = seed,
            target_size=(target_w,target_h))
    
    return generator

def get_validation_generator(df_val, directory_val, x_col, columns, shuffle = False, batch_size=128, seed=30, target_w = 224, target_h = 224):
    # normalize images
    image_generator = ImageDataGenerator(
    samplewise_center=True,
    samplewise_std_normalization= True)

    # get validation generator
    validation_generator = image_generator.flow_from_dataframe(
        dataframe = df_val,
        directory = directory_val,
        x_col = x_col,
        y_col = columns,
        class_mode = "raw",
        shuffle = shuffle,
        batch_size = batch_size,
        seed = seed,
        target_size=(target_w,target_h))
    
    return validation_generator

def get_test_generator(df_test, directory_test, x_col, columns, shuffle = False, batch_size=128, seed=30, target_w = 224, target_h = 224):
    # normalize images
    image_generator = ImageDataGenerator(
    samplewise_center=True,
    samplewise_std_normalization= True)

    # get test generator
    test_generator = image_generator.flow_from_dataframe(
        dataframe = df_test,
        directory = directory_test,
        x_col = x_col,
        y_col = columns,
        class_mode = "raw",
        shuffle = shuffle,
        batch_size = batch_size,
        seed = seed,
        target_size=(target_w,target_h))
    
    return test_generator

train_generator = get_train_generator(df_train, directory_train, "img_path", columns)
validation_generator = get_validation_generator(df_val, directory_val, "img_path", columns)
test_generator = get_test_generator(df_test, directory_test, "img_path", columns)

steps_per_epoch = train_generator.samples//train_generator.batch_size
steps_per_epoch

validation_steps = validation_generator.samples//validation_generator.batch_size
validation_steps

test_steps = test_generator.samples//test_generator.batch_size
test_steps

"""## DenseNet 구조"""

# 모델 구축
from keras.applications.densenet import DenseNet121
from keras.layers import Dense, GlobalAveragePooling2D
from keras import backend as K

# use the pretrained model of DenseNet121 available in Keras
base_model = DenseNet121(weights= 'imagenet', include_top=False)

x = base_model.output
x = GlobalAveragePooling2D()(x)
predictions = Dense(len(columns), activation="sigmoid")(x)

model = Model(inputs = base_model.input, outputs = predictions)

model.compile(optimizer='adam', loss = 'binary_crossentropy', metrics=['accuracy'])
model = Model(inputs = base_model.input, outputs = predictions)

from keras.callbacks import LearningRateScheduler

def step_decay(epoch):
    start = 0.01
    drop = 0.4
    epochs_drop = 5.0
    lr = start * (drop ** np.floor((epoch)/epochs_drop))
    return lr

lr_scheduler = LearningRateScheduler(step_decay, verbose=1)

# 모델 컴파일
model.compile(optimizer='adam',
              loss = 'binary_crossentropy',
              metrics=['accuracy'])

# test 모델 피팅
history = model.fit(train_generator,
                    validation_data = test_generator,
                    epochs = 30,
                    callbacks=[lr_scheduler],
                    steps_per_epoch = 50,
                    validation_steps = 11)

"""## DenseNetV2의 submission 파일 만들기"""

y_pred = model.predict(test_generator, steps = len(test_generator))
                                         
type(y_pred)
print(y_pred.shape)
print(y_pred.ndim)
print(y_pred.size)
print(y_pred)

def predict(y_df):
    preds=[]
    for i in y_df:
        for j in range(10):
            if i[j] > 0.5:
                preds.append(1)
            else:
                preds.append(0)
    return np.array(preds)

pred_arr = predict(y_pred)

print(pred_arr.shape)
print(pred_arr.ndim)
print(pred_arr.size)
print(pred_arr)

np_resha = pred_arr.reshape(1460,10)
pred_y_2 = np_resha
print(pred_y_2)

submit = pd.read_csv('/content/drive/MyDrive/sample_submission-2.csv')

submit.iloc[:, 1:] = pred_y_2  ### 여기서 pres = [[0, 1, 1, 0, 0, 1, 1, 0, 1, 1], [0, 1, 1, 1, 0, 1, 1, 1, 0, 1], [0, 1, 1, 0, 0, 1, 1, 1, 0, 0], ..., [0, 1, 1, 0, 0, 0, 1, 1, 0, 1]]
submit.head()

submit.to_csv('submit-2.csv', index=False)

"""## efficientNetB3"""

#!pip install efficientnet_pytorch

from efficientnet_pytorch import EfficientNet
model = EfficientNet.from_pretrained('efficientnet-b3')

# define input shape and batch size
input_shape = (224, 224, 3)
batch_size = 256

# build model
n_outputs = len(columns)

model_base = tf.keras.applications.EfficientNetB3(weights='imagenet', include_top=False, input_shape=input_shape)
model_base.trainable = False

model = Sequential([
    model_base,
    Dropout(0.3),
    Flatten(),
    Dense(n_outputs, activation="sigmoid")
])

model.summary()

from keras.callbacks import LearningRateScheduler

def step_decay(epoch):
    start = 0.01
    drop = 0.5
    epochs_drop = 5.0
    lr = start * (drop ** np.floor((epoch)/epochs_drop))
    return lr

lr_scheduler = LearningRateScheduler(step_decay, verbose=1)

# compile model
model.compile(optimizer = 'adam',
              loss="binary_crossentropy",
              metrics=["accuracy"])

# test model fit
history = model.fit(
    train_generator,
    epochs= 50,
    steps_per_epoch = 50,
    callbacks=[lr_scheduler],
    validation_data = test_generator,
    validation_steps = 11).history

"""### efficientNetB3 submission 파일 만들기기"""

y_pred = model.predict(test_generator, steps = len(test_generator))

def predict(y_df):
    preds=[]
    for i in y_df:
        for j in range(10):
            if i[j] > 0.5:
                preds.append(1)
            else:
                preds.append(0)
    return np.array(preds)

pred_arr = predict(y_pred)

print(pred_arr.shape)
print(pred_arr.ndim)
print(pred_arr.size)
print(pred_arr)

np_resha = pred_arr.reshape(1460,10)
pred_y_3 = np_resha
print(pred_y_3)

submit = pd.read_csv('/content/drive/MyDrive/sample_submission-3.csv')

submit.iloc[:, 1:] = pred_y_3  ### 여기서 pres = [[0, 1, 1, 0, 0, 1, 1, 0, 1, 1], [0, 1, 1, 1, 0, 1, 1, 1, 0, 1], [0, 1, 1, 0, 0, 1, 1, 1, 0, 0], ..., [0, 1, 1, 0, 0, 0, 1, 1, 0, 1]]
submit.head()

submit.to_csv('submit-3.csv', index=False)
