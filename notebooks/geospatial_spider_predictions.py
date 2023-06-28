# -*- coding: utf-8 -*-
"""Geospatial spider predictions.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ccUxlNwYiWA0MzJ33Wfs33J-aCUwuFbl
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error

import matplotlib.pyplot as plt
import seaborn as sns

def read_data(path):
    df = pd.read_parquet(path)
    return df

data = read_data('final_dataset.parquet')

data = data.drop(columns = ['kingdom', 'class', 'Unnamed: 0', 'phylum', 'order', 'scientificName', 'verbatimScientificName', 'countryCode'])


alpine_Cantons = ['Valais', 'Graubünden', 'Uri', 'Bern', 'Ticino', 'Schwyz', 'Glarus', 'Obwalden', 'Nidwalden', 'Appenzell', 'St. Gallen']
plateau_Cantons = ['Zürich', 'Aargau', 'Luzern', 'Thurgau', 'Solothurn', 'Basel', 'Schaffhausen', 'Zug', 'Fribourg', 'Genève']
jura_Cantons = ['Neuchâtel', 'Jura', 'Vaud']

# Create a mapping dictionary for each type
mapping = {}
for canton in alpine_Cantons:
    mapping[canton] = 'Alpine'
for canton in plateau_Cantons:
    mapping[canton] = 'Plateau'
for canton in jura_Cantons:
    mapping[canton] = 'Jura'

# Map the types to a new 'Type' column in the DataFrame
data['Landscape'] = data['stateProvince'].map(mapping)
data.info()

data['day'] = 1
data['date'] = pd.to_datetime(data[['Year', 'Month', 'day']])

data = data.replace({'PRESENT': 1})
data2 = data.sort_values('Year', ascending=True)
final_data = data2.groupby(['stateProvince', 'species','date','decimalLatitude','decimalLongitude','Landscape', 'elevation', 'taxonRank']).agg({'occurrenceStatus' : 'sum', 'Temperature' : 'mean', 'Precipitation': 'mean'}).reset_index()
final_data.info()

final_data.head()

# encoding the species this way because one hot encoder will create hundreds of columns which will impact the prediction
label_encoder = LabelEncoder()
label_encoder.fit(final_data['species'])
encoded_column = label_encoder.transform(final_data['species'])
final_data['species'] = encoded_column

"""## Split Dataset into train and test Datsets

We split the dataset into a standard 70:30 train-test split using stratified sampling to keep the distributions of classes similar in train and test datasets
"""

X = final_data.drop(columns=['occurrenceStatus'])
y = final_data['occurrenceStatus']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_train.shape, X_test.shape

"""## Separate categorical and numeric columns

We will need to treat these features separately just like before
"""

final_data['taxonRank'].unique()

categorical_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
numeric_features = X_train.select_dtypes(include=['int', 'float']).columns.tolist()

categorical_features, numeric_features

"""## Define Categorical Transformer Pipeline

Consists of the series of steps needed to tranform the categorical features.
- One-hot encoder to get dummy variables

## Define Numeric Transformer Pipeline

Consists of the series of steps needed to tranform the numeric features.
- Standard Scaler to scale the numeric features
"""

categorical_transformer = Pipeline(steps=[
                                          ("onehot", OneHotEncoder())
                                          ])
numeric_transformer = Pipeline(steps=[
                                      ("scaler", StandardScaler())
                                      ])

# Column Transformer Pipeline for preprocessing
preprocessor = ColumnTransformer(transformers=[
                                               ("num", numeric_transformer,
                                                       numeric_features),
                                               ("cat", categorical_transformer,
                                                       categorical_features)
                                               ])

model = RandomForestRegressor(n_estimators = 10, random_state = 42)
pipeline_rf = Pipeline([("pre_process", preprocessor),
                         ("model", model)])
pipeline_rf.fit(X_train, y_train)

y_pred = pipeline_rf.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("MSE:", mse)
print("R^2:", r2)

# Retrieve the feature importances
importances = pipeline_rf.named_steps['model'].feature_importances_

# Retrieve the one-hot encoder
one_hot_encoder = pipeline_rf.named_steps['pre_process'].transformers_[1][1].named_steps['onehot']

# Retrieve the transformed feature names from the one-hot encoder
encoded_feature_names = one_hot_encoder.get_feature_names_out(categorical_features)

# Combine the numeric feature names with the encoded feature names
feature_names = numeric_features + encoded_feature_names.tolist()

# Check if the lengths of feature_names and importances match
if len(feature_names) != len(importances):
    raise ValueError("Number of feature names does not match the number of importances.")

# Create a DataFrame to store the feature importances
feature_importances = pd.DataFrame({'Feature': feature_names, 'Importance': importances})

# Sort the feature importances in descending order
feature_importances = feature_importances.sort_values(by='Importance', ascending=False)
feature_importances

# let's try to drop the canton and check if our prediction improves
X = final_data.drop(columns=['occurrenceStatus', 'stateProvince', 'decimalLatitude', 'decimalLongitude'])
y = final_data['occurrenceStatus']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

categorical_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()
numeric_features = X_train.select_dtypes(include=['int', 'float']).columns.tolist()

categorical_transformer = Pipeline(steps=[
                                          ("onehot", OneHotEncoder())
                                          ])
numeric_transformer = Pipeline(steps=[
                                      ("scaler", StandardScaler())
                                      ])

# Column Transformer Pipeline for preprocessing
preprocessor = ColumnTransformer(transformers=[
                                               ("num", numeric_transformer,
                                                       numeric_features),
                                               ("cat", categorical_transformer,
                                                       categorical_features)
                                               ])

model = RandomForestRegressor(n_estimators = 10, random_state = 42)
pipeline_rf = Pipeline([("pre_process", preprocessor),
                         ("model", model)])
pipeline_rf.fit(X_train, y_train)

y_pred = pipeline_rf.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("MSE:", mse)
print("R^2:", r2)