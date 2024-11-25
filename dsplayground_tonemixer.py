import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
from PyQt6.QtCore import Qt
from tones import SINE_WAVE, SQUARE_WAVE, TRIANGLE_WAVE, SAWTOOTH_WAVE
from tones.mixer import Mixer
import sounddevice as sd
from datetime import datetime

default_sample_rate = 44100  # Hz
default_amplitude = 0.5


class ToneMixer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.mixed_samples = None
        self.sampled_signal = None

        layout = QVBoxLayout()

        self.mixer_sampling_rate_input = self.create_text_input('Mixer Sampling Rate (Hz)', default=str(default_sample_rate))
        self.mixer_amplitude_input = self.create_text_input('Mixer Amplitude', default=str(default_amplitude))
        self.sine_freq_input = self.create_text_input('Sine Wave Frequency (Hz)')
        self.square_freq_input = self.create_text_input('Square Wave Frequency (Hz)')
        self.triangle_freq_input = self.create_text_input('Triangle Wave Frequency (Hz)')
        self.sawtooth_freq_input = self.create_text_input('Sawtooth Wave Frequency (Hz)')
        self.duration_input = self.create_text_input('Duration (seconds)')
        self.sampling_rate_input = self.create_text_input('Discrete Sampling Rate (Hz)')
        self.fft_size_input = self.create_text_input('FFT Size')

        layout.addWidget(self.mixer_sampling_rate_input)
        layout.addWidget(self.mixer_amplitude_input)
        layout.addWidget(self.sine_freq_input)
        layout.addWidget(self.square_freq_input)
        layout.addWidget(self.triangle_freq_input)
        layout.addWidget(self.sawtooth_freq_input)
        layout.addWidget(self.duration_input)
        layout.addWidget(self.sampling_rate_input)
        layout.addWidget(self.fft_size_input)

        self.save_plot_checkbox = {}
        self.save_sound_checkbox = QCheckBox("Save as WAV")

        self.add_button_with_checkbox(layout, "Play Sound", self.play_sound, self.save_sound_checkbox)
        self.add_button_with_checkbox(layout, "Plot Signal", self.plot_signal)
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

    def play_sound(self):
        self.generate_signal(save_to_wav=self.save_sound_checkbox.isChecked())
        if self.mixed_samples is not None:
            try: 
                sd.check_output_settings(samplerate=self.sample_rate) # Check if output sound device supports sample rate
            except Exception as e:
                self.show_warning("Unsupported Sample Rate", str(e))
                return
            print("Playing the mixed signal...")
            sd.play(self.mixed_samples, self.sample_rate)
            sd.wait()
            print("Playback finished.")


    def plot_signal(self):
        self.generate_signal()
        if self.mixed_samples is not None:
            plt.figure(figsize=(8, 2.2))
            samples = self.mixed_samples
            sample_rate = self.sample_rate
            duration = len(samples) / sample_rate
            time_axis = np.linspace(0, duration, len(samples))

            plt.plot(time_axis, samples, color='blue')
            plt.title('Mixed Signal')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid()

            y_min, y_max = min(samples), max(samples)
            plt.ylim(y_min * 1.1, y_max * 1.1)
            plt.tight_layout()
            plt.show()

            if self.save_plot_checkbox["Plot Signal"].isChecked():
                filename = f"plot_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def sample_signal(self):
        self.generate_signal()
        if self.mixed_samples is not None:
            original_duration = len(self.mixed_samples) / self.sample_rate
            original_time = np.linspace(0, original_duration, len(self.mixed_samples))
            
            new_sample_rate = self.get_input_text(self.sampling_rate_input)
            if new_sample_rate <= 0:
                self.show_warning('Invalid Sampling Rate', 'Sampling rate must be greater than 0.')
                return
            
            sampled_duration = self.get_input_text(self.duration_input)
            if sampled_duration <= 0:
                self.show_warning('Invalid Duration', 'Duration must be greater than 0.')
                return

            num_samples = int(new_sample_rate * sampled_duration)
            sampled_time = np.linspace(0, sampled_duration, num_samples)
            sampled_signal = np.interp(sampled_time, original_time, self.mixed_samples)

            self.sampled_signal = sampled_signal

            plt.figure(figsize=(8, 2.2))
            plt.plot(original_time, self.mixed_samples, 'k', linewidth=1, linestyle='dotted')
            plt.stem(sampled_time, sampled_signal, linefmt='r', markerfmt='ro', basefmt='None')
            
            plt.title(f'DT-Signal obtained by sampling with $F_s = {new_sample_rate}$ Hz')
            plt.xlabel('Time (seconds)')
            
            y_min, y_max = min(self.mixed_samples), max(self.mixed_samples)
            plt.ylim(y_min * 1.1, y_max * 1.1)
            plt.tight_layout()
            plt.show()

            if self.save_plot_checkbox["Sample and Plot Discrete Signal"].isChecked():
                filename = f"sample_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(filename)
                print(f"Plot saved as {filename}")

    def plot_fft(self):
        self.generate_signal()
        if self.mixed_samples is not None:

            # Ensure FFT size matches the sample rate
            # TODO: See if it's possible to decouple the two
            if self.fft_size != self.sample_rate:
                self.show_warning(
                    "FFT Size Mismatch",
                    "The FFT size must match the sample rate. Please adjust your input. TODO: See if it's possible to decouple the two."
                )
                return
            
            fft_result = np.fft.fftshift(np.fft.fft(self.mixed_samples))
            mag = np.abs(fft_result)
            phase = np.angle(fft_result)
            freqs = np.linspace(-self.sample_rate / 2, self.sample_rate / 2, self.fft_size)

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
        if self.mixed_samples is not None:

            # Ensure FFT size matches the sample rate
            # TODO: See if it's possible to decouple the two
            if self.fft_size != self.sample_rate:
                self.show_warning(
                    "FFT Size Mismatch",
                    "The FFT size must match the sample rate. Please adjust your input. TODO: See if it's possible to decouple the two."
                )
                return
            
            psd = np.abs(np.fft.fft(self.mixed_samples)) ** 2 / (self.fft_size * self.sample_rate)
            psd_log = 10.0 * np.log10(psd)
            psd_shifted = np.fft.fftshift(psd_log)

            freqs = np.linspace(-self.sample_rate / 2, self.sample_rate / 2, self.fft_size)

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
        self.sample_rate = int(self.get_input_text(self.mixer_sampling_rate_input) or default_sample_rate)
        amplitude = float(self.get_input_text(self.mixer_amplitude_input) or default_amplitude)
        self.fft_size = int(self.get_input_text(self.fft_size_input))

        if duration <= 0:
            self.show_warning('Invalid Duration', 'Duration must be greater than 0.')
            return

        mixer = Mixer(self.sample_rate, amplitude)
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