import os
import torch
import numpy as np
import tensorflow as tf
import argparse


from models import BLSTMConversionModel, BLSTMResConversionModel
from config import Hparams
from utils import load_wav, _preemphasize, melspectrogram, logf0, wav2unnormalized_mfcc, \
    inv_mel_spectrogram, inv_preemphasize, save_wav, softmax, lf0_normailze
from models import CNNBLSTMClassifier


def main():
    hps = Hparams
    parser = argparse.ArgumentParser('VC inference')
    parser.add_argument('--src_wav', type=str, help='source wav file path')
    parser.add_argument('--ckpt', type=str, help='model ckpt path')
    parser.add_argument('--save_dir', type=str, help='synthesized wav save directory')
    parser.add_argument('--resnet', action='store_true', help='if enable resnet')
    args = parser.parse_args()
    # 0.
    src_wav_arr = load_wav(args.src_wav)
    pre_emphasized_wav = _preemphasize(src_wav_arr)
    # 1. extract ppgs
    ppg_extractor_hps = hps.PPGExtractor.CNNBLSTMClassifier
    mfcc_pl = tf.placeholder(dtype=tf.float32,
                             shape=[None, None, 3 * hps.Audio.n_mfcc],
                             name='mfcc_pl')

    ppg_extractor = CNNBLSTMClassifier(out_dims=hps.Audio.ppg_dim,
                                       n_cnn=ppg_extractor_hps.n_cnn,
                                       cnn_hidden=ppg_extractor_hps.cnn_hidden,
                                       cnn_kernel=ppg_extractor_hps.cnn_kernel,
                                       n_blstm=ppg_extractor_hps.n_blstm,
                                       lstm_hidden=ppg_extractor_hps.lstm_hidden)
    predicted_ppgs = ppg_extractor(inputs=mfcc_pl)['logits']
    # set up a session
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)
    sess.run(tf.global_variables_initializer())
    # load saved model
    saver = tf.train.Saver()
    print('Restoring ppgs extractor from {}'.format(ppg_extractor_hps.ckpt))
    saver.restore(sess, ppg_extractor_hps.ckpt)
    mfcc_feats = wav2unnormalized_mfcc(src_wav_arr)
    ppg = sess.run(predicted_ppgs,
                   feed_dict={mfcc_pl: np.expand_dims(mfcc_feats, axis=0)})
    sess.close()
    ppg = softmax(np.squeeze(ppg, axis=0))

    # 2. extract lf0, mel-spectrogram
    log_f0 = logf0(args.src_wav)
    log_f0 = lf0_normailze(log_f0)
    # mel-spectrogram is extracted for comparison
    mel_spec = melspectrogram(pre_emphasized_wav).astype(np.float32).T

    # 3. prepare inputs
    min_len = min(log_f0.shape[0], ppg.shape[0])
    vc_inputs = np.concatenate([ppg[:min_len, :], log_f0[:min_len, :]], axis=1)
    vc_inputs = np.expand_dims(vc_inputs, axis=1)  # [time, batch, dim]

    # 4. setup vc model and do the inference
    if not args.resnet:
        model = BLSTMConversionModel(in_channels=hps.Audio.ppg_dim + 2,
                                     out_channels=hps.Audio.num_mels,
                                     lstm_hidden=hps.BLSTMConversionModel.lstm_hidden)
    else:
        model = BLSTMResConversionModel(in_channels=hps.Audio.ppg_dim + 2,
                                     out_channels=hps.Audio.num_mels,
                                     lstm_hidden=hps.BLSTMConversionModel.lstm_hidden,
                                     other_params=hps.Audio.num_mels)
    device = torch.device('cpu')
    model.load_state_dict(torch.load(args.ckpt, map_location=device))
    model.eval()
    predicted_mels = model(torch.tensor(vc_inputs))
    predicted_mels = np.squeeze(predicted_mels.detach().numpy(), axis=1)

    # 5. synthesize wav
    synthesized_wav = inv_preemphasize(inv_mel_spectrogram(predicted_mels.T))
    resynthesized_wav = inv_preemphasize(inv_mel_spectrogram(mel_spec.T))
    ckpt_name = args.ckpt.split('/')[-1].split('.')[0]
    wav_name = args.src_wav.split('/')[-1].split('.')[0]
    save_wav(synthesized_wav, os.path.join(args.save_dir, '{}-{}-converted.wav'.format(wav_name, ckpt_name)))
    save_wav(resynthesized_wav, os.path.join(args.save_dir, '{}-{}-src-resyn.wav'.format(wav_name, ckpt_name)))
    return


if __name__ == '__main__':
    main()
