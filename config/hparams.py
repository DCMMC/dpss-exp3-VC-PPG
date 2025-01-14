class Hparams:
    class Audio:
        num_mels = 80
        ppg_dim = 347
        num_freq = 1025  # cannot be too small
        min_mel_freq = 30.
        max_mel_freq = 7600.
        sample_rate = 16000
        frame_length_ms = 25
        frame_shift_ms = 10
        upper_f0 = 500.
        lower_f0 = 30.
        n_mfcc = 13
        preemphasize = 0.97
        min_level_db = -80.0
        ref_level_db = 20.0
        max_abs_value = 1.
        symmetric_specs = False
        griffin_lim_iters = 60
        power = 1.5
        center = True

    class CMU_Arctic:
        num_spk = 6
        spk_to_inds = ['awb', 'bdl', 'clb', 'jmk', 'rms', 'slt']

    class TrainToOne:
        dev_set_rate = 0.1
        test_set_rate = 0.05
        epochs = 60
        train_batch_size = 32
        test_batch_size = 8
        shuffle_buffer = 128
        shuffle = True
        learning_rate = 1e-3
        num_workers = 0

    class TrainToMany:
        dev_set_rate = 0.1
        test_set_rate = 0.05
        epochs = 50
        train_batch_size = 32
        test_batch_size = 32
        shuffle_buffer = 128
        shuffle = True
        learning_rate = 1e-3
        num_workers = 0

    class BLSTMConversionModel:
        lstm_hidden = 256

    class BLSTMToManyConversionModel:
        lstm_hidden = 256
        spk_embd_dim = 64

    class PPGExtractor:
        class CNNBLSTMClassifier:
            n_cnn = 3
            cnn_hidden = 256
            cnn_kernel = 3
            n_blstm = 2
            lstm_hidden = 128
            ckpt = './saved_models/librispeechASR.ckpt-113000'
