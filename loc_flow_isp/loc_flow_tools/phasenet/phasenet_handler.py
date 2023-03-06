import os
import pandas as pd
import numpy as np
import time as _time
import tensorflow as tf
from .data_reader import DataReader_pred
from .model import ModelConfig, UNet
from .postprocess import (extract_picks, extract_amplitude)
from ... import p_dir

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class Util:

    @staticmethod
    def convert2dataframe(path_project):
        project_converted = []
        _names = path_project.keys()

        for name in _names:
            for i in range(len(path_project[name])):
                project_converted.append({
                    'id': name,
                    'fname': path_project[name][i][0],
                    'stats': path_project[name][i][1]
                })

        return pd.DataFrame.from_dict(project_converted)

    @staticmethod
    def convert2real(picks):
        dates = picks['date'].unique()
        fnames = picks['fname'].unique()

        for date in dates:
            pickpath = os.path.join(p_dir, date)

            if not os.path.isdir(pickpath):
                try:
                    os.mkdir(pickpath)
                except OSError as e:
                    print(e)
        start = _time.time()

        for date in dates:
            pickpath = os.path.join(p_dir, date)
            for fname in fnames:
                fname_new = fname + '.txt'
                pickfile= os.path.join(pickpath, fname_new)

                savedata = picks[(picks['date'] == date) & (picks['fname'] == fname)]

                savedata = savedata.sort_values('tt')

                if len(savedata.index) > 0:
                    with open(pickfile, 'w') as f:
                        data_aux = savedata.to_string(header=False, index=False, columns=['tt', 'weight', 'amplitude'])
                        f.write(data_aux)

        print('TIME SAVING ALL FILES: ', _time.time() - start)

    @staticmethod
    def get_files(project):
        filename = []

        for i in range(len(project)):
            filename.append(project[i])

        return filename

    @staticmethod
    def split_picks(picks):
        print('get_picks')
        prob_threshold = 0 #0.5
        columns = ['date', 'fname', 'year', 'month', 'day', 'net', 'station', 'flag', 'tt',
                   'weight', 'amplitude', 'phase']
        split_picks_ = pd.DataFrame(columns=columns)

        stats = picks['stats']
        ppick_tmp = picks['p_idx']
        spick_tmp = picks['s_idx']
        pprob_tmp = picks['p_prob']
        sprob_tmp = picks['s_prob']

        if 'p_amp' in picks.columns:
            p_amp = picks['p_amp']
        else:
            p_amp = []

        if 's_amp' in picks.columns:
            s_amp = picks['s_amp']
        else:
            s_amp = []

        start = _time.time()

        for i in np.arange(0, len(ppick_tmp)):
            ppick = []
            spick = []
            pprob = []
            sprob = []
            pamp = []
            samp = []
            split_aux_p = []
            split_aux_s = []
            year = stats[i].starttime.year
            month = stats[i].starttime.month
            day = stats[i].starttime.day
            station = stats[i].station
            network = stats[i].network

            ss = stats[i].starttime.hour*3600 + stats[i].starttime.minute*60 + stats[i].starttime.second + \
                 stats[i].starttime.microsecond/1000000

            samplingrate = 1/stats[i].sampling_rate

            if len(ppick_tmp[i][0]) > 0:
                ppick_um = ppick_tmp[i][0][:]
                pprob_um = pprob_tmp[i][0][:]

                if len(p_amp) > 0:
                    pamp_um = p_amp[i][0][:]

                for j in np.arange(0, len(ppick_um)):
                    if ppick_um[j] != ',':
                        ppick.append(ppick_um[j])

                for j in np.arange(0, len(pprob_um)):
                    if pprob_um[j] != ',':
                        pprob.append(pprob_um[j])

                if len(p_amp) > 0:
                    for j in np.arange(0, len(pamp_um)):
                        if pamp_um[j] != ',':
                            pamp.append(pamp_um[j])

                for j in np.arange(0, len(pprob)):
                    if float(pprob[j]) >= prob_threshold:
                        fname = network + '.' + station + '.' + 'P'
                        tp = int(ppick[j])*samplingrate+ss
                        amp = float(pamp[j])*2080*25 if len(p_amp) > 0 else 0
                        split_aux_p.append([str(year)+str(month)+str(day), fname, year, month, day, network, station,
                                             1, tp, pprob[j], amp, "P"])
                        #/1000000000

                split_picks_ = pd.concat([split_picks_, pd.DataFrame(split_aux_p, columns=columns)], ignore_index=True)

            if len(spick_tmp[i][0]) > 0:
                spick_um = spick_tmp[i][0][:]
                sprob_um = sprob_tmp[i][0][:]

                if len(s_amp) > 0:
                    samp_um = s_amp[i][0][:]

                for j in np.arange(0, len(spick_um)):
                    if spick_um[j] != ',':
                        spick.append(spick_um[j])

                for j in np.arange(0, len(sprob_um)):
                    if sprob_um[j] != ',':
                        sprob.append(sprob_um[j])

                if len(s_amp) > 0:
                    for j in np.arange(0, len(samp_um)):
                        if samp_um[j] != ',':
                            samp.append(samp_um[j])

                for j in np.arange(0, len(sprob)):
                    if float(sprob[j]) >= prob_threshold:
                        fname = network + '.' + station + '.' + 'S'
                        tp = int(spick[j])*samplingrate+ss
                        amp = float(samp[j]) * 2080 * 25 if len(s_amp) > 0 else 0
                        split_aux_s.append([str(year)+str(month)+str(day), fname, year, month, day, network, station, 1,
                                            tp, sprob[j], amp, "S"])
                        #/1000000000

                split_picks_ = pd.concat([split_picks_, pd.DataFrame(split_aux_s, columns=columns)], ignore_index = True)

        print('LEN TOTAL: ', len(ppick_tmp))
        print('START: ', _time.time()-start)

        return split_picks_


class Config:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class PhasenetISP:
    def __init__(self, files, batch_size=3, modelpath="", filepath="", hdf5_file="", hdf5_group="data",
                 resultpath="results", result_fname="picks", highpass_filter=0.5, min_p_prob=0.3, min_s_prob=0.3,
                 min_peak_distance=50, amplitude=False, format="mseed", stations="", plot_figure=False, save_prob=False,
                 time_lm=1, time_rm=4):

        files_ = Util.convert2dataframe(files)

        self.batch_size = batch_size
        self.highpass_filter = highpass_filter
        self.min_p_prob = min_p_prob
        self.min_s_prob = min_s_prob
        self.min_peak_distance = min_peak_distance
        self.time_lm = time_lm
        self.time_rm = time_rm

        self.model_path = modelpath
        self.file_path = filepath
        self.hdf5_group = hdf5_group
        self.result_path = resultpath

        self.project = files_
        self.files = files_['fname']
        self.hdf5_file = hdf5_file
        self.result_fname = result_fname
        self.stations = stations

        self.format = format

        self.amplitude = amplitude
        self.plot_figure = plot_figure
        self.save_prob = save_prob

        self.data_reader = None

    def phasenet(self):
        with tf.compat.v1.name_scope('create_inputs'):
            self.data_reader = DataReader_pred(
                format=self.format,
                data_dir=self.file_path,
                data_list=self.files,
                hdf5_file=self.hdf5_file,
                hdf5_group=self.hdf5_group,
                amplitude=self.amplitude,
                highpass_filter=self.highpass_filter
            )

        return self.predict()

    def predict(self):
        batch_size = self.batch_size
        dataset = self.data_reader.dataset(batch_size)
        batch = tf.compat.v1.data.make_one_shot_iterator(dataset).get_next()

        config = ModelConfig(X_shape=self.data_reader.X_shape)

        model = UNet(config=config, input_batch=batch, mode='pred')

        session_config = tf.compat.v1.ConfigProto()
        session_config.gpu_options.allow_growth = True

        with tf.compat.v1.Session(config=session_config) as session:
            picks = []
            amplitudes = [] if self.amplitude else None

            saver = tf.compat.v1.train.Saver(tf.compat.v1.global_variables(), max_to_keep=5)
            init = tf.compat.v1.global_variables_initializer()
            session.run(init)

            latest_check_point = tf.train.latest_checkpoint(self.model_path)
            saver.restore(session, latest_check_point)

            for _ in range(0, self.data_reader.num_data, batch_size):
                if self.amplitude:
                    pred_batch, X_batch, amplitude_batch, file_batch, t0_batch, station_batch = session.run(
                        [model.preds, batch[0], batch[1], batch[2], batch[3], batch[4]],
                        feed_dict={model.drop_rate: 0, model.is_training: False},
                    )
                else:
                    pred_batch, X_batch, file_batch, t0_batch, station_batch = session.run(
                        [model.preds, batch[0], batch[1], batch[2], batch[3]],
                        feed_dict={model.drop_rate: 0, model.is_training: False},
                    )

                waveforms = None

                if self.amplitude:
                    waveforms = amplitude_batch

                picks_aux = extract_picks(
                    preds=pred_batch,
                    fnames=file_batch,
                    station_ids=station_batch,
                    t0=t0_batch,
                    config={'min_p_prob': self.min_p_prob,
                            'min_s_prob': self.min_s_prob,
                            'min_peak_distance': self.min_peak_distance})

                picks.extend(picks_aux)

                if self.amplitude:
                    amplitudes_aux = extract_amplitude(amplitude_batch, picks_aux)
                    amplitudes.extend(amplitudes_aux)

            picks_ = self.picks2df(picks, amplitudes)
            return self.project.merge(picks_, how='inner', on='fname')


    @staticmethod
    def picks2df(picks, amplitudes):
        int2s = lambda x: ",".join(["[" + ",".join(map(str, i)) + "]" for i in x])
        flt2s = lambda x: ",".join(["[" + ",".join(map("{:0.3f}".format, i)) + "]" for i in x])
        sci2s = lambda x: ",".join(["[" + ",".join(map("{:0.3e}".format, i)) + "]" for i in x])

        if amplitudes is None:
            _picks = pd.DataFrame(picks)

        else:
            _picks = pd.DataFrame(picks)
            _amplitudes = pd.DataFrame(amplitudes)
            _picks[['p_amp', 's_amp']] = ["", ""]

            _picks = _picks.assign(p_amp=_amplitudes['p_amp'], s_amp=_amplitudes['s_amp'])

        return _picks
