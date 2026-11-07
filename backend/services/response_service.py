"""Response Composition & Generation Service for Warkari Pilgrimage Platform.

Composes context-aware, intent-specific responses grounded in:
- Recognized intent & sub-intent nuances
- Actual retrieved facility records (verified vs demo vs empty)
- Selected language (mr-IN, hi-IN, en-IN) with pure language consistency
- Distance and location availability
- Incident creation and safety disclaimers
"""

from typing import Any, Dict, List, Optional


def build_response_for_intent(
    intent: str,
    user_query: str,
    facilities: List[Dict[str, Any]],
    incident: Optional[Dict[str, Any]],
    language: str,
    has_user_location: bool = False,
    clarification_prompt: Optional[str] = None
) -> str:
    """Builds a rich, contextual response strictly in the user's selected language."""
    lang = (language or "mr-IN").lower()
    query_lower = (user_query or "").strip().lower()

    if intent == "GREETING":
        return _compose_greeting(lang)

    if intent == "UNKNOWN":
        return clarification_prompt or _compose_unknown(lang)

    if intent == "WATER":
        return _compose_water_response(query_lower, facilities, lang, has_user_location)

    if intent == "MEDICAL":
        return _compose_medical_response(query_lower, facilities, incident, lang, has_user_location)

    if intent == "FOOD":
        return _compose_food_response(query_lower, facilities, lang, has_user_location)

    if intent == "SANITATION":
        return _compose_sanitation_response(query_lower, facilities, lang, has_user_location)

    if intent == "SHELTER":
        return _compose_shelter_response(query_lower, facilities, lang, has_user_location)

    if intent == "EMERGENCY":
        return _compose_emergency_response(query_lower, incident, lang)

    if intent == "HELPLINE_INFO":
        return _compose_helpline_info_response(lang)

    if intent == "GENERAL_INFO":
        return _compose_general_info_response(query_lower, lang)

    # Fallback
    return _compose_unknown(lang)


def _compose_greeting(lang: str) -> str:
    if lang.startswith("mr"):
        return (
            "नमस्कार! मी वारकरी सहाय्यक आहे. "
            "आपणास पिण्याचे पाणी, वैद्यकीय मदत, अन्नछत्र, विश्रांतीची ठिकाणे, "
            "शौचालये किंवा इतर मार्गदर्शनासाठी मी मदत करू शकतो. "
            "आज आपल्याला कशाबद्दल माहिती हवी आहे?"
        )
    elif lang.startswith("hi"):
        return (
            "नमस्ते! मैं वारकरी सहायता सहायक हूँ। "
            "मैं आपको पीने का पानी, चिकित्सा शिविर, भोजन व्यवस्था, विश्राम स्थल "
            "तथा शौचालय सुविधाओं की जानकारी दे सकता हूँ। "
            "आज मैं आपकी क्या सहायता कर सकता हूँ?"
        )
    else:
        return (
            "Namaskar! I am Warkari, your pilgrimage assistance assistant. "
            "I can help you locate drinking water, medical posts, food distribution, "
            "rest shelters, and public toilets, or register an urgent assistance request. "
            "How can I assist you right now?"
        )


def _compose_unknown(lang: str) -> str:
    if lang.startswith("mr"):
        return (
            "माफ करा, मला आपला प्रश्न स्पष्ट समजला नाही. "
            "आपल्याला पिण्याचे पाणी, दवाखाना, अन्नछत्र, शौचालय, मुक्काम की हरवलेल्या व्यक्तीबाबत मदत हवी आहे का? "
            "कृपया थोडक्यात सांगा."
        )
    elif lang.startswith("hi"):
        return (
            "क्षमा करें, मैं आपका प्रश्न समझ नहीं पाया। "
            "क्या आपको पेयजल, चिकित्सा सहायता, भोजन, शौचालय, विश्राम स्थल अथवा लापता व्यक्ति के संबंध में सहायता चाहिए? "
            "कृपया स्पष्ट करें।"
        )
    else:
        return (
            "I could not understand your request clearly. "
            "Do you need drinking water, medical aid, food, public toilets, resting shelter, or missing person assistance? "
            "Please clarify your question."
        )


def _format_facility_details(facilities: List[Dict[str, Any]], lang: str, has_user_location: bool) -> Tuple[str, bool]:
    """Formats facility items list with verification truthfulness, distance notices,
    and transparent disclosure when showing canonical Marathi information due to pending translations."""
    if not facilities:
        return "", False

    lines = []
    has_demo = False
    has_fallback = False
    req_is_en = lang.startswith("en")
    req_is_hi = lang.startswith("hi")

    for i, fac in enumerate(facilities[:3], 1):
        name = fac.get("name") or "सुविधा केंद्र"
        loc = fac.get("location") or "पालखी मार्ग"
        dist = fac.get("distance_km")
        is_demo = fac.get("is_demo", False)
        if is_demo:
            has_demo = True

        if fac.get("language_fallback"):
            has_fallback = True

        dist_label = ""
        if has_user_location and dist is not None:
            if lang.startswith("mr"):
                dist_label = f" (सुमारे {dist} किमी अंतरावर)"
            elif lang.startswith("hi"):
                dist_label = f" (लगभग {dist} किमी दूरी पर)"
            else:
                dist_label = f" (approx {dist} km away)"

        lines.append(f"{i}. {name} - {loc}{dist_label}")

    formatted_text = "\n".join(lines)

    # Disclose translation fallback note transparently if requested in English or Hindi
    if has_fallback:
        if req_is_en:
            fallback_note = "\n(Note: Official English facility names are pending verification; original Marathi information is shown above.)"
            formatted_text += fallback_note
        elif req_is_hi:
            fallback_note = "\n(सूचना: आधिकारिक हिन्दी नाम सत्यापन प्रक्रिया में हैं; मूल मराठी जानकारी प्रदर्शित है।)"
            formatted_text += fallback_note

    return formatted_text, has_demo


def _compose_water_response(query: str, facilities: List[Dict[str, Any]], lang: str, has_user_location: bool) -> str:
    is_urgent = any(w in query for w in ["तातडीने", "लगेच", "संपले", "urgent", "emergency", "तहान"])
    fac_text, has_demo = _format_facility_details(facilities, lang, has_user_location)

    if lang.startswith("mr"):
        urgency_prefix = "तातडीची तहान असल्यास जवळच्या स्वयंसेवकांशी संपर्क साधा. " if is_urgent else ""
        if facilities:
            if has_demo:
                return (
                    f"{urgency_prefix}आमच्या सध्याच्या डेमो डेटामध्ये पिण्याच्या पाण्याची खालील संभाव्य ठिकाणे दाखवली आहेत "
                    f"(ही प्रत्यक्ष पडताळलेली सुविधा नाही):\n{fac_text}\n"
                    "कृपया प्रत्यक्ष जागेवर उपलब्धतेची खात्री करा. वारी मार्गावर शासकीय टँकर सतत फिरत असतात."
                )
            else:
                return (
                    f"{urgency_prefix}आपल्या जवळ पिण्याच्या पाण्याची खालील पडताळलेली सुविधा उपलब्ध आहे:\n{fac_text}\n"
                    "कृपया पिण्यापूर्वी पाण्याची खात्री करा आणि पाण्याचा अपव्यय टाळा."
                )
        else:
            return (
                f"{urgency_prefix}सध्या या परिसरासाठी अधिकृत पडताळणी झालेल्या पिण्याच्या पाण्याच्या टँकरची माहिती उपलब्ध नाही. "
                "पालखी मार्गावरील शासकीय मदत कक्षात पाणी उपलब्ध असते."
            )

    elif lang.startswith("hi"):
        urgency_prefix = "यदि पानी की तुरंत आवश्यकता है, तो नजदीकी स्वयंसेवकों से संपर्क करें। " if is_urgent else ""
        if facilities:
            if has_demo:
                return (
                    f"{urgency_prefix}हमारे वर्तमान डेमो डेटा में पेयजल के संभावित केंद्र दर्शाए गए हैं "
                    f"(यह वास्तविक सत्यापित डेटा नहीं है):\n{fac_text}\n"
                    "कृपया स्थल पर उपलब्धता की जांच अवश्य करें।"
                )
            else:
                return (
                    f"{urgency_prefix}आपके निकट सत्यापित पेयजल व्यवस्था उपलब्ध है:\n{fac_text}\n"
                    "कृपया स्थल पर जाकर जल सेवा का लाभ लें।"
                )
        else:
            return (
                f"{urgency_prefix}वर्तमान में इस स्थान के लिए सत्यापित पेयजल केंद्र की जानकारी उपलब्ध नहीं है। "
                "कृपया मुख्य मार्ग पर प्रशासनिक जल सेवा से संपर्क करें।"
            )

    else:
        urgency_prefix = "If you need water urgently, please alert the nearest route volunteer. " if is_urgent else ""
        if facilities:
            if has_demo:
                return (
                    f"{urgency_prefix}Our current demo dataset indicates the following potential drinking water points "
                    f"(Note: this is synthetic demo data, not live verified):\n{fac_text}\n"
                    "Please verify availability on-site."
                )
            else:
                return (
                    f"{urgency_prefix}Here are the verified drinking water points available near your route:\n{fac_text}\n"
                    "Water tankers are actively stationed along the pilgrimage path."
                )
        else:
            return (
                f"{urgency_prefix}Verified drinking water station information is currently unavailable in this sector. "
                "Official water tankers are stationed at major halts."
            )


def _compose_medical_response(query: str, facilities: List[Dict[str, Any]], incident: Optional[Dict[str, Any]], lang: str, has_user_location: bool) -> str:
    fac_text, has_demo = _format_facility_details(facilities, lang, has_user_location)

    if incident:
        inc_id = incident.get("id")
        if lang.startswith("mr"):
            return (
                f"तातडीची सूचना: आपली वैद्यकीय मदत विनंती (तिकीट #{inc_id}) प्रणालीत नोंदवली आहे. "
                "कृपया रुग्णाला सुरक्षित व सावलीच्या ठिकाणी विश्रांती द्या. "
                "(महत्त्वाची सूचना: आपले तिकीट नोंदवले गेले आहे, परंतु शासकीय रुग्णवाहिका किंवा स्वयंसेवक उपस्थित होण्याची अद्याप पुष्टी झालेली नाही. "
                "तातडीच्या स्थितीत थेट शासकीय १०८ रुग्णवाहिकेशी संपर्क साधा.)"
            )
        elif lang.startswith("hi"):
            return (
                f"आपातकालीन सूचना: आपकी चिकित्सा सहायता टिकट (#{inc_id}) दर्ज कर ली गई है। "
                "कृपया रोगी को छायादार व सुरक्षित स्थान पर बैठाएं। "
                "(महत्वपूर्ण सूचना: अनुरोध दर्ज किया गया है, किंतु अभी एम्बुलेंस या स्वयंसेवक की उपस्थिति की पुष्टि नहीं हुई है। "
                "गंभीर स्थिति में सरकारी १०८ एम्बुलेंस से तुरंत संपर्क करें।)"
            )
        else:
            return (
                f"Emergency Notice: Your medical assistance request (Ticket #{inc_id}) has been recorded. "
                "Please keep the affected person in a safe, shaded area. "
                "(Important Notice: Your request has been recorded. This does not mean a medical team has been dispatched or arrived. "
                "For life-threatening emergencies, call official 108 ambulance service immediately.)"
            )

    # Routine medical inquiry
    is_first_aid = any(w in query for w in ["प्रथमोपचार", "पट्टी", "गोळ्या", "चोट", "first aid", "bandage"])
    if lang.startswith("mr"):
        focus = "प्रथमोपचार व प्राथमिक औषधोपचारासाठी " if is_first_aid else "वैद्यकीय तपासणी व उपचारासाठी "
        if facilities:
            notice = " (डेमो डेटा - प्रत्यक्ष पडताळणी नाही)" if has_demo else " (पडताळलेले केंद्र)"
            return (
                f"{focus}खालील आरोग्य शिबिराची माहिती उपलब्ध आहे{notice}:\n{fac_text}\n"
                "गंभीर त्रास असल्यास स्वतः चालण्याचा प्रयत्न न करता विश्रांती घ्या."
            )
        else:
            return (
                "सध्या या भागात पडताळणी झालेले वैद्यकीय मदत केंद्र उपलब्ध नाही. "
                "पालखी मार्गावरील शासकीय आरोग्य पथक किंवा रुग्णवाहिका कर्मचाऱ्यांशी संपर्क साधा."
            )

    elif lang.startswith("hi"):
        focus = "प्राथमिक उपचार और दवाइयों के लिए " if is_first_aid else "चिकित्सा जांच एवं परामर्श हेतु "
        if facilities:
            notice = " (डेमो डेटा - असत्यापित)" if has_demo else " (सत्यापित केंद्र)"
            return (
                f"{focus}निकटतम स्वास्थ्य शिविर की जानकारी:\n{fac_text}{notice}\n"
                "अधिक समस्या होने पर तुरंत विश्राम करें।"
            )
        else:
            return (
                "वर्तमान में इस क्षेत्र के लिए सत्यापित चिकित्सा शिविर की जानकारी उपलब्ध नहीं है। "
                "कृपया नजदीकी सरकारी एम्बुलेंस से संपर्क करें।"
            )

    else:
        focus = "For first aid and basic medication, " if is_first_aid else "For healthcare and medical consultation, "
        if facilities:
            notice = " (Synthetic Demo Data)" if has_demo else " (Verified Facility)"
            return (
                f"{focus}here is the medical post information on record:\n{fac_text}{notice}\n"
                "If symptoms worsen, please request urgent assistance."
            )
        else:
            return (
                "Verified medical post information is currently unavailable in this immediate sector. "
                "Please approach official medical staff stationed along the highway."
            )


def _compose_food_response(query: str, facilities: List[Dict[str, Any]], lang: str, has_user_location: bool) -> str:
    is_prasad = any(w in query for w in ["प्रसाद", "prasad"])
    fac_text, has_demo = _format_facility_details(facilities, lang, has_user_location)

    if lang.startswith("mr"):
        topic = "महाप्रसाद" if is_prasad else "अन्नछत्र व भोजन व्यवस्था"
        if facilities:
            demo_warn = " [डेमो डेटा - प्रत्यक्ष पडताळणी नाही]" if has_demo else ""
            return (
                f"वारकऱ्यांसाठी {topic} खालील ठिकाणी उपलब्ध असल्याची माहिती आहे{demo_warn}:\n{fac_text}\n"
                "अन्नछत्र वेळेनुसार कार्यरत असते. कृपया अन्न वाया घालवू नका."
            )
        else:
            return f"सध्या या परिसरासाठी {topic} उपलब्धतेची पडताळलेली माहिती उपलब्ध नाही."

    elif lang.startswith("hi"):
        topic = "प्रसाद" if is_prasad else "भोजन व अन्नक्षेत्र"
        if facilities:
            demo_warn = " [डेमो डेटा]" if has_demo else ""
            return (
                f"तीर्थयात्रियों के लिए {topic} की जानकारी:\n{fac_text}{demo_warn}\n"
                "भोजन वितरण निश्चित समय पर संचालित होता है।"
            )
        else:
            return f"वर्तमान में इस स्थान के लिए {topic} की सत्यापित जानकारी उपलब्ध नहीं है।"

    else:
        topic = "Prasad distribution" if is_prasad else "Free meals and food distribution"
        if facilities:
            demo_warn = " [Demo Data - Not Live Verified]" if has_demo else ""
            return (
                f"{topic} points recorded near your route:\n{fac_text}{demo_warn}\n"
                "Canteens operate according to daily pilgrimage meal times."
            )
        else:
            return f"Verified {topic} information is currently unavailable in this location."


def _compose_sanitation_response(query: str, facilities: List[Dict[str, Any]], lang: str, has_user_location: bool) -> str:
    is_complaint = any(w in query for w in ["घाण", "अस्वच्छ", "पाणी नाही", "गंदा", "dirty", "unclean", "smell"])
    fac_text, has_demo = _format_facility_details(facilities, lang, has_user_location)

    if lang.startswith("mr"):
        if is_complaint:
            return (
                "शौचालयाच्या अस्वच्छतेची नोंद घेण्यात आली आहे. स्वच्छता पथकाला या भागाची माहिती कळवली जाईल. "
                f"पर्यायी स्वच्छतागृह ठिकाणे:\n{fac_text}" if facilities else "शौचालयाच्या अस्वच्छतेची नोंद घेतली आहे."
            )
        if facilities:
            demo_warn = " [डेमो डेटा]" if has_demo else ""
            return (
                f"सार्वजनिक स्वच्छतागृह व फिरती शौचालये खालील ठिकाणी उपलब्ध आहेत{demo_warn}:\n{fac_text}\n"
                "कृपया स्वच्छता राखण्यास सहकार्य करा."
            )
        return "सध्या या परिसरासाठी पडताळणी झालेल्या सार्वजनिक स्वच्छतागृहांची माहिती उपलब्ध नाही."

    elif lang.startswith("hi"):
        if is_complaint:
            return "शौचालय की अस्वच्छता की सूचना दर्ज कर ली गई है। स्वच्छता कर्मियों को सूचित किया जाएगा।"
        if facilities:
            demo_warn = " [डेमो डेटा]" if has_demo else ""
            return (
                f"सार्वजनिक व मोबाइल शौचालय केंद्र:\n{fac_text}{demo_warn}\n"
                "कृपया स्वच्छता बनाए रखें।"
            )
        return "वर्तमान में इस क्षेत्र के लिए सत्यापित सार्वजनिक शौचालयों की जानकारी उपलब्ध नहीं है।"

    else:
        if is_complaint:
            return "Thank you for reporting the sanitation issue. The route hygiene team has been logged for maintenance."
        if facilities:
            demo_warn = " [Demo Data]" if has_demo else ""
            return (
                f"Public restrooms and mobile sanitation units are located at:\n{fac_text}{demo_warn}\n"
                "Please help maintain cleanliness."
            )
        return "Verified public sanitation information is currently unavailable in this area."


def _compose_shelter_response(query: str, facilities: List[Dict[str, Any]], lang: str, has_user_location: bool) -> str:
    is_night_stay = any(w in query for w in ["रात्र", "मुक्काम", "झोप", "रात", "night", "sleep", "stay"])
    fac_text, has_demo = _format_facility_details(facilities, lang, has_user_location)

    if lang.startswith("mr"):
        type_str = "रात्र मुक्काम व विश्रांती कक्ष" if is_night_stay else "विश्रांती मंडप व निवारा तंबू"
        if facilities:
            demo_warn = " [डेमो डेटा]" if has_demo else ""
            return (
                f"वारकऱ्यांसाठी {type_str} खालील ठिकाणी उपलब्ध आहेत{demo_warn}:\n{fac_text}\n"
                "मुक्काम तळावर सुरक्षा व पिण्याच्या पाण्याची व्यवस्था असते."
            )
        return f"सध्या या परिसरासाठी {type_str} उपलब्धतेची पडताळलेली माहिती उपलब्ध नाही."

    elif lang.startswith("hi"):
        type_str = "रात्रि विश्राम स्थल" if is_night_stay else "विश्राम शिविर व तंबू"
        if facilities:
            demo_warn = " [डेमो डेटा]" if has_demo else ""
            return (
                f"तीर्थयात्रियों के लिए {type_str}:\n{fac_text}{demo_warn}\n"
                "विश्राम स्थल पर सुरक्षा नियमों का पालन करें।"
            )
        return f"वर्तमान में इस क्षेत्र के लिए {type_str} की जानकारी उपलब्ध नहीं है।"

    else:
        type_str = "Overnight accommodation and resting camp" if is_night_stay else "Rest shelters and shaded tents"
        if facilities:
            demo_warn = " [Demo Data]" if has_demo else ""
            return (
                f"{type_str} points available for pilgrims:\n{fac_text}{demo_warn}\n"
                "Halts provide security and essential resting facilities."
            )
        return f"Verified information for {type_str.lower()} is currently unavailable here."


def _compose_emergency_response(query: str, incident: Optional[Dict[str, Any]], lang: str) -> str:
    inc_id = incident.get("id") if incident else "नोंदवले"
    is_medical_urgency = any(w in query for w in ["बेशुद्ध", "बेहोश", "चक्कर", "हार्ट", "श्वास", "रक्त", "accident", "unconscious", "collapse", "breath", "bleeding", "ambulance", "रुग्णवाहिका", "एम्बुलेंस"])

    if lang.startswith("mr"):
        ambulance_tip = " वैद्यकीय आणीबाणीसाठी थेट शासकीय १०८ रुग्णवाहिकेशी त्वरित संपर्क साधा." if is_medical_urgency else ""
        return (
            f"आणीबाणी अलर्ट: आपली मदत विनंती (तिकीट #{inc_id}) तातडीने नोंदवली गेली आहे. "
            f"कृपया शांत राहा आणि सुरक्षित ठिकाणी थांबा.{ambulance_tip} "
            "(महत्त्वाची सूचना: हे तिकीट प्रणालीत नोंदवले गेले आहे, परंतु हे थेट पोलीस किंवा आपत्कालीन कॉल नाही. "
            "तातडीच्या धोक्यात जवळच्या पोलीस किंवा सुरक्षा चौकीकडे संपर्क साधा.)"
        )
    elif lang.startswith("hi"):
        ambulance_tip = " चिकित्सीय आपात स्थिति में तुरंत सरकारी १०८ एम्बुलेंस से संपर्क करें।" if is_medical_urgency else ""
        return (
            f"आपातकालीन अलर्ट दर्ज किया गया (टिकट #{inc_id})। "
            f"कृपया सुरक्षित स्थान पर रहें।{ambulance_tip} "
            "(महत्वपूर्ण सूचना: अनुरोध दर्ज कर लिया गया है, किंतु यह सीधा पुलिस या आपातकालीन कॉल नहीं है। "
            "अत्यधिक आपात स्थिति में निकटतम सुरक्षा बल से संपर्क करें।)"
        )
    else:
        ambulance_tip = " For medical emergencies, contact official 108 ambulance immediately." if is_medical_urgency else ""
        return (
            f"Emergency Alert: Your assistance request (Ticket #{inc_id}) has been recorded. "
            f"Please stay in a safe position.{ambulance_tip} "
            "(Important Notice: Your request has been recorded. This does not mean emergency services have been contacted directly. "
            "For life-threatening danger, notify route security personnel immediately.)"
        )


def _compose_helpline_info_response(lang: str) -> str:
    """Informational emergency helpline guidance without creating false active incident tickets."""
    if lang.startswith("mr"):
        return (
            "वैद्यकीय आणीबाणीसाठी अधिकृत शासकीय रुग्णवाहिका क्रमांक १०८ आहे. "
            "पोलीस मदतीसाठी १०० किंवा ११२ डायल करा. "
            "(महत्त्वाची सूचना: हा केवळ माहितीपर संदेश असून कोणताही थेट कॉल जोडला गेलेला नाही. "
            "तातडीच्या वेळी स्वतः या क्रमांकावर थेट संपर्क साधा किंवा जवळच्या सुरक्षा कक्षास कळवा.)"
        )
    elif lang.startswith("hi"):
        return (
            "चिकित्सीय आपात स्थिति के लिए आधिकारिक सरकारी एम्बुलेंस नंबर १०८ है। "
            "पुलिस सहायता के लिए १०० या ११२ डायल करें। "
            "(महत्वपूर्ण सूचना: यह केवल सूचनात्मक मार्गदर्शन है, कोई सीधा कॉल नहीं मिलाया गया है। "
            "गंभीर स्थिति में स्वयं इस नंबर पर डायल करें अथवा नजदीकी सुरक्षा कक्ष से संपर्क करें।)"
        )
    else:
        return (
            "For medical emergencies, the official government ambulance helpline is 108. "
            "For police assistance, dial 100 or 112. "
            "(Important Notice: This is informational guidance only and does not place an emergency call. "
            "In life-threatening situations, dial the helpline directly or alert the nearest police booth.)"
        )


def _compose_general_info_response(query: str, lang: str) -> str:
    is_route = any(w in query for w in ["मार्ग", "रस्ता", "route", "direction", "कुठे"])
    is_darshan = any(w in query for w in ["दर्शन", "वेळ", "timing", "darshan"])

    if lang.startswith("mr"):
        if is_route:
            return (
                "संत ज्ञानेश्वर महाराज व संत तुकाराम महाराज पालखी सोहळा पुणे, सासवड, लोणंद, फलटण, "
                "नातेपुते, माळशिरस, वेळापूर, वाखरी मार्गे पंढरपूरकडे मार्गक्रमण करतो. "
                "विशिष्ट मुक्काम स्थळाची माहिती हवी असल्यास मुक्कामाचे गाव विचारा."
            )
        elif is_darshan:
            return (
                "पंढरपूर विठ्ठल रुक्मिणी मंदिरात पदस्पर्श दर्शन व मुखदर्शन अशा दोन रांगा असतात. "
                "वारी काळात दर्शनाची वेळ वाढवली जाते. अधिकृत सूचना मंदिर प्रशासनाच्या फलकावर उपलब्ध असतात."
            )
        return (
            "पंढरपूर आषाढी वारी पालखी सोहळा सुरू आहे. पाणी, मुक्काम, वैद्यकीय मदत किंवा मार्गदर्शनासाठी "
            "आपण कधीही विचारू शकता. जय हरी विठ्ठल!"
        )

    elif lang.startswith("hi"):
        if is_route:
            return (
                "पालकी यात्रा पुणे, सासवड, लोणंद, फलटण, वेळापूर और वाखरी होते हुए पंढरपुर पहुँचती है। "
                "विशिष्ट पड़ाव की जानकारी के लिए स्थान का नाम बताएं।"
            )
        elif is_darshan:
            return (
                "पंढरपुर श्री विट्ठल रुक्मिणी मंदिर में पदस्पर्श दर्शन और मुखदर्शन दोनों व्यवस्थाएं हैं। "
                "यात्रा काल में दर्शन के समय में विस्तार किया जाता है।"
            )
        return (
            "पंढरपुर आषाढ़ी वारी यात्रा प्रगति पर है। जल, विश्राम स्थल, चिकित्सा सेवा अथवा मार्गदर्शन हेतु आप पूछ सकते हैं।"
        )

    else:
        if is_route:
            return (
                "The primary Palkhi procession routes proceed through Pune, Saswad, Lonand, Phaltan, "
                "Velapur, and Wakhari before reaching Pandharpur. Ask for a specific town halt for details."
            )
        elif is_darshan:
            return (
                "The Pandharpur Vitthal-Rukmini Temple maintains separate queues for Charansparsh (feet touch) "
                "and Mukh Darshan. Timings are extended during the Wari pilgrimage period."
            )
        return (
            "The Pandharpur Ashadhi Wari pilgrimage is underway. Feel free to ask about drinking water, "
            "resting camps, healthcare, or route assistance. Jai Hari Vitthal!"
        )
