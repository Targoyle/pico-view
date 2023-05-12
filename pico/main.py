from machine import ADC, Pin

adc_0 = ADC(0)
adc_1 = ADC(1)
adc_2 = ADC(2)
adc_3 = ADC(3)

while True:
    raw_adc_0 = adc_0.read_u16()
    raw_adc_1 = adc_1.read_u16()
    raw_adc_2 = adc_2.read_u16()
    raw_adc_3 = adc_3.read_u16()

    print('{:05d}{:05d}{:05d}{:05d}'.format(
        raw_adc_0,
        raw_adc_1,
        raw_adc_2,
        raw_adc_3,
    ))
