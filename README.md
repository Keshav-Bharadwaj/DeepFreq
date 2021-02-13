# Code and Pretrained Networks from <br>"Complex Learning for Super-Resolution Convolutional Networks in Multi-Static Radars"

This repository contains information, code and models from the paper [Complex Learning for Super-Resolution
Convolutional Networks in Multi-Static Radars] by Keshav Bharadwaj, [Steffen Schieler,](https://github.com/st0nedB/DeepFreq) and [Prof. Giovanni Del Galdo]. Please visit the [project webpage here](https://github.com/Keshav-Bharadwaj/DeepFreq/). 

## Code and Pre-trained Models

Please refer to [`requirements.txt`](requirements.txt) for required packages. 

### pre-trained models
The directory [`pretrained_models`](pretrained_models) contains the pretained models of Complex DeepFreq. 

### Example code for using Pre-Trained models

In [`Complex_DeepFreq.ipynb`](Complex_DeepFreq.ipynb), Complex DeepFreq is applied to different signals and the results are visualized. 


### Train

[`train.py`](train.py) provides the code for training a model from scratch. An example usage of the script with some options is given below:

```shell
python train.py \
	--n_training 200000 \
	--n_epochs_fr 200 \
	--n_epochs_fc 100 \
	--output_dir /checkpoint/experiment_name \
```

Please refer to the `argparse` module in [`train.py`](train.py) for additional training options.

### Test

[`test.py`](test.py) provides the script to bechmark the performance of DeepFreq against several baselines. An example usage of the script is provided below.


```shell
python test.py \
	--data_dir test_dataset/ \
  	--output_dir results/ \
  	--fr_path pretrained_models/DeepFreq/frequency_representation_module.pth \
  	--fc_path pretrained_models/DeepFreq/frequency_counting_module.pth \
  	--psnet_path pretrained_models/PSnet/psnet.pth \
	--psnet_fc_path pretrained_models/PSnet/frequency_counting_psnet.pth \
	--overwrite
```




### Generate test data

 [`generate_dataset.py`](`generate_dataset.py`) provides the code to generate data. An example usage is shown below:

```shell
python generate_dataset.py \
    	--output_dir my_testset/ \
    	--n_test 1000 \
	--signal_dimension 50 \
   	--minimum_separation 1. \
    	--dB 0 5 10 15 20 25 30 35 40 45 50 \
```

The particular instance of test data used in the original paper is available in the [`test_dataset`](test_dataset).

