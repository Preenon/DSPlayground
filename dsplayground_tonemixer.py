import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from PyQt6.QtCore import Qt
from tones import SINE_WAVE, SQUARE_WAVE, TRIANGLE_WAVE, SAWTOOTH_WAVE
from tones.mixer import Mixer
import sounddevice as sd
from datetime import datetime


class ToneMixer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.mixed_samples = None
        self.sampled_signal = None
        self.mixer_sample_rate = 44100  # audio standard (Hz)
        self.amplitude = 0.5
        self.fft_size = self.mixer_sample_rate
        
        layout = QVBoxLayout()

        self.mixer_sampling_rate_input = self.create_text_input('Mixer Sampling Rate (Hz)', default=str(self.mixer_sample_rate))
        self.mixer_amplitude_input = self.create_text_input('Mixer Amplitude', default=str(self.amplitude))
        self.sine_freq_input = self.create_text_input('Sine Wave Frequency (Hz)', default='440')
        self.square_freq_input = self.create_text_input('Square Wave Frequency (Hz)')
        self.triangle_freq_input = self.create_text_input('Triangle Wave Frequency (Hz)')
        self.sawtooth_freq_input = self.create_text_input('Sawtooth Wave Frequency (Hz)')
        self.snr_db_input = self.create_text_input('SNR (dB)')
        self.noise_power_db_input = self.create_text_input('Noise Power (dB)')
        self.duration_input = self.create_text_input('Duration (seconds)', default='1')
        self.sampling_rate_input = self.create_text_input('Discrete Sampling Rate (Hz)')
        self.fft_size_input = self.create_text_input('FFT Size', default=str(self.fft_size))

        layout.addWidget(self.mixer_sampling_rate_input)
        layout.addWidget(self.mixer_amplitude_input)
        layout.addWidget(self.sine_freq_input)
        layout.addWidget(self.square_freq_input)
        layout.addWidget(self.triangle_freq_input)
        layout.addWidget(self.sawtooth_freq_input)
        layout.addWidget(self.snr_db_input)
        layout.addWidget(self.noise_power_db_input)
        layout.addWidget(self.duration_input)
        layout.addWidget(self.sampling_rate_input)
        layout.addWidget(self.fft_size_input)

        self.save_plot_checkbox = {}
        self.save_sound_checkbox = QCheckBox("Save as WAV")

        self.add_button_with_checkbox(layout, "Play Sound", self.play_sound, self.save_sound_checkbox)
        self.add_button_with_checkbox(layout, "Plot Signal", self.plot_signal)
        self.add_button_with_checkbox(layout, "Plot Signal Power", self.plot_signal_power)
        self.add_button_with_checkbox(layout, "Sample and Plot Discrete Signal", self.sample_signal)
        self.add_button_with_checkbox(layout, "Plot FFT", self.plot_fft)
        self.add_button_with_checkbox(layout, "Plot PSD", self.plot_psd)

        self.setLayout(layout)

    def create_text_input(self, label_text, default=''):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        input_box = QLineEdit()
        input_box.setText(default)
        layout.addWidget(label)
        layout.addWidget(input_box)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def add_button_with_checkbox(self, layout, button_text, function, checkbox=None):
        button_layout = QHBoxLayout()
        button = QPushButton(button_text)
        button.clicked.connect(function)

        button_layout.addWidget(button)
        if checkbox is None:
            checkbox = QCheckBox("Save as PNG")
        button_layout.addWidget(checkbox)
        layout.addLayout(button_layout)

        self.save_plot_checkbox[button_text] = checkbox

    def at_most_one_noise(self):
        return not (self.get_input_text(self.snr_db_input) != 0 and self.get_input_text(self.noise_power_db_input) != 0)
    
    def play_sound(self):
        self.generate_signal(save_to_wav=self.save_sound_checkbox.isChecked())
        if self.mixed_samples is not None and self.at_most_one_noise():
            try: 
                sd.check_output_settings(samplerate=self.mixer_sample_rate) # check if output sound device supports sample rate
            except Exception as e:
                self.show_warning("Unsupported Sample Rate", str(e))
                return
            print("Playing the mixed signal...")
            sd.play(self.mixed_samples, self.mixer_sample_rate)
            sd.wait()
            print("Playback finished.")


    def plot_signal(self):
        self.generate_signal()
        if self.mixed_samples is not None and self.at_most_one_noise():
            plt.figure(figsize=(8, 2.2))
            
            # compute x-axis values
            duration = len(self.mixed_samples) / self.mixer_sample_rate  # total duration in seconds
            time_axis = [i / self.mixer_sample_rate for i in range(len(self.mixed_samples))]  # time in seconds
            
            max_frequency = max(self.get_input_text(self.sine_freq_input),
                                self.get_input_text(self.square_freq_input),
                                self.get_input_text(self.triangle_freq_input),
                                self.get_input_text(self.sawtooth_freq_input))

            # adjust visible interval inversely proportional to frequency
            if max_frequency > 0:
                visible_duration = 10 / max_frequency  # display ~10 cycles
            else:
                visible_duration = duration  # show full duration for zero frequency

            plt.plot(time_axis, self.mixed_samples, color='blue')
            plt.title('Mixed Signal')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid()

            # adjust axes dynamically
            plt.xlim(0, min(visible_duration, duration))  # limit to either the visible or full duration

            # get the y-axis limits for consistency
            y_min, y_max = min(self.mixed_samples), max(self.mixed_samples)
            plt.ylim(y_min * 1.1, y_max * 1.1)  # extend y-limits slightly for clarity

            plt.tight_layout()
            plt.show()
            if self.save_plot_checkbox["Plot Signal"].isChecked():
                filename = f"plot_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def plot_signal_power(self):
        self.generate_signal()
        if self.mixed_samples is not None and self.at_most_one_noise():
            plt.figure(figsize=(8, 2.2))
            
            # compute x-axis values
            duration = len(self.mixed_samples) / self.mixer_sample_rate  # total duration in seconds
            time_axis = [i / self.mixer_sample_rate for i in range(len(self.mixed_samples))]  # time in seconds
            
            max_frequency = max(self.get_input_text(self.sine_freq_input),
                                self.get_input_text(self.square_freq_input),
                                self.get_input_text(self.triangle_freq_input),
                                self.get_input_text(self.sawtooth_freq_input))

            # adjust visible interval inversely proportional to frequency
            if max_frequency > 0:
                visible_duration = 10 / max_frequency  # display ~10 cycles
            else:
                visible_duration = duration  # show full duration for zero frequency

            signal_power = self.mixed_samples ** 2 # convention is 1-ohm resistor
            signal_power_db = 10 * np.log10(signal_power)
            plt.plot(time_axis, signal_power_db, color='blue')
            plt.title('Signal Power in dB')
            plt.ylabel('Power (dB)')
            plt.xlabel('Time (s)')
            plt.grid()

            # adjust axes dynamically
            plt.xlim(0, min(visible_duration, duration))  # limit to either the visible or full duration

            y_max = max(signal_power_db)
            y_min = -60 # 1e-6x converted to dB, good enough approximation for -inf
            plt.ylim(y_min, y_max)
            
            plt.tight_layout()
            plt.show()
            if self.save_plot_checkbox["Plot Signal Power"].isChecked():
                filename = f"plot_signal_power_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def sample_signal(self):
        self.generate_signal()
        if self.mixed_samples is not None and self.at_most_one_noise():
            original_duration = len(self.mixed_samples) / self.mixer_sample_rate
            original_time = np.linspace(0, original_duration, len(self.mixed_samples))
            
            # get user-specified sampling rate
            new_sample_rate = self.get_input_text(self.sampling_rate_input)
            if new_sample_rate <= 0:
                self.show_warning('Invalid Sampling Rate', 'Sampling rate must be greater than 0.')
                return
            
            # perform equidistant sampling
            sampled_duration = self.get_input_text(self.duration_input)
            if sampled_duration <= 0:
                self.show_warning('Invalid Duration', 'Duration must be greater than 0.')
                return

            num_samples = int(new_sample_rate * sampled_duration)
            sampled_time = np.linspace(0, sampled_duration, num_samples)
            sampled_signal = np.interp(sampled_time, original_time, self.mixed_samples)

            self.plot_sampled_signal(original_time, sampled_time, sampled_signal)

    def plot_sampled_signal(self, original_time, sampled_time, sampled_signal):
        plt.figure(figsize=(8, 2.2))
        plt.plot(original_time, self.mixed_samples, 'k', linewidth=1, linestyle='dotted')
        plt.stem(sampled_time, sampled_signal, linefmt='r', markerfmt='ro', basefmt='None')
        
        plt.title(f'DT-Signal obtained by sampling with $F_s = {self.get_input_text(self.sampling_rate_input)}$ Hz')
        plt.xlabel('Time (seconds)')
        
        y_min, y_max = min(self.mixed_samples), max(self.mixed_samples)
        plt.ylim(y_min * 1.1, y_max * 1.1)

        max_frequency = max(self.get_input_text(self.sine_freq_input),
                            self.get_input_text(self.square_freq_input),
                            self.get_input_text(self.triangle_freq_input),
                            self.get_input_text(self.sawtooth_freq_input))
        
        if max_frequency > 0:
            visible_duration = 10 / max_frequency
        else:
            visible_duration = len(self.mixed_samples) / self.mixer_sample_rate

        plt.xlim(0, min(visible_duration, len(self.mixed_samples) / self.mixer_sample_rate))
        plt.tight_layout()
        plt.show()

        if self.save_plot_checkbox["Sample and Plot Discrete Signal"].isChecked():
            filename = f"sample_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename)
            print(f"Plot saved as {filename}")

    def plot_fft(self):
        self.generate_signal()
        if self.mixed_samples is not None and self.at_most_one_noise():

            # ensure FFT size matches the sample rate
            # TODO: sSee if it's possible to decouple the two
            if self.fft_size != self.mixer_sample_rate:
                self.show_warning(
                    "FFT Size Mismatch",
                    "The FFT size must match the sample rate. Please adjust your input. TODO: See if it's possible to decouple the two."
                )
                return
            
            fft_result = np.fft.fftshift(np.fft.fft(self.mixed_samples))
            mag = np.abs(fft_result)
            phase = np.angle(fft_result)
            freqs = np.linspace(-self.mixer_sample_rate / 2, self.mixer_sample_rate / 2, self.fft_size)

            plt.figure(figsize=(8, 4))
            plt.subplot(2, 1, 1)
            plt.plot(freqs, mag, '.-')
            plt.title('FFT Magnitude')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magnitude')

            plt.subplot(2, 1, 2)
            plt.plot(freqs, phase, '.-')
            plt.title('FFT Phase')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Phase')

            plt.tight_layout()
            plt.show()

            if self.save_plot_checkbox["Plot FFT"].isChecked():
                filename = f"plot_fft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def plot_psd(self):
        self.generate_signal()
        if self.mixed_samples is not None and self.at_most_one_noise():
            if self.fft_size != self.mixer_sample_rate:
                self.show_warning(
                    "FFT Size Mismatch",
                    "The FFT size must match the sample rate. Please adjust your input. TODO: See if it's possible to decouple the two."
                )
                return
            
            psd = np.abs(np.fft.fft(self.mixed_samples)) ** 2 / (self.fft_size * self.mixer_sample_rate)
            psd_log = 10.0 * np.log10(psd)
            psd_shifted = np.fft.fftshift(psd_log)

            freqs = np.linspace(-self.mixer_sample_rate / 2, self.mixer_sample_rate / 2, self.fft_size)

            plt.plot(freqs, psd_shifted, '.-')
            plt.title('Power Spectral Density')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magnitude (dB)')

            plt.tight_layout()
            plt.grid(True)
            plt.show()

            if self.save_plot_checkbox["Plot PSD"].isChecked():
                filename = f"plot_psd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def generate_signal(self, save_to_wav=False):
        sine_freq = self.get_input_text(self.sine_freq_input)
        square_freq = self.get_input_text(self.square_freq_input)
        triangle_freq = self.get_input_text(self.triangle_freq_input)
        sawtooth_freq = self.get_input_text(self.sawtooth_freq_input)
        duration = self.get_input_text(self.duration_input)
        self.mixer_sample_rate = int(self.get_input_text(self.mixer_sampling_rate_input))
        self.amplitude = float(self.get_input_text(self.mixer_amplitude_input))
        self.fft_size = int(self.get_input_text(self.fft_size_input))

        if duration <= 0:
            self.show_warning('Invalid Duration', 'Duration must be greater than 0.')
            return

        mixer = Mixer(self.mixer_sample_rate, self.amplitude)
        if sine_freq > 0:
            mixer.create_track(0, SINE_WAVE)
            mixer.add_tone(0, frequency=sine_freq, duration=duration)

        if square_freq > 0:
            mixer.create_track(1, SQUARE_WAVE)
            mixer.add_tone(1, frequency=square_freq, duration=duration)

        if triangle_freq > 0:
            mixer.create_track(2, TRIANGLE_WAVE)
            mixer.add_tone(2, frequency=triangle_freq, duration=duration)

        if sawtooth_freq > 0:
            mixer.create_track(3, SAWTOOTH_WAVE)
            mixer.add_tone(3, frequency=sawtooth_freq, duration=duration)

        self.mixed_samples = mixer.mix()
        self.mixed_samples = np.array(self.mixed_samples)

        snr_db = self.get_input_text(self.snr_db_input)
        noise_power_avg_db = self.get_input_text(self.noise_power_db_input)

        if snr_db != 0 and noise_power_avg_db != 0:
            self.show_warning("Input Error", "Specify only one: SNR or Noise Power (both in dB).")
            return

        if snr_db != 0:
            signal_power = self.mixed_samples ** 2 # Convention is 1-ohm resistor
            signal_power_avg = np.mean(signal_power)
            signal_power_avg_db = 10 * np.log10(signal_power_avg)
            noise_power_avg_db = signal_power_avg_db - snr_db
            noise_power_avg = 10 ** (noise_power_avg_db / 10)
        elif noise_power_avg_db != 0:
            noise_power_avg = 10 ** (noise_power_avg_db / 10)
        else:
            noise_power_avg = 0

        noise = np.random.normal(0, np.sqrt(noise_power_avg), len(self.mixed_samples))
        self.mixed_samples += noise

        if save_to_wav:
            filename = f"play_sound_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            mixer.write_wav(filename)
            print(f"Sound saved as {filename}")


    def get_input_text(self, input_widget):
        text = input_widget.findChild(QLineEdit).text().strip()
        return float(text) if text else 0.0

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ToneMixer()
    window.setWindowTitle('DSPlayground: Tone Mixer')
    window.show()
    sys.exit(app.exec())
