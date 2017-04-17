avrdude -U "lfuse:r:-:h" -U "hfuse:r:-:h" -U "efuse:r:-:h" -U "lock:r:-:h" -s -c usbasp -p m128 
avrdude -s -c usbasp -p m128 -U "flash:w:firmware\tester\build\ic-tester-main.hex:a"
