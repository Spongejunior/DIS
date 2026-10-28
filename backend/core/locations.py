"""Extension Planning Areas (EPAs) of Mzimba North and the sections in each.

This is the single list used by the registration and profile forms, the
location filters on the reports page, and the database clean-up in app.py.

A user's EPA is stored in ``User.location`` and their section in
``User.specific_location``. Farmers are assigned to the veterinarians who share
their EPA (see ``auto_assign_by_location`` in app.py).
"""

EPA_SECTIONS = {
    'Bwengu': [
        'Bwengu', 'Katope', 'Embombeni', 'Enukweni', 'Luzi', 'Kacheche',
        'Vongo', 'Luhomero', 'Kavula', 'Jombo',
    ],
    'Engucwini': [
        'Emanyaleni', 'Kamwe', 'Madise', 'Engucwini',
    ],
    'Mpherembe': [
        'Bowe', 'Kazuni', 'Ezweleni', 'Mpherembe', 'Luvwere', 'Enkweleni',
        'Elunyeni', 'Matala',
    ],
    'Zombwe': [
        'Zombwe 1', 'Ekwaiweni 1', 'Lupaso', 'Ekwendeni', 'Choma',
        'Ekwaiweni 2', 'Doroba', 'Edundu', 'Kaluholo', 'Zombwe 2',
        "Eng'congolweni", 'Mtwalo',
    ],
    'Emsizini': [
        'Kafulufulu', 'Enyezini', 'Emsizini', 'Lusangazi', 'Chiwiri',
        'Matuli', 'Baula', 'Elamuleni', 'Kabwanda',
    ],
    'Malidade': [
        'Thunduwike', 'Malidade', 'Kapando', 'Manoro', 'Geza', 'Msambafumu',
        'Kabira', 'Malidade section',
    ],
    'Njuyu': [
        'Kafukule', 'Kapembelwa', 'Njuyu', 'Chigude', 'Emityani', 'Chinyera',
        'Funzani', 'Manthulu',
    ],
    'Euthini': [
        'Yakuwata I', 'Chamnguma', 'Euthini 1', 'Euthini 2', 'Mkwangwali',
        'Mtende', 'Kapando', 'Kamubanga', 'Kanyankhunde', 'Nthumba',
        'Mzambazi', 'Ejezeni',
    ],
    'Mbalachanda': [
        'Madede', 'Mbalachanda', 'Chimaliwa', 'Kasenga', "Chang'anga",
        'Katete',
    ],
}

EPA_NAMES = list(EPA_SECTIONS)

# Every section once, for form fields that accept a section from any EPA.
ALL_SECTIONS = list(dict.fromkeys(
    section for sections in EPA_SECTIONS.values() for section in sections
))

# Names used before the EPA list was corrected -> current name.
RENAMED_EPAS = {
    'Emgucwini': 'Engucwini',
}


def section_belongs_to_epa(section, epa):
    return section in EPA_SECTIONS.get(epa, ())
