import requests

tests = [
    # 1. Marathi
    ('पिण्याचे पाणी कुठे मिळेल?', 'mr-IN', 'WATER'),
    ('मला वैद्यकीय मदत हवी आहे', 'mr-IN', 'MEDICAL'),
    ('स्वच्छतागृह कुठे आहे?', 'mr-IN', 'SANITATION'),
    ('माझी व्यक्ती हरवली आहे, मुलगा सापडत नाही', 'mr-IN', 'LOST_PERSON'),
    ('जेवणाची सोय कुठे आहे?', 'mr-IN', 'FOOD'),
    ('विश्रांतीसाठी तंबू कुठे आहेत?', 'mr-IN', 'SHELTER'),
    ('पालखीचा मार्ग काय आहे?', 'mr-IN', 'GENERAL_INFO'),
    ('वाचवा अपघात झाला आहे तातडीने मदत हवी', 'mr-IN', 'EMERGENCY'),

    # 2. Hindi
    ('पीने का पानी कहाँ मिलेगा?', 'hi-IN', 'WATER'),
    ('मुझे चिकित्सा सहायता चाहिए।', 'hi-IN', 'MEDICAL'),
    ('शौचालय कहाँ है?', 'hi-IN', 'SANITATION'),
    ('मेरे पिता खो गए हैं भीड़ में', 'hi-IN', 'LOST_PERSON'),
    ('खाना कहाँ मिलेगा?', 'hi-IN', 'FOOD'),
    ('विश्राम स्थल कहाँ है?', 'hi-IN', 'SHELTER'),
    ('दर्शन का समय क्या है?', 'hi-IN', 'GENERAL_INFO'),
    ('आपातकाल बेहोश हो गए हैं', 'hi-IN', 'EMERGENCY'),

    # 3. English
    ('Where can I find drinking water?', 'en-IN', 'WATER'),
    ('I need medical help', 'en-IN', 'MEDICAL'),
    ('Where are the toilets?', 'en-IN', 'SANITATION'),
    ('I have lost my mother near the tent', 'en-IN', 'LOST_PERSON'),
    ('Where can I get food and prasad?', 'en-IN', 'FOOD'),
    ('Where is resting shelter?', 'en-IN', 'SHELTER'),
    ('What is the palkhi schedule today?', 'en-IN', 'GENERAL_INFO'),
    ('Critical emergency someone collapsed', 'en-IN', 'EMERGENCY'),

    # 4. Marathi transliteration
    ('pani kuthe milel?', 'mr-IN', 'WATER'),
    ('davakhana kuthe ahe', 'mr-IN', 'MEDICAL'),
    ('toilet kuthe ahe', 'mr-IN', 'SANITATION'),
    ('mukkam kuthe ahe', 'mr-IN', 'SHELTER'),
    ('jevan kuthe bhetel', 'mr-IN', 'FOOD'),
    ('aai haravali ahe gardit', 'mr-IN', 'LOST_PERSON'),

    # 5. Unknown & clarification
    ('random unrelated gibberish sentence 987', 'mr-IN', 'UNKNOWN'),
    ('completely irrelevant phrase about astronomy', 'en-IN', 'UNKNOWN'),
]

passed = 0
for text, lang, expected in tests:
    res = requests.post('http://127.0.0.1:8000/api/intelligence/chat', json={'message': text, 'language': lang}).json()
    actual = res['intent']
    status = 'OK' if actual == expected else 'FAIL'
    if status == 'OK':
        passed += 1
    print(f'[{status}] {lang} | "{text}" -> Expected: {expected}, Got: {actual} (Conf: {res["confidence"]})')

print(f'\nTOTAL PASSED: {passed}/{len(tests)}')
if passed != len(tests):
    raise AssertionError(f"Only {passed}/{len(tests)} passed.")
