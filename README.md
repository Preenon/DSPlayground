# DSPlayground
A suite of educational tools and visualizers for digital signal processing concepts, currently written in Python. I would be pleased if this helps anyone reinforce their learning on DSP topics! Currently consists of the following tools:

## Tone Mixer
Generate and mix the four major waveforms (sine, square, triangle, sawtooth) at specified frequencies (in Hz) and hear the output signal, as well as view the associated plot in the time domain! You can also specify a downsampling rate and view the sampled plot, and view the signal in the frequency domain (via its FFT and PSD). WARNING: Ensure that the FFT size is the same as the mixer's sampling rate. Features an option to save signals as WAV files and plots as PNGs.

## Spectrum Analyzer
Visualize signals in real time with time, frequency, and spectrogram/waterfall graphics!  Admittedly, most of this tool's code is cribbed from the wonderful [PySDR](https://pysdr.org/) textbook (specifically from Section 22. Real-Time GUIs with PyQt), which I encourage you to check out. The original GUI supports the PlutoSDR, USRP, or simulation-only mode, but I extended it to include modes for microphone input ("mic") and loading in a WAV file as input ("file").

# Licensing
Tone Generator/Mixer is released under the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0), and Spectrum Analyzer is released under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 Unported License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

# Acknowledgements
* As previously mentioned, all the people who contributed to the PySDR textbook, led and authored by the illustrious Dr. Marc Lichtman from the University of Maryland. The link to the Github repository for code associated with the PySDR textbook can be found [here](https://github.com/777arc/PySDR).
* Dr. Meinard Müller from the International Audio Laboratories Erlangen, who has written Python notebooks for understanding music processing. His [explanation](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C0/C0.html) on signals and sampling helped with my implementation of plotting signals at downsampled rates.
Disclaimer: I am not affiliated with or endorsed by these people, I just think their work has been cool and helpful to my own.

# TODO/Goals
* Add more tools that showcase more DSP concepts (e.g. types of noise, modulation, aliasing, ADC and DAC, quantization, useful filters)
* Expand on the existing tools and their capabilities (e.g. ability to generate time-varying tones, spectrograms and periodograms, ability to load in WAV files for analysis in Tone Mixer)
* Take a crack at the "Waterfall x-axis doesn’t update when changing center frequency (PSD plot does though)" bug in the original Spectrum Analyzer
* Fix x-axis in the frequency and spectrogram graphs in Spectrum Analyzer so that it displays correct scale of frequencies in real time when using "mic" or "file" option (use Tone Mixer as workaround for now)
* See if it's possible to decouple the mixer sampling rate from FFT size somehow
* See if it's possible for Spectrum Analyzer to support dynamic playback of files (so you don't have to reload the script to select a new WAV file, you could instead initiate a file select from within the main GUI and use a play button to plot the analysis of the file as it would be heard in real-time instead of it currently looping indefinitely as it does now) 
* General cleaner and saner integration of UI elements in tools (I do not profess to be a Qt expert)
* See if it would be feasible/worthwhile to consolidate multiple tools together (so you could play real-time sounds in Spectrum Analyzer thanks to Tone Mixer), although licensing issues might get in the way of that

This is a personal project of mine, so don't expect updates or replies on a regular (or frequent) schedule. However, absolutely feel free to use the code and expand on it, make your own forks (although watch the licenses), and shoot me requests, issues, or bug fixes!
