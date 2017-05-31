# survey_data_augmenter

Module to augment CSV survey data with duration and banned pesticides use.

Libraries:
```
pip3 install fuzzywuzzy[speedup]
pip3 install pandas
```

Use:
```
from survey_data_augmenter import augment
augment('path_to_data.csv')
```
