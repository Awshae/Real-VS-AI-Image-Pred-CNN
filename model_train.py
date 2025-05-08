import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt

#GPU Check
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
    print("Using GPU:", physical_devices)
else:
    print("Running on CPU")

#Paths
train_dir = "..CNN/test"
test_dir = "..CNN/train"

#Hyperparameters
IMG_SIZE = (160, 160)
BATCH_SIZE = 32
EPOCHS = 30


#Data Generators
train_gen = ImageDataGenerator(
    rescale=1./255,
    horizontal_flip=True,
    zoom_range=0.2,
    rotation_range=15
)

test_gen = ImageDataGenerator(rescale=1./255)

train_ds = train_gen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

test_ds = test_gen.flow_from_directory(
    test_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary',
    shuffle=False
)

#Load base model
base_model = MobileNetV2(input_shape=(160,160,3), include_top=False, weights='imagenet')

base_model.trainable = True

#Freeze all layers except the last 30
for layer in base_model.layers[:-30]:
    layer.trainable = False

#Build model
model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])


#Compile
model.compile(optimizer=tf.keras.optimizers.Adam(1e-4),
              loss='binary_crossentropy',
              metrics=['accuracy'])

#Callbacks
early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

#Train
history = model.fit(train_ds, validation_data=test_ds, epochs=EPOCHS, callbacks=[early_stop])

#Save model
model.save("model.h5")

#Plot accuracy
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Training vs Validation Accuracy')
plt.legend()
plt.grid(True)
plt.show()

#Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(5, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=test_ds.class_indices.keys(), 
            yticklabels=test_ds.class_indices.keys())
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()


#Evaluation
y_true = test_ds.classes
y_pred = (model.predict(test_ds) > 0.5).astype(int).flatten()
print(classification_report(y_true, y_pred, target_names=test_ds.class_indices.keys()))
