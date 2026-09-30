import type { ImdCategory, Threat } from '../types/forecast'
import { formatDate } from './format'

export type LangCode = 'en' | 'hi' | 'mr' | 'bn' | 'as' | 'ta' | 'te' | 'kn' | 'ml' | 'gu' | 'pa' | 'or'

interface LanguagePack {
  label: string // native name for the tab
  speech: string // BCP-47 tag for speechSynthesis
  category: Record<ImdCategory, string>
  // Fixed template; district/state names stay in English for accuracy
  body: (a: AlertFields) => string
}

export interface AlertFields {
  category: string
  district: string
  state: string
  peak: number
  date: string
}

const HELPLINE = '112 · 1077'

export const LANGUAGES: Record<LangCode, LanguagePack> = {
  en: {
    label: 'English',
    speech: 'en-IN',
    category: { heavy: 'Heavy', very_heavy: 'Very heavy', extremely_heavy: 'Extremely heavy' },
    body: (a) =>
      `${a.category} rainfall warning for ${a.district}, ${a.state}. Up to ${a.peak} mm of rain is expected in the next 24 hours (${a.date}). Risk of flash floods and landslides. Stay away from rivers and slopes, and move to safe higher ground if advised. Follow instructions from the local administration. Emergency: ${HELPLINE}.`,
  },
  hi: {
    label: 'हिन्दी',
    speech: 'hi-IN',
    category: { heavy: 'भारी', very_heavy: 'बहुत भारी', extremely_heavy: 'अत्यंत भारी' },
    body: (a) =>
      `${a.district}, ${a.state} के लिए ${a.category} वर्षा की चेतावनी। अगले 24 घंटों में ${a.peak} मिमी तक बारिश की संभावना है (${a.date})। अचानक बाढ़ और भूस्खलन का खतरा। नदियों और ढलानों से दूर रहें, और सलाह मिलने पर सुरक्षित ऊँचे स्थान पर जाएँ। स्थानीय प्रशासन के निर्देशों का पालन करें। आपातकालीन: ${HELPLINE}।`,
  },
  mr: {
    label: 'मराठी',
    speech: 'mr-IN',
    category: { heavy: 'मुसळधार', very_heavy: 'अति मुसळधार', extremely_heavy: 'अत्यंत मुसळधार' },
    body: (a) =>
      `${a.district}, ${a.state} साठी ${a.category} पावसाचा इशारा. पुढील 24 तासांत ${a.peak} मिमी पर्यंत पावसाची शक्यता (${a.date}). अचानक पूर आणि भूस्खलनाचा धोका. नद्या आणि उतारांपासून दूर राहा, आणि सूचना मिळाल्यास सुरक्षित उंच ठिकाणी जा. स्थानिक प्रशासनाच्या सूचनांचे पालन करा. आपत्कालीन: ${HELPLINE}.`,
  },
  bn: {
    label: 'বাংলা',
    speech: 'bn-IN',
    category: { heavy: 'ভারী', very_heavy: 'অতি ভারী', extremely_heavy: 'অত্যন্ত ভারী' },
    body: (a) =>
      `${a.district}, ${a.state}-এর জন্য ${a.category} বৃষ্টির সতর্কতা। আগামী 24 ঘণ্টায় ${a.peak} মিমি পর্যন্ত বৃষ্টির সম্ভাবনা (${a.date})। হঠাৎ বন্যা ও ভূমিধসের ঝুঁকি। নদী ও ঢাল থেকে দূরে থাকুন, এবং পরামর্শ পেলে নিরাপদ উঁচু স্থানে যান। স্থানীয় প্রশাসনের নির্দেশ মেনে চলুন। জরুরি: ${HELPLINE}।`,
  },
  as: {
    label: 'অসমীয়া',
    speech: 'as-IN',
    category: { heavy: 'গধুৰ', very_heavy: 'অতি গধুৰ', extremely_heavy: 'অত্যন্ত গধুৰ' },
    body: (a) =>
      `${a.district}, ${a.state}ৰ বাবে ${a.category} বৰষুণৰ সতৰ্কবাণী। অহা 24 ঘণ্টাত ${a.peak} মি.মি. লৈকে বৰষুণৰ সম্ভাৱনা (${a.date})। আকস্মিক বানপানী আৰু ভূমিস্খলনৰ আশংকা। নদী আৰু ঢাল অঞ্চলৰ পৰা আঁতৰি থাকক, আৰু পৰামৰ্শ পালে সুৰক্ষিত ওখ স্থানলৈ যাওক। স্থানীয় প্ৰশাসনৰ নিৰ্দেশনা মানি চলক। জৰুৰীকালীন: ${HELPLINE}।`,
  },
  ta: {
    label: 'தமிழ்',
    speech: 'ta-IN',
    category: { heavy: 'கனமழை', very_heavy: 'மிக கனமழை', extremely_heavy: 'அதி கனமழை' },
    body: (a) =>
      `${a.district}, ${a.state} பகுதிக்கு ${a.category} எச்சரிக்கை. அடுத்த 24 மணி நேரத்தில் ${a.peak} மி.மீ வரை மழை பெய்ய வாய்ப்பு (${a.date}). திடீர் வெள்ளம் மற்றும் நிலச்சரிவு அபாயம். ஆறுகள் மற்றும் சரிவுகளிலிருந்து விலகி இருங்கள்; அறிவுறுத்தப்பட்டால் பாதுகாப்பான உயரமான இடத்திற்குச் செல்லுங்கள். உள்ளூர் நிர்வாகத்தின் அறிவுறுத்தல்களைப் பின்பற்றுங்கள். அவசர உதவி: ${HELPLINE}.`,
  },
  te: {
    label: 'తెలుగు',
    speech: 'te-IN',
    category: { heavy: 'భారీ', very_heavy: 'అతి భారీ', extremely_heavy: 'అత్యంత భారీ' },
    body: (a) =>
      `${a.district}, ${a.state} కు ${a.category} వర్ష హెచ్చరిక. రాబోయే 24 గంటల్లో ${a.peak} మి.మీ వరకు వర్షం కురిసే అవకాశం (${a.date}). ఆకస్మిక వరదలు మరియు కొండచరియలు విరిగిపడే ప్రమాదం. నదులు మరియు వాలు ప్రాంతాలకు దూరంగా ఉండండి; సూచన అందితే సురక్షితమైన ఎత్తైన ప్రదేశానికి వెళ్ళండి. స్థానిక అధికారుల సూచనలను పాటించండి. అత్యవసరం: ${HELPLINE}.`,
  },
  kn: {
    label: 'ಕನ್ನಡ',
    speech: 'kn-IN',
    category: { heavy: 'ಭಾರೀ', very_heavy: 'ಅತಿ ಭಾರೀ', extremely_heavy: 'ಅತ್ಯಂತ ಭಾರೀ' },
    body: (a) =>
      `${a.district}, ${a.state} ಗೆ ${a.category} ಮಳೆ ಎಚ್ಚರಿಕೆ. ಮುಂದಿನ 24 ಗಂಟೆಗಳಲ್ಲಿ ${a.peak} ಮಿ.ಮೀ ವರೆಗೆ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ (${a.date}). ಹಠಾತ್ ಪ್ರವಾಹ ಮತ್ತು ಭೂಕುಸಿತದ ಅಪಾಯ. ನದಿಗಳು ಮತ್ತು ಇಳಿಜಾರುಗಳಿಂದ ದೂರವಿರಿ; ಸೂಚನೆ ಬಂದರೆ ಸುರಕ್ಷಿತ ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ. ಸ್ಥಳೀಯ ಆಡಳಿತದ ಸೂಚನೆಗಳನ್ನು ಪಾಲಿಸಿ. ತುರ್ತು: ${HELPLINE}.`,
  },
  ml: {
    label: 'മലയാളം',
    speech: 'ml-IN',
    category: { heavy: 'ശക്തമായ', very_heavy: 'അതിശക്തമായ', extremely_heavy: 'അതിതീവ്ര' },
    body: (a) =>
      `${a.district}, ${a.state} - ${a.category} മഴ മുന്നറിയിപ്പ്. അടുത്ത 24 മണിക്കൂറിനുള്ളിൽ ${a.peak} മി.മീ വരെ മഴയ്ക്ക് സാധ്യത (${a.date}). മിന്നൽ പ്രളയത്തിനും ഉരുൾപൊട്ടലിനും സാധ്യത. നദികളിൽ നിന്നും ചരിവുകളിൽ നിന്നും അകന്നു നിൽക്കുക; നിർദേശം ലഭിച്ചാൽ സുരക്ഷിതമായ ഉയർന്ന സ്ഥലത്തേക്ക് മാറുക. പ്രാദേശിക ഭരണകൂടത്തിന്റെ നിർദേശങ്ങൾ പാലിക്കുക. അടിയന്തരം: ${HELPLINE}.`,
  },
  gu: {
    label: 'ગુજરાતી',
    speech: 'gu-IN',
    category: { heavy: 'ભારે', very_heavy: 'અતિ ભારે', extremely_heavy: 'અત્યંત ભારે' },
    body: (a) =>
      `${a.district}, ${a.state} માટે ${a.category} વરસાદની ચેતવણી. આગામી 24 કલાકમાં ${a.peak} મિ.મી. સુધી વરસાદની શક્યતા (${a.date}). અચાનક પૂર અને ભૂસ્ખલનનું જોખમ. નદીઓ અને ઢોળાવથી દૂર રહો, અને સલાહ મળે તો સુરક્ષિત ઊંચા સ્થળે જાઓ. સ્થાનિક વહીવટીતંત્રની સૂચનાઓનું પાલન કરો. ઇમરજન્સી: ${HELPLINE}.`,
  },
  pa: {
    label: 'ਪੰਜਾਬੀ',
    speech: 'pa-IN',
    category: { heavy: 'ਭਾਰੀ', very_heavy: 'ਬਹੁਤ ਭਾਰੀ', extremely_heavy: 'ਅਤਿ ਭਾਰੀ' },
    body: (a) =>
      `${a.district}, ${a.state} ਲਈ ${a.category} ਮੀਂਹ ਦੀ ਚੇਤਾਵਨੀ। ਅਗਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ${a.peak} ਮਿ.ਮੀ. ਤੱਕ ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ (${a.date})। ਅਚਾਨਕ ਹੜ੍ਹ ਅਤੇ ਜ਼ਮੀਨ ਖਿਸਕਣ ਦਾ ਖ਼ਤਰਾ। ਦਰਿਆਵਾਂ ਅਤੇ ਢਲਾਣਾਂ ਤੋਂ ਦੂਰ ਰਹੋ, ਅਤੇ ਸਲਾਹ ਮਿਲਣ 'ਤੇ ਸੁਰੱਖਿਅਤ ਉੱਚੀ ਥਾਂ 'ਤੇ ਜਾਓ। ਸਥਾਨਕ ਪ੍ਰਸ਼ਾਸਨ ਦੀਆਂ ਹਦਾਇਤਾਂ ਦੀ ਪਾਲਣਾ ਕਰੋ। ਐਮਰਜੈਂਸੀ: ${HELPLINE}।`,
  },
  or: {
    label: 'ଓଡ଼ିଆ',
    speech: 'or-IN',
    category: { heavy: 'ପ୍ରବଳ', very_heavy: 'ଅତି ପ୍ରବଳ', extremely_heavy: 'ଅତ୍ୟଧିକ ପ୍ରବଳ' },
    body: (a) =>
      `${a.district}, ${a.state} ପାଇଁ ${a.category} ବର୍ଷା ଚେତାବନୀ। ଆଗାମୀ 24 ଘଣ୍ଟାରେ ${a.peak} ମି.ମି. ପର୍ଯ୍ୟନ୍ତ ବର୍ଷା ହେବାର ସମ୍ଭାବନା (${a.date})। ହଠାତ୍ ବନ୍ୟା ଓ ଭୂସ୍ଖଳନର ଆଶଙ୍କା। ନଦୀ ଓ ଢାଲୁ ଅଞ୍ଚଳଠାରୁ ଦୂରରେ ରୁହନ୍ତୁ, ଏବଂ ପରାମର୍ଶ ମିଳିଲେ ସୁରକ୍ଷିତ ଉଚ୍ଚ ସ୍ଥାନକୁ ଯାଆନ୍ତୁ। ସ୍ଥାନୀୟ ପ୍ରଶାସନର ନିର୍ଦ୍ଦେଶ ପାଳନ କରନ୍ତୁ। ଜରୁରୀକାଳୀନ: ${HELPLINE}।`,
  },
}

// Official/primary regional language per state (Hindi-belt states use Hindi only)
const STATE_LANGUAGE: Record<string, LangCode> = {
  Maharashtra: 'mr',
  'West Bengal': 'bn',
  Tripura: 'bn',
  Assam: 'as',
  'Tamil Nadu': 'ta',
  Puducherry: 'ta',
  'Andhra Pradesh': 'te',
  Telangana: 'te',
  Karnataka: 'kn',
  Kerala: 'ml',
  Gujarat: 'gu',
  Punjab: 'pa',
  Odisha: 'or',
}

/** Languages to offer for a threat: regional (if any), Hindi, English. */
export function languagesFor(state: string): LangCode[] {
  const regional = STATE_LANGUAGE[state]
  return regional ? [regional, 'hi', 'en'] : ['hi', 'en']
}

export function alertText(threat: Threat, date: string, lang: LangCode): string {
  const pack = LANGUAGES[lang]
  return pack.body({
    category: pack.category[threat.category],
    district: threat.district,
    state: threat.state,
    peak: Math.round(threat.peak_mm),
    date: formatDate(date),
  })
}
