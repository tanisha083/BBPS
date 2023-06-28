# -*- coding: utf-8 -*-
"""Pipeline_1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1v4qle7notb_ufpXo51LxGfAlmM_PMf9H

## Importing Required Libraries and Packages
"""

from __future__ import print_function, division
from builtins import range, input
import numpy as np
import tensorflow as tf
import keras
import cv2
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
from tensorflow.keras.applications.inception_v3 import InceptionV3
from keras.layers import Activation,Dropout,Flatten, Dense
from keras import backend as k
from keras.preprocessing import image
import time
from numpy.random import seed
seed(1337)
import tqdm
from glob import glob
from sklearn.utils import shuffle
from keras.models import Sequential
from keras.models import Model
from keras.layers import Dense, Activation, Conv2D, Flatten, BatchNormalization, Dropout, MaxPool2D
from tensorflow.keras.optimizers import Adam
from keras.callbacks import ReduceLROnPlateau, EarlyStopping
from keras.utils import np_utils
import pandas as pd
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras import layers
from keras.applications.vgg16 import VGG16
from keras.applications.vgg16 import preprocess_input
import albumentations as A
import random

!pip install tqdm

!pip install pandas

!apt-get update && apt-get install libgl1 -y

!pip install opencv-python

!pip install albumentations

!pip3 install matplotlib

!pip install -U scikit-learn

!pip uninstall sklearn

!pip install transformers[sklearn] --force-reinstall

!pip uninstall scipy

# re-size all the images to specific model
IMAGE_SIZE = [224, 224]

# training config:
batch_size = 16 #Change for cpu-32

"""##  Counting Files in Each Image Directory"""

import os
f=open("/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/path.txt", "r")
images_paths = f.read().split('\n')
for image in images_paths:
    if image:
        fileList=os.listdir(image)
        count=0
        for file in fileList:
            if not file.startswith('.'):
                count+=1
        print(image)
        print(len(fileList))
        print(count)
#         print(fileList)

"""## Setting Image Directory Paths"""

#paths
train_path = '/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/train'
valid_path = '/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/val'
test_path = '/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/test'

"""## Image Data Augmentation Configuration for Training"""

# create an instance of ImageDataGenerator - general
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
gen = ImageDataGenerator(
    A.Compose(
    [A.RandomRotate90(),
     A.Transpose(),
     A.HueSaturationValue()]),
#     rotation_range=40,
     rescale=None,
    horizontal_flip=True,
    fill_mode='nearest'
)
valid_datagen = ImageDataGenerator( rescale=None )

"""## Creating Image Data Generators for Training and Validation"""

# create generators
train_generator = gen.flow_from_directory(
  train_path,
  target_size=IMAGE_SIZE,
  shuffle=True,
  batch_size=batch_size,
  seed=42,
)

print(train_generator.class_indices)
labels=train_generator.class_indices
valid_generator = valid_datagen.flow_from_directory(
  valid_path,
  target_size=IMAGE_SIZE,
  shuffle=False,
  batch_size=batch_size,
  seed=42,
)
print(valid_generator.class_indices)

"""## Image Data Augmentation Example"""

# example of data aug
from numpy import expand_dims
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from matplotlib import pyplot
# load the image
img = load_img('/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/test/3/bowel_17_score_3-0_00000034.jpg')
# convert to numpy array
data = img_to_array(img)
# expand dimension to one sample
samples = expand_dims(data, 0)
# create image data augmentation generator
datagen = gen
# prepare iterator
it = datagen.flow(samples, batch_size=1)
# generate samples and plot
pyplot.figure(figsize=(20,10))
for i in range(20):
    # define subplot
    pyplot.subplot(5,5,i+1)
    batch = it.next()
    # convert to unsigned integers for viewing
    image = batch[0].astype('int32')
    pyplot.grid(False)
    pyplot.axis('off')
    # plot raw pixel data
    pyplot.imshow(image)
    plt.savefig('augmented_incppp_2.svg')

# show the figure
pyplot.show()

tf.test.is_gpu_available()

img

from tensorflow.keras.optimizers import SGD

"""# Creating a Transfer Learning Model with ResNetRS101 Backbone"""

from keras.applications.nasnet import NASNetLarge,NASNetMobile
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.inception_v3 import InceptionV3
from keras.applications.inception_resnet_v2 import InceptionResNetV2
from keras.applications.vgg16 import VGG16
base_model= tf.keras.applications.resnet_rs.ResNetRS101(
    input_shape=(224,224,3),
    include_top=False,
    weights="imagenet")
# base_model = tf.keras.applications.vgg16.VGG16(input_shape=(224,224,3), weights='imagenet', include_top=False)

for layer in base_model.layers:
    layer.trainable = False

from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.optimizers import SGD, Adam
import tensorflow_addons as tfa

x = layers.Flatten()(base_model.output)
x = layers.Dense(512, activation='relu')(x)
x = layers.Dropout(0.2)(x)
x = layers.Dense(256, activation='relu')(x)
x = BatchNormalization()(x)

# Add a final softmax layer with 4 node for classification output
x = layers.Dense(4, activation='softmax')(x)

model = tf.keras.models.Model(base_model.input, x)

import tensorflow as tf
import tensorflow_addons as tfa

"""## Configuring Callbacks for Model Training and Monitoring"""

#callbacks
import datetime
import wandb
from keras.callbacks import ModelCheckpoint
from tensorflow.keras import layers, models, Model, optimizers
from keras.callbacks import ModelCheckpoint
from wandb.keras import WandbCallback
from tensorflow.keras.callbacks import TensorBoard


early_stop = EarlyStopping(monitor='val_loss', patience=15, verbose=1, min_delta=1e-4)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=4, verbose=1, min_delta=1e-4)

log_dir = "/workspace/Tanisha/Boston_Scoring/Resnet50/log" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
# tensorboard_callback=TensorBoard(log_dir=wandb.run.dir)

!pip install wandb

"""## Learning Rate Scheduler Callback for Adaptive Learning Rate"""

def lr_scheduler(epoch, lr):
    # log the current learning rate onto W&B
    if wandb.run is None:
        raise wandb.Error("You must call wandb.init() before WandbCallback()")

    wandb.log({'learning_rate': lr}, commit=False)

    if epoch < 7:
        return lr
    else:
        return lr * tf.math.exp(-configs['lr_decay_rate'])

lr_callback = tf.keras.callbacks.LearningRateScheduler(lr_scheduler)

"""## Initializing Weights & Biases (W&B) Run and Configuring Experiment Parameters"""

# Initialize the W&B run
run = wandb.init(project='Nerthus',
    config={
    "init_learning_rate": 0.001,
    "lr_decay_rate": 3e-4,
    "metrics" : ['acc',tf.keras.metrics.AUC(),tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),tfa.metrics.F1Score(num_classes=4, average="macro")],
    "model_name" : 'ResNet101',
    "earlystopping_patience" : 15,
    "loss_fn" : 'categorical_crossentropy',
    "epochs": 100,
    },sync_tensorboard=True)
config = wandb.config

# model.summary()

sgd = tf.keras.optimizers.SGD(learning_rate=3e-4, momentum=0.8, nesterov=False)
model.compile(optimizer = sgd, loss = 'categorical_crossentropy', metrics = ['acc',tf.keras.metrics.AUC(),tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),tfa.metrics.F1Score(num_classes=4, average="macro")])

"""
# Define WandbCallback for experiment tracking
wandb_callback = WandbCallback()

# callbacks
callbacks_list = [early_stop, reduce_lr,lr_callback,model_checkpoint_callback,tensorboard_callback,wandb_callback]
tensorboard_callback = tf.keras.callbacks.TensorBoard(histogram_freq=1)"""

r = model.fit(train_generator,validation_data=valid_generator,epochs=config.epochs,callbacks=[WandbCallback(),TensorBoard(log_dir=wandb.run.dir)])

"""# !tensorboard --logdir logs/fit"""

run.finish()

"""## Loading Pretrained Weights into the Model"""

model.load_weights('/workspace/Tanisha/BOSTON/ResNet50/resnet101.h5')

with open("./result_resnet_101.txt",'w') as f:
    for k in r.history.keys():
        print(k,file=f)
        for i in r.history[k]:
            print(i,file=f)

cd VGG16

ls

np.mean(r.history['acc'])

np.mean(r.history['auc_1'])

np.mean(r.history['val_acc'])

np.mean(r.history['val_auc_1'])

np.mean(r.history['f1_score'])

np.mean(r.history['val_f1_score'])

np.mean(r.history['loss'])

np.mean(r.history['val_loss'])

"""##Visualizing Model Accuracy and Loss"""

import matplotlib.pyplot as plt

# summarize history for accuracy
plt.plot(r.history['acc'])
plt.plot(r.history['val_acc'])
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='best')
plt.savefig('incp_sgd_cnn_acc_6..svg',format='svg', dpi=1200)
plt.show()
# summarize history for loss
plt.plot(r.history['loss'])
plt.plot(r.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.savefig('incp_sgd_cnn_loss_6..svg',format='svg', dpi=1200)
plt.show()

"""## Visualizing Model AUC (Area Under the Curve)"""

import matplotlib.pyplot as plt

# summarize history for accuracy
plt.plot(r.history['auc_1'])
plt.plot(r.history['val_auc_1'])
plt.title('Model AUC')
plt.ylabel('AUC')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='best')
plt.savefig('incp_sgd_cnn_auc_6.svg',format='svg', dpi=1200)
plt.show()

import matplotlib.pyplot as plt

# summarize history for accuracy
plt.plot(r.history['f1_score'])
plt.plot(r.history['val_f1_score'])
plt.title('Model F1 Score')
plt.ylabel('F1 Score')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='best')
plt.savefig('incp_sgd_cnn_f1_Score_6.svg',format='svg', dpi=1200)
plt.show()

"""##Evaluating Model Performance on Test Data"""

testg = ImageDataGenerator(rescale=None)
test_gen = testg.flow_from_directory(
  test_path,
  target_size=IMAGE_SIZE,
  shuffle=False,
)
print(test_gen.class_indices)

# Evaluate on Validation data
scores = model.evaluate(valid_generator)
print("%s%s: %.2f%%" % ("evaluate ",model.metrics_names[1], scores[1]*100))

test_score = model.evaluate_generator(test_gen,steps=12)
print("[INFO] accuracy: {:.2f}%".format(test_score[1] * 100))
print("[INFO] Loss: ",test_score[0])

"""## Plotting and Analyzing the Confusion Matrix"""

#Plot the confusion matrix. Set Normalize = True/False
def plot_confusion_matrix(cm, classes, normalize=True, title='Confusion matrix', cmap=plt.cm.Greens):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    plt.figure(figsize=(6,6))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar().outline.set_visible(False)
    plt.box(False)
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes,fontsize=10)
    plt.yticks(np.arange(0,4),classes)
    if normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            cm = np.around(cm, decimals=2)
            cm[np.isnan(cm)] = 0.0
            print("Normalized confusion matrix")
    else:
            print('Confusion matrix, without normalization')
    thresh = cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black",fontsize=12)
    plt.ylabel('True label',ha='center', labelpad=-5)
    plt.xlabel('Predicted label')
    plt.savefig('test_cm.svg',format='svg', dpi=1200)
#Print the Target names
from sklearn.metrics import classification_report, confusion_matrix
import itertools

target_names = []
for key in train_generator.class_indices:
    target_names.append(key)

Y_pred = model.predict_generator(test_gen)
y_pred = np.argmax(Y_pred, axis=1)
print('Confusion Matrix')
cm = confusion_matrix(test_gen.classes, y_pred)
plot_confusion_matrix(cm, target_names, title='Confusion Matrix')
#Print Classification Report
print('Classification Report')
print(classification_report(test_gen.classes, y_pred, target_names=target_names))

from pandas import DataFrame
import numpy as np
import seaborn as sn
from sklearn.metrics import classification_report, confusion_matrix
import itertools
#shuffle=False
target_names = []
for key in train_generator.class_indices:
    target_names.append(key)
# print(target_names)
#Confution Matrix
Y_pred = model.predict_generator(test_gen)
y_pred = np.argmax(Y_pred, axis=1)
classes=['0','1','2','3']
columns = ['%s' %(i) for i in (classes)]

confm = confusion_matrix(test_gen.classes, y_pred)
df_cm = DataFrame(confm, index=columns, columns=columns)
annot_kws={'fontsize':20,
           'fontstyle':'oblique',
           'alpha':0.9,
           'verticalalignment':'center'}

ax = sn.heatmap(df_cm, cmap='Reds', annot=True,annot_kws=annot_kws,fmt="d")
plt.ylabel('True label',ha='center')
plt.xlabel('Predicted label')
plt.savefig('test_cm.svg',format='svg', dpi=1200)
print('Classification Report')
print(classification_report(test_gen.classes, y_pred, target_names=target_names))

"""### Plotting and Analyzing the Confusion Matrix for Validation Data"""

from string import ascii_uppercase
from pandas import DataFrame
import numpy as np
import seaborn as sn
from sklearn.metrics import classification_report, confusion_matrix
import itertools

target_names = []
for key in train_generator.class_indices:
    target_names.append(key)

Y_pred = model.predict_generator(valid_generator)
y_pred = np.argmax(Y_pred, axis=1)
classes=['0','1','2','3']
columns = ['%s' %(i) for i in (classes)]

confm = confusion_matrix(valid_generator.classes, y_pred)
df_cm = DataFrame(confm, index=columns, columns=columns)

ax = sn.heatmap(df_cm, cmap='Reds', annot=True,annot_kws={"size": 12},fmt="d")
plt.ylabel('True label',ha='center')
plt.xlabel('Predicted label')
plt.savefig('valid_cm.svg',format='svg', dpi=1200)
print('Classification Report')
print(classification_report(valid_generator.classes, y_pred, target_names=target_names))

"""# Feature Map"""

img_path='/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/test/1/bowel_10_score_1-0_00000019.jpg' #healthy

successive_outputs = [layer.output for layer in model.layers]

visualization_model = models.Model(inputs = model.input, outputs = successive_outputs)
#Load the input image
img = load_img(img_path, target_size=(224, 224))
# Convert ht image to Array of dimension (150,150,3)
x   = img_to_array(img)
x   = x.reshape((1,) + x.shape)
# Rescale by 1/255
x /= 255.0
# Let's run input image through our vislauization network
# to obtain all intermediate representations for the image.
successive_feature_maps = visualization_model.predict(x)
# Retrieve are the names of the layers, so can have them as part of our plot

layer_names = ['block5_conv3']
print(layer_names)
for layer_name, feature_map in zip(layer_names, successive_feature_maps):

  if len(feature_map.shape) == 4:

    # Plot Feature maps for the conv / maxpool layers, not the fully-connected layers

    n_features = feature_map.shape[-1]  # number of features in the feature map
    size       = feature_map.shape[ 1]  # feature map shape (1, size, size, n_features)

    # We will tile our images in this matrix
    display_grid = np.zeros((size, size * n_features))

    # Postprocess the feature to be visually palatable
    for i in range(n_features):
      x  = feature_map[0, :, :, i]
      x -= x.mean()
      x /= x.std ()
      x *=  64
      x += 128
      x  = np.clip(x, 0, 255).astype('uint8')
      # Tile each filter into a horizontal grid
      display_grid[:, i * size : (i + 1) * size] = x

# Display the grid
    scale = 20. / n_features
    plt.figure( figsize=(scale * n_features, scale), dpi=600)
    plt.title ( layer_name )
    plt.grid  ( False )
    plt.axis('off')
    plt.imshow( display_grid, aspect='auto', cmap='viridis' )
plt.savefig("fm11.png",dpi=600)

"""## Extracting Intermediate Layer Outputs from a Pretrained Model"""

# # Define a new Model, Input= image
# # Output= intermediate representations for all layers in the
# # previous model after the first.
successive_outputs = [layer.output for layer in model.layers[1:]]
# #visualization_model = Model(img_input, successive_outputs)
visualization_model = models.Model(inputs = model.input, outputs = successive_outputs)
#Load the input image
img = load_img('/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/train/3/bowel_17_score_3-0_00000103.jpg',target_size=(224, 224))
# img = load_img(img_path, target_size=(224, 224))
# Convert ht image to Array of dimension (150,150,3)
x   = img_to_array(img)
x=np.expand_dims(x,axis=0)

x.shape

# # Rescale by 1/255
# x /= 255.0
# # Let's run input image through our vislauization network
# # to obtain all intermediate representations for the image.
successive_feature_maps = visualization_model.predict(x)
# Retrieve are the names of the layers, so can have them as part of our plot
layer_names = [layer.name for layer in model.layers]

"""## Visualizing Feature Maps of Convolutional Layers"""

for layer_name, feature_map in zip(layer_names, successive_feature_maps):
  print(feature_map.shape)
  if len(feature_map.shape) == 4:

    # Plot Feature maps for the conv / maxpool layers, not the fully-connected layers

    n_features = feature_map.shape[-1]  # number of features in the feature map
    size       = feature_map.shape[ 1]  # feature map shape (1, size, size, n_features)

    # We will tile our images in this matrix
    display_grid = np.zeros((size, size * n_features))

    # Postprocess the feature to be visually palatable
    for i in range(n_features):
      x  = feature_map[0, :, :, i]
      x -= x.mean()
      x /= x.std ()
      x *=  64
      x += 128
      x  = np.clip(x, 0, 255).astype('uint8')
      # Tile each filter into a horizontal grid
      display_grid[:, i * size : (i + 1) * size] = x
# Display the grid
    scale = 20. / n_features
    plt.figure( figsize=(scale * n_features, scale) )
    plt.title ( layer_name )
    plt.grid  ( False )
    plt.imshow( display_grid, aspect='auto', cmap='viridis' )

"""## Evaluating Model Performance on Test Data"""

testg = ImageDataGenerator(rescale=None)
test_gen = testg.flow_from_directory(
  test_path,
  target_size=IMAGE_SIZE,
  shuffle=False,
)
print(test_gen.class_indices)

# Evaluate on Validation data
scores = model.evaluate(test_gen)
print("%s%s: %.2f%%" % ("evaluate ",model.metrics_names[1], scores[1]*100))

!pip install visualkeras

!pip3 install keras-visualizer

# !pip install graphviz

from keras.utils.vis_utils import plot_model
plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

from keras_visualizer import visualizer

import visualkeras

visualkeras.layered_view(model, scale_xy=1, scale_z=0.001, max_z=0.001,legend=True,to_file='model_layered.png').show() # write and show



#PRINT ALL LAYER NAMES FOR CAM
for idx in range(len(model.layers)):
  print(model.get_layer(index = idx).name)

import numpy as np
import tensorflow as tf
from tensorflow import keras

# Display
from IPython.display import Image, display
import matplotlib.pyplot as plt
import matplotlib.cm as cm

model_builder = model
img_size = (224,224)

last_conv_layer_name = "BlockGroup5__block_0__act_2"
# The local path to our target image
img_path='/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/test/0/bowel_1_score_0-0_00000024.jpg' #healthy

"""### Functions for Generating Grad-CAM Heatmap"""

def get_img_array(img_path, size):
    img = keras.preprocessing.image.load_img(img_path, target_size=size)
    # `array` is a float32 Numpy array of shape (299, 299, 3)
    array = keras.preprocessing.image.img_to_array(img)
    # We add a dimension to transform our array into a "batch"
    array = np.expand_dims(array, axis=0)
    return array


def make_gradcam_heatmap(img_array, model, last_conv_layer_name, pred_index=None):
    # First, we create a model that maps the input image to the activations
    # of the last conv layer as well as the output predictions
    grad_model = tf.keras.models.Model(
        [model.inputs], [model.get_layer(last_conv_layer_name).output, model.output]
    )

    # Then, we compute the gradient of the top predicted class for our input image
    # with respect to the activations of the last conv layer
    with tf.GradientTape() as tape:
        last_conv_layer_output, preds = grad_model(img_array)
        if pred_index is None:
            pred_index = tf.argmax(preds[0])
        class_channel = preds[:, pred_index]

    # This is the gradient of the output neuron (top predicted or chosen)
    # with regard to the output feature map of the last conv layer
    grads = tape.gradient(class_channel, last_conv_layer_output)

    # This is a vector where each entry is the mean intensity of the gradient
    # over a specific feature map channel
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # We multiply each channel in the feature map array
    # by "how important this channel is" with regard to the top predicted class
    # then sum all the channels to obtain the heatmap class activation
    last_conv_layer_output = last_conv_layer_output[0]
    heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    # For visualization purpose, we will also normalize the heatmap between 0 & 1
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()

img = load_img('/workspace/Tanisha/Boston_Scoring/Dataset/nerthus-dataset-frames/test/0/bowel_1_score_0-0_00000024.jpg')

img

# img.save('lime_shap_gradcam_test_1_bowel_10_score_1-0_00000007.jpg')

# Prepare image
img_array = get_img_array(img_path, size=img_size)


# Remove last layer's softmax
model.layers[-1].activation = None

# Print what the top predicted class is
preds = model.predict(img_array)
#print("Predicted:", decode_predictions(preds, top=1)[0])

# Generate class activation heatmap
heatmap = make_gradcam_heatmap(img_array, model, last_conv_layer_name)

# Display heatmap
plt.style.use('dark_background')
plt.matshow(heatmap)
plt.show()

"""### Saving and Displaying Grad-CAM"""

def save_and_display_gradcam(img_path, heatmap, cam_path, alpha=0.9):
    # Load the original image
    img = keras.preprocessing.image.load_img(img_path)
    img = keras.preprocessing.image.img_to_array(img)

    # Rescale heatmap to a range 0-255
    heatmap = np.uint8(255 * heatmap)

    # Use jet colormap to colorize heatmap
    jet = cm.get_cmap("jet")

    # Use RGB values of the colormap
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]

    # Create an image with RGB colorized heatmap
    jet_heatmap = keras.preprocessing.image.array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = keras.preprocessing.image.img_to_array(jet_heatmap)

    # Superimpose the heatmap on original image
    superimposed_img = jet_heatmap * alpha + img
    superimposed_img = keras.preprocessing.image.array_to_img(superimposed_img)

    # Save the superimposed image
    superimposed_img.save(cam_path)
    # Display Grad CAM
    display(Image(cam_path))


save_and_display_gradcam(img_path, heatmap, "gradcam_101.png")

def save_and_display_gradcam(img_path, heatmap, cam_path, alpha=0.9):
    # Load the original image
    img = keras.preprocessing.image.load_img(img_path)
    img = keras.preprocessing.image.img_to_array(img)

    # Rescale heatmap to a range 0-255
    heatmap = np.uint8(255 * heatmap)

    # Use jet colormap to colorize heatmap
    jet = cm.get_cmap("jet")

    # Use RGB values of the colormap
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]

    # Create an image with RGB colorized heatmap
    jet_heatmap = keras.preprocessing.image.array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = keras.preprocessing.image.img_to_array(jet_heatmap)

    # Superimpose the heatmap on original image
    superimposed_img = jet_heatmap * alpha + img
    superimposed_img = keras.preprocessing.image.array_to_img(superimposed_img)

    # Save the superimposed image
    superimposed_img.save(cam_path)
    # Display Grad CAM
    display(Image(cam_path))


save_and_display_gradcam(img_path, heatmap, "cam1.png")

!pip install shap==0.40.0

# !pip install numpy==1.24.2
# !pip install "numpy<1.24.0"

import numpy
print(numpy.__version__)

import numpy
print(numpy.__version__)

import math
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import shap

# !pip install shap
from skimage.segmentation import slic
from matplotlib.colors import LinearSegmentedColormap
from tensorflow.keras.models import Model

IMG_COUNT = 100
IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_CHANNELS = 3
IMG_SHAPE = (IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)

"""###  Image Loader Class for Preprocessing and Loading Images"""

from skimage.io import imread
from skimage.transform import resize
import numpy as np

class Loader:

    IMG_WIDTH = 224
    IMG_HEIGHT = 224
    IMG_CHANNEL = 3

    def preprocess_image(self, path: str):
        x = imread(path)
        x = resize(x, (Loader.IMG_WIDTH, Loader.IMG_HEIGHT)) * 255
        return x

    def load_sample(self, size: int):
        with open("/workspace/Tanisha/Boston_Scoring/Resnet50/imgs.txt", "r") as f:
            images_paths = f.read().split('\n')
            dataset = np.ndarray(shape=(size, Loader.IMG_WIDTH, Loader.IMG_HEIGHT, Loader.IMG_CHANNEL), dtype=np.float32)
            for index, images_path in enumerate(images_paths[:size]):
                dataset[index] = self.preprocess_image(images_path)
        return dataset

!pwd

!cd ..

!cd ..

!cd ..

!pwd

loader = Loader()
data = loader.load_sample(14)
data = preprocess_input(data)
data.shape

image_example = data[8]

"""### Image Masking Function"""

def mask_image(
    zs: np.array,
    segmentation: np.array,
    image: np.array,
    background: Optional[int] = None
) -> np.array:
    if background is None:
        background = image.mean((0,1))
    out = np.zeros((zs.shape[0], image.shape[0], image.shape[1], image.shape[2]))
    for i in range(zs.shape[0]):
        out[i,:,:,:] = image
        for j in range(zs.shape[1]):
            if zs[i,j] == 0:
                out[i][segmentation == j,:] = background
    return out

def fill_segmentation(values: np.array, segmentation_lut: np.array) -> np.array:
    out = np.zeros(segmentation_lut.shape)
    for i in range(values.shape[0]):
        out[segmentation_lut == i] = values[i]
    return out
def get_colormap() -> LinearSegmentedColormap:
    blue = (22/255, 134/255, 229/255)
    blue_shades = [(*blue, alpha) for alpha in np.linspace(1, 0, 100)]
    red = (254/255 ,0/255, 86/255)
    red_shades = [(*red, alpha) for alpha in np.linspace(0, 1, 100)]
    return LinearSegmentedColormap.from_list("shap", blue_shades + red_shades)

def plot_shap_top_explanations(
    model: Model,
    image: np.array,
    class_names_mapping: Dict[int, str],
    top_preds_count: int = 3,
    fig_title: Optional[str] = None,
    fig_name: Optional[str] = None
) -> None:
    """
    A method that provides explanations for N top classes.
    :param model: Keras based Image Classification model
    :param image: Single image in the form of numpy array. Shape: [224, 224, 3]
    :param class_names_mapping: Dictionary that provides mapping between class inedex and name
    :param top_preds_count: Number of top predictions that we want to explain
    :param fig_title: Figure title
    :param fig_name: Output figure path
    :return:
    """

    image_columns = 4
    image_rows = math.ceil(top_preds_count / image_columns)

    segments_slic = slic(image, n_segments=100, compactness=30, sigma=3)

    def _h(z):
        return model.predict(mask_image(z, segments_slic, image, 255))
    explainer = shap.KernelExplainer(_h, np.zeros((1,100)))
    shap_values = explainer.shap_values(np.ones((1,100)), nsamples=1000)

    preds = model.predict(np.expand_dims(image, axis=0))
    top_preds_indexes = np.flip(np.argsort(preds))[0,:top_preds_count]
    top_preds_values = preds.take(top_preds_indexes)
    top_preds_names = np.vectorize(lambda x: class_names[x])(top_preds_indexes)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(image_rows, image_columns, figsize=(image_columns * 5, image_rows * 5))
    [ax.set_axis_off() for ax in axes.flat]

    max_val = np.max([np.max(np.abs(shap_values[i][:,:-1])) for i in range(len(shap_values))])
    color_map = get_colormap()

    for i, (index, value, name, ax) in \
        enumerate(zip(top_preds_indexes, top_preds_values, top_preds_names, axes.flat)):

        m = fill_segmentation(shap_values[index][0], segments_slic)
        subplot_title = "{}. class: {} pred: {:.3f}".format(i + 1, name, value)
        ax.imshow(image / 255)
        ax.imshow(m, cmap=color_map, vmin=-max_val, vmax=max_val)
        ax.set_title(subplot_title, pad=20,fontsize=16)

    if fig_title:
        fig.suptitle(fig_title, fontsize=30)
    if fig_name:
        plt.savefig(fig_name)
    plt.show()

image_example.shape

image_example=data[7]

class_names = {0:'BBPS 0', 1:'BBPS 1',2:'BBPS 2',3:'BBPS 3'}

plot_shap_top_explanations(model, image_example, class_names, top_preds_count=4,
                           fig_name="shap.svg")

!pip install lime==0.2.0.0

import lime
# print(lime.__version__)

from lime import lime_image
from lime.wrappers.scikit_image import SegmentationAlgorithm
from skimage.segmentation import mark_boundaries

image_example = data[7]

import math
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from lime import lime_image
from lime.wrappers.scikit_image import SegmentationAlgorithm
from skimage.segmentation import mark_boundaries

from skimage.segmentation import felzenszwalb, slic, quickshift, watershed
from skimage.segmentation import mark_boundaries
# from keras.models import Model


def plot_lime_top_explanations(
    model: Model,
    image: np.array,
    class_names_mapping: Dict[int, str],
    top_preds_count: int = 3,
    fig_title: Optional[str] = None,
    fig_name: Optional[str] = None
) -> None:
    """
    A method that provides explanations for N top classes.
    :param model: Keras based Image Classification model
    :param image: Single image in the form of numpy array. Shape: [224, 224, 3]
    :param class_names_mapping: Dictionary that provides mapping between class inedex and name
    :param top_preds_count: Number of top predictions that we want to explain
    :param fig_title: Figure title
    :param fig_name: Output figure path
    :return:
    """

    image_columns = 4
    image_rows = math.ceil(top_preds_count / image_columns)
    explainer = lime_image.LimeImageExplainer()
    explanation = explainer.explain_instance(
        image,
        classifier_fn = model.predict,
        top_labels=100,
        hide_color=0,
        num_samples=1000
    )

    preds = model.predict(np.expand_dims(image, axis=0))
    top_preds_indexes = np.flip(np.argsort(preds))[0,:top_preds_count]
    top_preds_values = preds.take(top_preds_indexes)
    top_preds_names = np.vectorize(lambda x: class_names[x])(top_preds_indexes)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(image_rows, image_columns, figsize=(image_columns * 5, image_rows * 5))
    [ax.set_axis_off() for ax in axes.flat]

    for i, (index, value, name, ax) in \
        enumerate(zip(top_preds_indexes, top_preds_values, top_preds_names, axes.flat)):

        temp, mask = explanation.get_image_and_mask(
            explanation.top_labels[i],
            positive_only=False,
            num_features=5,
            hide_rest=False
        )

        subplot_title = "{}. class: {} pred: {:.3f}".format(i + 1, name, value)
        ax.imshow(mark_boundaries(temp / 255, mask))
        ax.set_title(subplot_title, pad=20,fontsize=16)

    if fig_title:
        fig.suptitle(fig_title, fontsize=30)
    if fig_name:
        plt.tight_layout()  # Add this before saving
        plt.subplots_adjust(top=0.90)  # Adjust this value as needed
        plt.savefig(fig_name)
        plt.savefig(fig_name)
    plt.show()

# Commented out IPython magic to ensure Python compatibility.
# %%time
# class_names ={0:'BBPS 0', 1:'BBPS 1',2:'BBPS 2',3:'BBPS 3'}
# plot_lime_top_explanations(model, image_example, class_names, top_preds_count=4,fig_name="LIME.svg")































#

