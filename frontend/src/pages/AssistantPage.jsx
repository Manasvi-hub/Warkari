import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Mic,
  Square,
  Volume2,
  RotateCcw,
  Play,
  Pause,
  Languages,
  AlertCircle,
  ArrowLeft,
  Loader2,
  Sparkles,
  Send,
  MapPin,
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  Compass,
  Phone,
  Info,
  UserCheck,
  UserX
} from 'lucide-react';
import { processVoicePipeline, sendChatMessage, synthesizeSpeech } from '../services/api';
import { convertBlobToWav } from '../utils/audioUtils';

const SUPPORTED_LANGUAGES = [
  { code: 'mr-IN', label: 'मराठी (Marathi)', short: 'मराठी' },
  { code: 'hi-IN', label: 'हिन्दी (Hindi)', short: 'हिन्दी' },
  { code: 'en-IN', label: 'English (India)', short: 'English' },
];

export function AssistantPage() {
  const [selectedLanguage, setSelectedLanguage] = useState('mr-IN');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [processingState, setProcessingState] = useState('idle'); // idle | converting | processing | ready | error
  const [textInput, setTextInput] = useState('');

  // Results
  const [recognizedIntent, setRecognizedIntent] = useState(null);
  const [confidenceScore, setConfidenceScore] = useState(null);
  const [userQuery, setUserQuery] = useState('');
  const [responseText, setResponseText] = useState('');
  const [facilities, setFacilities] = useState([]);
  const [incidentInfo, setIncidentInfo] = useState(null);
  const [clarificationRequired, setClarificationRequired] = useState(false);

  // Missing person staged workflow state
  const [awaitingConsent, setAwaitingConsent] = useState(false);
  const [awaitingDetails, setAwaitingDetails] = useState(false);
  const [missingDetails, setMissingDetails] = useState({ name: '', age: '', last_seen: '' });

  const [audioUrl, setAudioUrl] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  const audioPlayerRef = useRef(null);
  const activeBlobUrlRef = useRef(null);
  const playRequestIdRef = useRef(0);
  const activeAbortControllerRef = useRef(null);

  // Authoritative Audio Controller: stop current audio immediately and invalidate in-flight promises
  const stopAudioImmediate = () => {
    playRequestIdRef.current += 1;
    if (audioPlayerRef.current) {
      try {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.currentTime = 0;
        audioPlayerRef.current.src = '';
        audioPlayerRef.current.onplay = null;
        audioPlayerRef.current.onended = null;
        audioPlayerRef.current.onpause = null;
        audioPlayerRef.current.onerror = null;
      } catch (e) {
        console.warn('Error pausing audio:', e);
      }
      audioPlayerRef.current = null;
    }
    setIsPlaying(false);

    if (activeAbortControllerRef.current) {
      try {
        activeAbortControllerRef.current.abort();
      } catch (e) {
        // ignore
      }
      activeAbortControllerRef.current = null;
    }
  };

  // Authoritative single-instance audio playback function
  const playAudioStream = (newSrc, autoPlay = true, expectedRequestId = null) => {
    // 1. If an expectedRequestId was passed, verify it is still the freshest request
    if (expectedRequestId !== null && expectedRequestId !== playRequestIdRef.current) {
      if (newSrc && newSrc.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(newSrc);
        } catch (e) {
          // ignore
        }
      }
      return;
    }

    // 2. Stop and dispose previous audio instance completely
    if (audioPlayerRef.current) {
      try {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.currentTime = 0;
        audioPlayerRef.current.src = '';
        audioPlayerRef.current.onplay = null;
        audioPlayerRef.current.onended = null;
        audioPlayerRef.current.onpause = null;
        audioPlayerRef.current.onerror = null;
      } catch (e) {
        // ignore
      }
      audioPlayerRef.current = null;
    }

    // 3. Clean up previous object URL if any
    if (activeBlobUrlRef.current && activeBlobUrlRef.current !== newSrc) {
      try {
        URL.revokeObjectURL(activeBlobUrlRef.current);
      } catch (e) {
        console.warn('Error revoking blob url:', e);
      }
      activeBlobUrlRef.current = null;
    }

    if (newSrc && newSrc.startsWith('blob:')) {
      activeBlobUrlRef.current = newSrc;
    }

    // 4. Update state so UI controls reflect the current audio
    setAudioUrl(newSrc);

    if (!newSrc || !autoPlay) return;

    // 5. Play using single tracked Audio instance
    const currentRequestId = playRequestIdRef.current;
    try {
      const player = new Audio(newSrc);
      audioPlayerRef.current = player;

      player.onplay = () => setIsPlaying(true);
      player.onended = () => setIsPlaying(false);
      player.onpause = () => setIsPlaying(false);
      player.onerror = (e) => {
        console.warn('Audio playback error:', e);
        setIsPlaying(false);
      };

      if (playRequestIdRef.current === currentRequestId) {
        const playPromise = player.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            console.log('Autoplay deferred by browser policy. Click Play to listen:', err);
            setIsPlaying(false);
          });
        }
      }
    } catch (err) {
      console.warn('Could not initialize audio player:', err);
    }
  };

  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (audioPlayerRef.current) {
        try {
          audioPlayerRef.current.pause();
          audioPlayerRef.current.currentTime = 0;
          audioPlayerRef.current.src = '';
        } catch (e) {
          // ignore
        }
        audioPlayerRef.current = null;
      }
      if (activeBlobUrlRef.current) {
        try {
          URL.revokeObjectURL(activeBlobUrlRef.current);
        } catch (e) {
          // ignore
        }
        activeBlobUrlRef.current = null;
      }
    };
  }, []);

  // Voice recording handlers
  const startRecording = async () => {
    stopAudioImmediate();
    resetState();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorMessage('Microphone access is not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const rawBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        await handleAudioProcessing(rawBlob);
      };

      recorder.start(250);
      setIsRecording(true);
      setRecordingDuration(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone permission error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Microphone permission was denied. Please allow microphone access in your browser settings.');
      } else {
        setErrorMessage(`Failed to start recording: ${err.message || 'Unknown error'}`);
      }
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleAudioProcessing = async (rawBlob) => {
    stopAudioImmediate();
    const currentReqId = playRequestIdRef.current;
    const controller = new AbortController();
    activeAbortControllerRef.current = controller;

    try {
      setProcessingState('converting');
      const wavBlob = await convertBlobToWav(rawBlob);

      if (playRequestIdRef.current !== currentReqId) return;

      setProcessingState('processing');
      const result = await processVoicePipeline(wavBlob, selectedLanguage, controller.signal);

      if (playRequestIdRef.current !== currentReqId) return;

      setUserQuery(result.transcript || '');

      // Apply unified intelligence results from voice pipeline
      applyIntelResult({
        intent: result.intent,
        confidence: result.confidence,
        response_text: result.response_text,
        facilities: result.facilities || [],
        incident: result.incident || null,
        clarification_required: false,
        awaiting_missing_person_consent: false,
        awaiting_missing_person_details: false,
      });

      if (result.audio_base64) {
        playAudioStream(result.audio_base64, true, currentReqId);
      }

      setProcessingState('ready');
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Voice pipeline error:', err);
      setErrorMessage(err.message || 'Failed to process voice request.');
      setProcessingState('error');
    }
  };

  // Text input processing
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    const query = textInput.trim();
    if (!query) return;

    // Immediately interrupt any playing audio and invalidate previous requests
    stopAudioImmediate();
    const currentReqId = playRequestIdRef.current;
    const controller = new AbortController();
    activeAbortControllerRef.current = controller;

    resetState();
    setUserQuery(query);
    setProcessingState('processing');

    try {
      const intel = await sendChatMessage(query, selectedLanguage, {}, controller.signal);
      
      if (playRequestIdRef.current !== currentReqId) return;
      applyIntelResult(intel);

      // Synthesize spoken voice for text queries using normalized speech_text
      const textToSpeak = intel.speech_text || intel.response_text;
      if (textToSpeak) {
        synthesizeSpeech(textToSpeak, selectedLanguage, controller.signal)
          .then((blob) => {
            if (playRequestIdRef.current !== currentReqId) {
              return;
            }
            const url = URL.createObjectURL(blob);
            playAudioStream(url, true, currentReqId);
          })
          .catch((err) => {
            if (err.name !== 'AbortError') {
              console.warn('Speech synthesis background error:', err);
            }
          });
      }

      setProcessingState('ready');
      setTextInput('');
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Intelligence chat error:', err);
      setErrorMessage(err.message || 'Failed to process assistant request.');
      setProcessingState('error');
    }
  };

  // Missing person staged consent handlers
  const handleConsentResponse = async (consentGranted) => {
    setProcessingState('processing');
    try {
      const intel = await sendChatMessage(userQuery || 'हरवलेली व्यक्ती मदत', selectedLanguage, {
        missing_person_consent: consentGranted,
      });
      applyIntelResult(intel);
      setProcessingState('ready');
    } catch (err) {
      console.error('Consent submission error:', err);
      setErrorMessage(err.message || 'Failed to submit consent choice.');
      setProcessingState('error');
    }
  };

  const handleDetailsSubmit = async (e) => {
    e.preventDefault();
    setProcessingState('processing');
    try {
      const intel = await sendChatMessage(userQuery, selectedLanguage, {
        missing_person_consent: true,
        missing_person_details: missingDetails,
      });
      applyIntelResult(intel);
      setProcessingState('ready');
    } catch (err) {
      console.error('Details submission error:', err);
      setErrorMessage(err.message || 'Failed to submit details.');
      setProcessingState('error');
    }
  };

  const applyIntelResult = (intel) => {
    setRecognizedIntent(intel.intent);
    setConfidenceScore(intel.confidence);
    setResponseText(intel.response_text);
    setFacilities(intel.facilities || []);
    setIncidentInfo(intel.incident || null);
    setClarificationRequired(Boolean(intel.clarification_required));
    setAwaitingConsent(Boolean(intel.awaiting_missing_person_consent));
    setAwaitingDetails(Boolean(intel.awaiting_missing_person_details));
  };

  const resetState = () => {
    // Invalidate any inflight audio request and stop current audio
    stopAudioImmediate();

    setErrorMessage(null);
    setAudioUrl(null);
    setUserQuery('');
    setResponseText('');
    setRecognizedIntent(null);
    setConfidenceScore(null);
    setFacilities([]);
    setIncidentInfo(null);
    setClarificationRequired(false);
    setAwaitingConsent(false);
    setAwaitingDetails(false);
    setMissingDetails({ name: '', age: '', last_seen: '' });
    audioChunksRef.current = [];
    setProcessingState('idle');
  };

  const handleTogglePlayPause = () => {
    if (!audioPlayerRef.current) {
      if (audioUrl) {
        playAudioStream(audioUrl, true);
      }
      return;
    }

    if (isPlaying) {
      audioPlayerRef.current.pause();
    } else {
      audioPlayerRef.current.play().catch((err) => {
        console.warn('Playback error on resume:', err);
      });
    }
  };

  const handleReplay = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.currentTime = 0;
      audioPlayerRef.current.play().catch((e) => console.log('Replay deferred:', e));
    } else if (audioUrl) {
      playAudioStream(audioUrl, true);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12 space-y-8 text-[#292723]">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2DDD3] pb-5">
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#7A6858] hover:text-[#C65319] transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>मुखपृष्ठावर परत जा (Back to Home)</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-[#292723] tracking-tight flex items-center gap-2">
            <span>वारकरी सहाय्यक</span>
            <span className="text-[#C65319] text-sm font-normal">/ Voice & Text AI</span>
          </h1>
          <p className="text-xs sm:text-sm text-[#7A6858] mt-1">
            Multilingual Voice AI • Facility Search • Staged Seva Workflow
          </p>
        </div>

        {/* Language Selector */}
        <div className="flex items-center gap-2 bg-white border border-[#E2DDD3] rounded-2xl px-3.5 py-2 shadow-xs">
          <Languages className="w-4 h-4 text-[#C65319] shrink-0" />
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            disabled={isRecording || processingState === 'processing'}
            className="bg-transparent text-xs text-[#292723] font-semibold focus:outline-hidden cursor-pointer"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} className="bg-white text-[#292723]">
                {lang.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Interactive Assistant Card */}
      <div className="bg-white border border-[#E2DDD3] rounded-3xl p-6 sm:p-10 text-center shadow-xs relative overflow-hidden space-y-8">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-[#C65319]/5 rounded-full blur-3xl pointer-events-none"></div>

        {/* Voice Section */}
        <div className="relative z-10 flex flex-col items-center justify-center space-y-4">
          <div className="relative flex items-center justify-center">
            {isRecording && (
              <>
                <span className="absolute w-36 h-36 rounded-full bg-rose-500/20 animate-ping opacity-75"></span>
                <span className="absolute w-44 h-44 rounded-full bg-rose-500/10 animate-pulse"></span>
              </>
            )}

            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={processingState === 'processing' || processingState === 'converting'}
              className={`w-24 h-24 rounded-full flex flex-col items-center justify-center transition-all duration-300 shadow-md ${
                isRecording
                  ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/40 scale-105'
                  : 'bg-[#C65319] hover:bg-[#A83E16] text-white shadow-[#C65319]/30 hover:scale-105'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isRecording ? 'Stop recording' : 'Start speaking'}
            >
              {isRecording ? <Square className="w-8 h-8 fill-current" /> : <Mic className="w-8 h-8" />}
            </button>
          </div>

          <div>
            {isRecording ? (
              <div className="flex items-center justify-center gap-2 text-rose-700 font-semibold text-xs animate-pulse">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600"></span>
                <span>रेकॉर्डिंग सुरू आहे... / Recording ({formatDuration(recordingDuration)})</span>
              </div>
            ) : processingState === 'processing' || processingState === 'converting' ? (
              <div className="flex items-center justify-center gap-2 text-[#A83E16] text-xs font-semibold">
                <Loader2 className="w-4 h-4 animate-spin text-[#C65319]" />
                <span>
                  {processingState === 'converting'
                    ? 'Preparing audio encoding...'
                    : 'Processing request & assistance rules...'}
                </span>
              </div>
            ) : (
              <p className="text-xs text-[#7A6858]">
                माइक बटण दाबून बोला किंवा खाली टाईप करा (Click mic or type query below)
              </p>
            )}
          </div>
        </div>

        {/* Text Input Option */}
        <form onSubmit={handleTextSubmit} className="relative z-10 max-w-xl mx-auto flex items-center gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="उदा. पिण्याचे पाणी कुठे मिळेल? / Need drinking water..."
            disabled={isRecording || processingState === 'processing'}
            className="flex-1 bg-[#FAF8F3] border border-[#E2DDD3] rounded-2xl px-4 py-3 text-xs text-[#292723] placeholder-[#A09385] focus:outline-hidden focus:border-[#C65319] focus:ring-1 focus:ring-[#C65319] transition-colors"
          />
          <button
            type="submit"
            disabled={!textInput.trim() || processingState === 'processing'}
            className="px-5 py-3 rounded-2xl bg-[#C65319] hover:bg-[#A83E16] disabled:opacity-40 text-white font-semibold text-xs flex items-center gap-2 transition-all shadow-sm"
          >
            <span>पाठवा</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Error Display */}
        {errorMessage && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-left flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs text-rose-900 space-y-1">
              <p className="font-semibold text-rose-950">Processing Error</p>
              <p>{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Results Panel */}
        {(userQuery || responseText) && (
          <div className="space-y-6 text-left border-t border-[#E2DDD3] pt-6">
            {/* User Input & Recognized Intent Badge */}
            <div className="bg-[#FAF8F3] border border-[#E2DDD3] rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-[#7A6858]">
                <span className="font-semibold text-[#A83E16] uppercase tracking-wider flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5" />
                  <span>तुमचा प्रश्न / Pilgrim Request</span>
                </span>
                {recognizedIntent && (
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#F0EDE5] text-[#594333] border border-[#E2DDD3]">
                      Intent: {recognizedIntent}
                    </span>
                    {confidenceScore !== null && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-white text-[#7A6858] border border-[#E2DDD3]">
                        {Math.round(confidenceScore * 100)}% Match
                      </span>
                    )}
                  </div>
                )}
              </div>
              <p className="text-sm font-semibold text-[#292723]">
                {userQuery}
              </p>
            </div>

            {/* Clarification prompt badge if needed */}
            {clarificationRequired && (
              <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>अस्पष्ट प्रश्न: कृपया स्पष्ट माहितीसाठी खालील पर्याय निवडा किंवा अधिक माहिती द्या.</span>
              </div>
            )}

            {/* AI Assistant Spoken / Written Response */}
            <div className="bg-[#FAF8F3] border border-[#C69A52]/40 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between text-xs text-[#7A6858]">
                <span className="font-semibold text-[#C65319] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>वारकरी सहाय्यक / Assistant Guidance</span>
                </span>
              </div>
              <p className="text-sm sm:text-base text-[#292723] font-marathi leading-relaxed">
                {responseText}
              </p>

              {/* Audio Controls */}
              {audioUrl && (
                <div className="flex items-center justify-between pt-3 border-t border-[#E2DDD3]">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleTogglePlayPause}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold shadow-xs transition-colors"
                      title={isPlaying ? 'Pause Audio' : 'Resume Audio'}
                    >
                      {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                      <span>{isPlaying ? 'Pause Voice' : 'Resume Voice'}</span>
                    </button>
                    <button
                      onClick={handleReplay}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-white hover:bg-[#F0EDE5] text-[#292723] border border-[#E2DDD3] text-xs font-semibold transition-colors"
                      title="Replay from start"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-[#594333]" />
                      <span>Replay</span>
                    </button>
                    {isPlaying && (
                      <span className="flex items-center gap-1.5 text-xs text-[#C65319] font-medium ml-2">
                        <Volume2 className="w-4 h-4 animate-pulse" />
                        <span>Playing audio...</span>
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Stage 2: Missing Person Explicit Consent UI */}
            {awaitingConsent && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-3">
                <div className="flex items-center gap-2 text-amber-900 text-xs font-bold uppercase tracking-wider">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span>संमती आवश्यक / Consent Required</span>
                </div>
                <p className="text-xs sm:text-sm text-[#292723]">
                  आपण हरवलेल्या व्यक्तीबाबत मदत विनंती नोंदवू इच्छिता का? (Do you want to register an assistance request?)
                </p>
                <div className="flex items-center gap-3 pt-1">
                  <button
                    onClick={() => handleConsentResponse(true)}
                    disabled={processingState === 'processing'}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold shadow-xs transition-colors"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>होय, नोंदणी करा (Yes, Proceed)</span>
                  </button>
                  <button
                    onClick={() => handleConsentResponse(false)}
                    disabled={processingState === 'processing'}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white hover:bg-[#F0EDE5] text-[#594333] text-xs font-semibold border border-[#E2DDD3] transition-colors"
                  >
                    <UserX className="w-4 h-4" />
                    <span>नाही, गरज नाही (No, Cancel)</span>
                  </button>
                </div>
              </div>
            )}

            {/* Stage 3: Missing Person Minimal Details Form */}
            {awaitingDetails && (
              <form onSubmit={handleDetailsSubmit} className="bg-[#FAF8F3] border border-[#C69A52]/40 rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-[#A83E16] text-xs font-bold uppercase tracking-wider">
                  <Info className="w-4 h-4 text-[#C65319]" />
                  <span>न्यूनतम आवश्यक तपशील / Essential Details</span>
                </div>
                <p className="text-xs text-[#7A6858]">
                  केवळ आवश्यक माहिती द्या. आधार किंवा संवेदनशील वैयक्तिक माहिती विचारली जात नाही.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-[#292723] mb-1">नाव किंवा टोपणनाव (Identifier)</label>
                    <input
                      type="text"
                      required
                      value={missingDetails.name}
                      onChange={(e) => setMissingDetails({ ...missingDetails, name: e.target.value })}
                      placeholder="उदा. ज्ञानेश्वर"
                      className="w-full bg-white border border-[#E2DDD3] rounded-xl px-3 py-2 text-xs text-[#292723] focus:outline-hidden focus:border-[#C65319]"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#292723] mb-1">अंदाजे वय (Approx Age)</label>
                    <input
                      type="text"
                      value={missingDetails.age}
                      onChange={(e) => setMissingDetails({ ...missingDetails, age: e.target.value })}
                      placeholder="उदा. ६५ वर्षे / ज्येष्ठ"
                      className="w-full bg-white border border-[#E2DDD3] rounded-xl px-3 py-2 text-xs text-[#292723] focus:outline-hidden focus:border-[#C65319]"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-[#292723] mb-1">शेवटचे ठिकाण (Last Seen)</label>
                    <input
                      type="text"
                      value={missingDetails.last_seen}
                      onChange={(e) => setMissingDetails({ ...missingDetails, last_seen: e.target.value })}
                      placeholder="उदा. वाखरी तळ"
                      className="w-full bg-white border border-[#E2DDD3] rounded-xl px-3 py-2 text-xs text-[#292723] focus:outline-hidden focus:border-[#C65319]"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={processingState === 'processing'}
                  className="px-4 py-2.5 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold shadow-xs transition-colors"
                >
                  तपशील पाठवा व तिकीट बनवा (Submit Details)
                </button>
              </form>
            )}

            {/* Retrieved Facilities Cards */}
            {facilities.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#594333] flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#C65319]" />
                  <span>उपलब्ध सुविधा केंद्रे / Retrieved Facilities ({facilities.length})</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {facilities.map((fac) => (
                    <div
                      key={fac.id}
                      className="bg-white border border-[#E2DDD3] rounded-2xl p-4 space-y-2 hover:border-[#C69A52] transition-colors shadow-2xs"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-[#292723] font-marathi">{fac.name}</h4>
                            {fac.language_fallback && (
                              <span
                                className="text-[10px] px-1.5 py-0.5 rounded bg-[#FAF8F3] text-[#7A6858] border border-[#E2DDD3]"
                                title="Original Marathi name shown pending reviewed translation"
                              >
                                {selectedLanguage.startsWith('en')
                                  ? 'Original (MR)'
                                  : selectedLanguage.startsWith('hi')
                                  ? 'मूल नाम (MR)'
                                  : 'मूळ नाव (MR)'}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-[#594333] mt-0.5">{fac.location}</p>
                        </div>

                        <div className="flex flex-col items-end gap-1">
                          {fac.is_demo ? (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-amber-50 text-amber-800 border border-amber-200">
                              DEMO DATA
                            </span>
                          ) : fac.is_verified ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>VERIFIED</span>
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-[#FAF8F3] text-[#7A6858] border border-[#E2DDD3]">
                              UNVERIFIED
                            </span>
                          )}
                        </div>
                      </div>

                      {fac.description && (
                        <p className="text-xs text-[#7A6858] leading-normal">{fac.description}</p>
                      )}

                      <div className="flex items-center justify-between text-[11px] text-[#A09385] pt-2 border-t border-[#E2DDD3]">
                        <span className="capitalize text-[#C65319] font-medium">
                          {fac.category.replace('_', ' ')}
                        </span>

                        {fac.contact_phone && !fac.is_demo && (
                          <span className="flex items-center gap-1 text-[#292723] font-semibold">
                            <Phone className="w-3 h-3 text-[#C65319]" />
                            <span>{fac.contact_phone}</span>
                          </span>
                        )}

                        {fac.distance_km !== null && fac.distance_km !== undefined && (
                          <span className="font-mono text-[#594333] font-semibold">
                            {fac.distance_km} km away
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Incident Created Card */}
            {incidentInfo && (
              <div className="bg-white border border-rose-300 rounded-2xl p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-rose-800 text-xs font-bold uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <span>मदत तिकीट नोंदवले / Assistance Ticket #{incidentInfo.id}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-50 text-rose-800 border border-rose-200">
                    Urgency: {incidentInfo.urgency_level}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-[#292723] font-medium">{incidentInfo.description}</p>
                
                {/* Ephemeral Tracking Credentials Banner */}
                {incidentInfo.raw_tracking_token && (
                  <div className="p-4 bg-[#FAF8F3] border border-[#C69A52]/40 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#A83E16]">
                        सार्वजनिक संदर्भ: {incidentInfo.public_reference || 'WKR-PENDING'}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 bg-white text-[#C65319] border border-[#C65319]/30 rounded font-semibold">
                        खाजगी ट्रॅकिंग टोकन
                      </span>
                    </div>
                    <div className="p-2.5 bg-white rounded-xl border border-[#E2DDD3] font-mono text-xs text-[#292723] break-all select-all font-semibold">
                      {incidentInfo.raw_tracking_token}
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-[#7A6858]">
                      <span>हा टोकन कॉपी करून ठेवा. आपण /track पृष्ठावर स्थिती पाहू शकता.</span>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(incidentInfo.raw_tracking_token);
                          alert('Tracking token copied to clipboard! Keep it safe to check status.');
                        }}
                        className="px-3 py-1 bg-[#C65319] hover:bg-[#A83E16] text-white rounded-lg text-[11px] font-semibold shrink-0"
                      >
                        Copy Token
                      </button>
                    </div>
                  </div>
                )}

                <div className="p-3 bg-[#FAF8F3] rounded-xl text-xs text-[#594333] border border-[#E2DDD3]">
                  <p className="text-rose-900 font-medium">{incidentInfo.safety_disclaimer}</p>
                  <p className="text-[11px] text-[#7A6858] mt-1">
                    (Note: Ticket creation logs the distress record for control team coordination. It does not replace direct official emergency response.)
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Safety & Protocol Footer */}
      <div className="bg-white border border-[#E2DDD3] rounded-2xl p-4 text-xs text-[#7A6858] flex items-start gap-3 shadow-xs">
        <Info className="w-4 h-4 text-[#C65319] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-[#292723]">Safety & Privacy Protocol:</p>
          <p>
            Demo facilities are strictly badged as DEMO DATA with zero fake phone numbers. Missing-person assistance requires explicit user consent before ticket registration. Public status endpoints do not reveal private personal identifiers.
          </p>
        </div>
      </div>
    </div>
  );
}
