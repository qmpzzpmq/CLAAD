import numpy as np
import scipy
import torch
from Transform.AWGN import AWGN
from Transform.fade import fade
from Transform.freq_mask import freq_mask
from Transform.MelSpec import MelSpec
from Transform.pitch_shift import pitch_shift
from Transform.time_mask import time_mask
from Transform.time_shift import time_shift
from Transform.time_stretch import time_stretch

# from Dataset.data_loader import audiodir, MIMII


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def transform(y, sr=16000, mel=False):
    if not mel:
        trans_var = np.random.randint(0, 8)
        if trans_var == 6:  # Time Stretch
            S = time_stretch(y)
            cls = 6
            return S, cls

        elif trans_var == 7:  # Pitch Shift
            S = pitch_shift(y)
            cls = 7
            return S, cls

        elif trans_var == 0:  # Additive Noise
            S = AWGN(y)
            cls = 0
            return S, cls

        elif trans_var == 1:  # Fade In/Fade Out
            S = fade(y, sr)
            cls = 1
            return S, cls

        elif trans_var == 2:  # Frequency Masking
            S_dB = MelSpec(y, sr)
            S = freq_mask(S_dB)
            cls = 2
            return S, cls

        elif trans_var == 3:  # Time Masking
            S_dB = MelSpec(y, sr)
            if S_dB.dim() == 2:
                S_dB = S_dB.unsqueeze(0)
            S = time_mask(S_dB)
            cls = 3
            return S, cls

        elif trans_var == 4:  # Time Shift
            S = time_shift(y)
            cls = 4
            return S, cls

        else:  # Identity Transform
            S_dB = MelSpec(y, sr)
            cls = 5
            return S_dB, cls

    else:
        cls = 6
        S_dB = MelSpec(y, sr)
        return S_dB, cls


def apply_transform(train_features, train_labels, state=0):
    if state == 0:  # Training
        # batch_size = train_features.size()[0]
        # batch_size = 128
        batch_size = 2
        Train = torch.zeros((2 * batch_size, 1, 128, 313))
        Label_cls = torch.zeros(2 * batch_size)

        # for i in range(0, train_features.size()[0]):
        for i in range(0, batch_size):
            # y = train_features[i]
            y = train_features
            S1, cls1 = transform(y)
            Train[i, 0, :, :] = S1
            Label_cls[i] = cls1

            S2, cls2 = transform(y)
            Train[i + batch_size, 0, :, :] = S2
            Label_cls[i + batch_size] = cls2
        # Label = torch.cat((train_labels,train_labels),0)
        Label = Label_cls
    else:  # Test
        batch_size = train_features.size(0)
        Train = torch.zeros((batch_size, 1, 128, 313))
        for i in range(0, train_features.size()[0]):
            y = train_features[i]
            S, cls = transform(y, mel=True)
            Train[i, 0, :, :] = S
        Label = train_labels
    return Train, Label


def anomaly_score(z, v_mean, v_cov):
    return scipy.spatial.distance.mahalanobis(z, v_mean, v_cov)
