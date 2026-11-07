import React from 'react';
import { Link } from 'react-router-dom';
import {
  Mic,
  ArrowRight,
  Compass,
  ShieldAlert,
  HeartHandshake,
  Users,
  MapPin,
  CheckCircle2,
  PhoneCall,
  Volume2
} from 'lucide-react';
import { StatusIndicator } from '../components/StatusIndicator';

export function HomePage() {
  return (
    <div className="space-y-0 text-[#292723]">
      {/* ------------------------------------------------------------- */}
      {/* 1. HERO SECTION: Image-Led Immersive Visual Centerpiece */}
      {/* ------------------------------------------------------------- */}
      <section className="relative w-full bg-[#FAF8F3] overflow-hidden border-b border-[#E2DDD3]">
        <div className="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 pt-4 pb-8 sm:pt-10 sm:pb-16">
          {/* Brand & Editorial Headline Header */}
          <div className="text-center max-w-3xl mx-auto mb-6 sm:mb-8 space-y-2.5 sm:space-y-3 animate-fade-in">
            <div className="inline-flex items-center gap-1.5 sm:gap-2 px-3 sm:px-3.5 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/50 text-[#A83E16] text-[11px] sm:text-xs font-semibold shadow-xs">
              <span className="font-marathi">|| विठ्ठल विठ्ठल जय हरी ||</span>
              <span className="text-[#C69A52]">•</span>
              <span className="font-medium text-[#594333]">Pandharpur Waari</span>
            </div>

            <h1 className="text-2xl xs:text-3xl sm:text-5xl lg:text-6xl font-display font-bold tracking-tight text-[#292723] leading-[1.15]">
              Walking Together.<br />
              <span className="text-[#C65319]">Every Warkari Matters.</span>
            </h1>

            <p className="text-xs sm:text-base lg:text-lg text-[#594333] font-normal max-w-xl mx-auto leading-relaxed px-2">
              Your digital companion throughout the Pandharpur Waari — voice assistance, verified route facilities, emergency support, and seva coordination.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-2.5 sm:gap-3.5 pt-2 max-w-md mx-auto sm:max-w-none">
              <Link
                to="/assistant"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-5 sm:px-6 py-3.5 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white font-semibold text-xs sm:text-sm shadow-md shadow-[#C65319]/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 min-h-[44px]"
              >
                <Mic className="w-4 h-4 text-white shrink-0" />
                <span>Explore Pilgrim Assistant</span>
                <ArrowRight className="w-4 h-4 shrink-0" />
              </Link>

              <a
                href="#spirit-of-waari"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 sm:px-6 py-3.5 rounded-xl bg-white hover:bg-[#F0EDE5] text-[#292723] font-semibold text-xs sm:text-sm border border-[#E2DDD3] shadow-xs transition-colors min-h-[44px]"
              >
                <span>Our Mission</span>
              </a>
            </div>
          </div>

          {/* Central Photographic Centerpiece */}
          <div className="relative mx-auto rounded-xl sm:rounded-3xl overflow-hidden shadow-xl sm:shadow-2xl border-2 sm:border-4 border-white ring-1 ring-[#E2DDD3] bg-[#E2DDD3]/50">
            <img
              src="/Warkari.jpg"
              alt="Pandharpur Waari Procession with Warkaris in traditional white clothing carrying tall saffron flags"
              className="w-full h-auto object-cover max-h-[50vh] sm:max-h-[65vh] lg:max-h-[75vh] select-none"
              style={{ objectPosition: 'center 20%' }}
              loading="eager"
            />
            {/* Editorial bottom gradient anchoring photograph */}
            <div className="absolute inset-x-0 bottom-0 h-20 sm:h-28 bg-gradient-to-t from-[#292723]/80 via-[#292723]/30 to-transparent flex items-end p-3 sm:p-6">
              <div className="text-white text-[11px] sm:text-sm font-medium flex items-center justify-between w-full">
                <span className="font-marathi text-amber-200 line-clamp-1 sm:line-clamp-none">
                  वारकरी बंधू-भगिनींची पायी पंढरी वारी — एकतेचा महासोहळा.
                </span>
                <span className="hidden sm:inline-block bg-white/20 backdrop-blur-sm px-2.5 py-0.5 rounded-md text-[11px] font-sans border border-white/20 shrink-0 ml-2">
                  Pandharpur Palkhi Marg
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Backend Health Status Badge */}
      <div className="bg-[#FAF8F3] py-4 border-b border-[#E2DDD3]">
        <div className="max-w-3xl mx-auto px-4">
          <StatusIndicator />
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. THE SPIRIT OF WAARI: Editorial Introduction */}
      {/* ------------------------------------------------------------- */}
      <section id="spirit-of-waari" className="py-16 sm:py-24 bg-[#F0EDE5] border-b border-[#E2DDD3]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <span className="text-xs uppercase font-bold tracking-widest text-[#C65319]">
              Cultural Heritage & Devotion
            </span>
            <h2 className="text-2xl sm:text-4xl font-display font-bold text-[#292723]">
              The Spirit of Waari
            </h2>
            <div className="w-16 h-1 bg-[#C65319] mx-auto rounded-full mt-2 mb-4"></div>
            <p className="text-[#594333] text-sm sm:text-base leading-relaxed">
              For over seven centuries, hundreds of thousands of Warkaris walk hundreds of kilometers across Maharashtra to the sacred temple town of Pandharpur.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-7 rounded-2xl border border-[#E2DDD3] shadow-xs space-y-3">
              <span className="text-xs font-semibold text-[#A83E16] uppercase tracking-wider">Collective Seva</span>
              <h3 className="text-lg font-bold text-[#292723]">Unity Beyond Barriers</h3>
              <p className="text-xs text-[#594333] leading-relaxed">
                In the Waari, all pilgrims are equal. Walking side by side in traditional white attire with saffron flags high above, kings and commoners chant the divine name as one community.
              </p>
            </div>

            <div className="bg-white p-7 rounded-2xl border border-[#E2DDD3] shadow-xs space-y-3">
              <span className="text-xs font-semibold text-[#A83E16] uppercase tracking-wider">Ancient Tradition</span>
              <h3 className="text-lg font-bold text-[#292723]">Saint Wisdom & Abhangas</h3>
              <p className="text-xs text-[#594333] leading-relaxed">
                Guided by the teachings of Sant Dnyaneshwar, Sant Tukaram, and Sant Namdev, the journey is an embodiment of selfless seva, spiritual discipline, and compassion.
              </p>
            </div>

            <div className="bg-white p-7 rounded-2xl border border-[#E2DDD3] shadow-xs space-y-3">
              <span className="text-xs font-semibold text-[#A83E16] uppercase tracking-wider">Modern Care</span>
              <h3 className="text-lg font-bold text-[#292723]">Preserving Every Pilgrim</h3>
              <p className="text-xs text-[#594333] leading-relaxed">
                From water points to emergency care, our digital platform bridges the ancient pilgrimage with reliable multilingual assistance tailored to elderly pilgrims and field volunteers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 3. A COMPANION ON EVERY STEP: Multilingual Voice & Facilities */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-24 bg-[#FAF8F3] border-b border-[#E2DDD3]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="space-y-2">
                <span className="text-xs uppercase font-bold tracking-widest text-[#C65319]">
                  Speech-First Digital Seva
                </span>
                <h2 className="text-2xl sm:text-4xl font-display font-bold text-[#292723]">
                  A Companion on Every Step
                </h2>
                <p className="text-[#594333] text-sm sm:text-base leading-relaxed">
                  Designed specifically for rural and elderly pilgrims who prefer speaking over typing. Speak in your natural dialect and receive instant spoken guidance.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-xl bg-[#FAF8F3] border border-[#C65319]/30 flex items-center justify-center text-[#C65319] shrink-0 mt-0.5">
                    <Mic className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#292723]">Multilingual Voice Assistant</h4>
                    <p className="text-xs text-[#7A6858] leading-relaxed mt-0.5">
                      Prisma STT and Timbre TTS speech engine supporting authentic Marathi, Hindi, and Indian English with respectful dialect normalization.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-xl bg-[#FAF8F3] border border-[#C69A52]/40 flex items-center justify-center text-[#C69A52] shrink-0 mt-0.5">
                    <Compass className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#292723]">Verified Route Facilities</h4>
                    <p className="text-xs text-[#7A6858] leading-relaxed mt-0.5">
                      Search drinking water points, medical tents, sanitation facilities, food distribution centers (annachhatra), and rest shelters with exact GPS coordinates.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3.5">
                  <div className="w-9 h-9 rounded-xl bg-[#FAF8F3] border border-[#594333]/30 flex items-center justify-center text-[#594333] shrink-0 mt-0.5">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#292723]">Hands-Free Audio Playback</h4>
                    <p className="text-xs text-[#7A6858] leading-relaxed mt-0.5">
                      Instant spoken responses with audio pause, resume, and interruption controls so pilgrims can listen on crowded roads without looking at the screen.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  to="/assistant"
                  className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold transition-all shadow-sm"
                >
                  <span>Try the Voice Assistant</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Visual Sample Card */}
            <div className="bg-[#F0EDE5] p-6 sm:p-8 rounded-3xl border border-[#E2DDD3] space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#E2DDD3] pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse"></span>
                  <span className="text-xs font-bold text-[#292723]">Live Assistant Demo</span>
                </div>
                <span className="text-[11px] bg-white text-[#C65319] border border-[#C65319]/20 font-semibold px-2 py-0.5 rounded">
                  मराठी
                </span>
              </div>

              <div className="space-y-3">
                {/* Pilgrim utterance */}
                <div className="bg-white p-3.5 rounded-2xl rounded-tl-none border border-[#E2DDD3] text-xs space-y-1">
                  <p className="font-semibold text-[#A83E16]">वारकरी (Pilgrim):</p>
                  <p className="text-[#292723] font-marathi">"जवळचे पिण्याचे पाणी कुठे मिळेल?"</p>
                </div>

                {/* Assistant response */}
                <div className="bg-[#FAF8F3] p-4 rounded-2xl rounded-tr-none border border-[#C69A52]/30 text-xs space-y-2">
                  <p className="font-semibold text-[#C65319] flex items-center gap-1.5">
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>सहाय्यक उत्तर (Spoken Response):</span>
                  </p>
                  <p className="text-[#292723] font-marathi leading-relaxed">
                    "वाखारी मुक्काम तळाजवळ शासकीय पिण्याचे पाणी केंद्र उपलब्ध आहे. हे केंद्र २५० मीटर अंतरावर आहे."
                  </p>
                  <div className="pt-1 flex items-center gap-2 text-[11px] text-[#7A6858]">
                    <MapPin className="w-3 h-3 text-[#C65319]" />
                    <span>वाखारी मुक्काम तळ (Wakhari, Pandharpur)</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 text-center">
                <Link
                  to="/facilities"
                  className="text-xs text-[#594333] hover:text-[#C65319] font-semibold underline underline-offset-4"
                >
                  Browse all 5 route facilities with map coordinates &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 4. HELP WHEN IT MATTERS: Emergency & Incident Tracking */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-24 bg-[#F0EDE5] border-b border-[#E2DDD3]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <span className="text-xs uppercase font-bold tracking-widest text-[#C65319]">
              Immediate Lifeline
            </span>
            <h2 className="text-2xl sm:text-4xl font-display font-bold text-[#292723]">
              Help When It Matters
            </h2>
            <div className="w-16 h-1 bg-[#C65319] mx-auto rounded-full mt-2 mb-4"></div>
            <p className="text-[#594333] text-sm sm:text-base leading-relaxed">
              In a crowded pilgrimage of millions, rapid emergency escalation, missing family support, and privacy-protected tracking are paramount.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Immediate 108 Emergency Card */}
            <div className="bg-white p-7 rounded-3xl border border-[#E2DDD3] shadow-xs space-y-4">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F3] border border-rose-300 flex items-center justify-center text-rose-700">
                <PhoneCall className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#292723]">Ambulance & 108 Helpline Safeguard</h3>
              <p className="text-xs text-[#594333] leading-relaxed">
                When a life-safety situation arises, the assistant immediately surfaces government emergency ambulance numbers (<strong>108</strong>) and national emergency services (<strong>112</strong>) without creating false or unmanaged tickets.
              </p>
              <div className="bg-[#FAF8F3] p-3 rounded-xl border border-[#E2DDD3] text-xs space-y-1">
                <span className="font-semibold text-rose-700">तातडीची मदत:</span>
                <p className="text-[#594333]">रुग्णवाहिका: <strong className="text-[#292723]">108</strong> | पोलीस: <strong className="text-[#292723]">100 / 112</strong></p>
              </div>
            </div>

            {/* Privacy-Protected Tracking */}
            <div className="bg-white p-7 rounded-3xl border border-[#E2DDD3] shadow-xs space-y-4">
              <div className="w-10 h-10 rounded-xl bg-[#FAF8F3] border border-[#C65319]/30 flex items-center justify-center text-[#C65319]">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[#292723]">256-Bit Public Request Tracking</h3>
              <p className="text-xs text-[#594333] leading-relaxed">
                Assistance tickets generate a single-use cryptographically secure tracking token and public code (<code>WKR-XXXX-XXXX</code>). Pilgrims can check resolution status without registration or revealing personal data.
              </p>
              <div className="pt-2">
                <Link
                  to="/track"
                  className="inline-flex items-center gap-2 text-xs font-semibold text-[#C65319] hover:text-[#A83E16]"
                >
                  <span>Open Public Incident Tracker</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* 5. TOGETHER, WE SUPPORT THE WAARI: Volunteers & Coordination */}
      {/* ------------------------------------------------------------- */}
      <section className="py-16 sm:py-24 bg-[#FAF8F3]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-br from-[#F0EDE5] to-[#FAF8F3] p-8 sm:p-12 rounded-3xl border border-[#E2DDD3] shadow-sm">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#C69A52]/40 text-[#594333] text-xs font-semibold">
                <HeartHandshake className="w-3.5 h-3.5 text-[#C65319]" />
                <span>सेवाभाव आणि स्वयंसेवक समन्वय</span>
              </div>

              <h2 className="text-2xl sm:text-4xl font-display font-bold text-[#292723]">
                Together, We Support the Waari
              </h2>

              <p className="text-sm sm:text-base text-[#594333] leading-relaxed">
                Behind every resolved incident is a dedicated network of approved sevaks and sector coordinators. From dispatch to resolution, our mobile-optimized portals ensure seamless coordination.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 text-left">
                <div className="bg-white p-5 rounded-2xl border border-[#E2DDD3] space-y-2">
                  <div className="flex items-center gap-2 text-[#C65319] font-bold text-sm">
                    <Users className="w-4 h-4" />
                    <span>Volunteer Sevak Desk</span>
                  </div>
                  <p className="text-xs text-[#7A6858] leading-relaxed">
                    Mobile-first assignment viewer: accept incoming assistance requests, update progress to 'En Route' and 'On Scene', and record resolution notes directly from the road.
                  </p>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-[#E2DDD3] space-y-2">
                  <div className="flex items-center gap-2 text-[#594333] font-bold text-sm">
                    <Compass className="w-4 h-4" />
                    <span>Coordinator Operations Desk</span>
                  </div>
                  <p className="text-xs text-[#7A6858] leading-relaxed">
                    Sector-level incident oversight: filter tickets by urgency and sector, assign verified sevaks, monitor real-time fulfillment, and review historical logs.
                  </p>
                </div>
              </div>

              <div className="pt-6 flex flex-wrap items-center justify-center gap-4">
                <Link
                  to="/login"
                  className="px-6 py-3 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold shadow-md shadow-[#C65319]/20 transition-all"
                >
                  Join as a Sevak or Login
                </Link>
                <Link
                  to="/facilities"
                  className="px-6 py-3 rounded-xl bg-white hover:bg-[#F0EDE5] text-[#292723] text-xs font-semibold border border-[#E2DDD3] transition-colors"
                >
                  Explore Palkhi Map
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
