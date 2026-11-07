import React, { useState, useEffect } from 'react';
import { searchFacilities } from '../services/api';
import {
  MapPin,
  Search,
  Filter,
  CheckCircle2,
  Droplet,
  HeartPulse,
  Trash2,
  Utensils,
  Home,
  AlertCircle,
  Loader2,
  Compass,
  Phone,
  ExternalLink
} from 'lucide-react';

const CATEGORIES = [
  { key: '', label: 'सर्व (All)', icon: Compass },
  { key: 'drinking_water', label: 'पिण्याचे पाणी (Water)', icon: Droplet },
  { key: 'medical', label: 'वैद्यकीय मदत (Medical)', icon: HeartPulse },
  { key: 'sanitation', label: 'स्वच्छतागृह (Sanitation)', icon: Trash2 },
  { key: 'food', label: 'अन्नछत्र (Food)', icon: Utensils },
  { key: 'resting_area', label: 'विश्रांती मंडप (Rest Area)', icon: Home },
];

export function FacilitiesPage() {
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('mr-IN');
  const [selectedFacility, setSelectedFacility] = useState(null);

  const loadFacilities = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { language: selectedLanguage };
      if (selectedCategory) params.category = selectedCategory;
      if (searchQuery.trim()) params.query = searchQuery.trim();

      const data = await searchFacilities(params);
      setFacilities(data);
      if (data.length > 0 && !selectedFacility) {
        setSelectedFacility(data[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load route facilities.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFacilities();
  }, [selectedCategory, selectedLanguage]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadFacilities();
  };

  return (
    <div className="max-w-7xl mx-auto px-3.5 sm:px-6 lg:px-8 py-5 sm:py-10 space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 sm:gap-4 border-b border-[#E2DDD3] pb-4 sm:pb-6">
        <div className="space-y-1.5 sm:space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/40 text-[#A83E16] text-[11px] sm:text-xs font-semibold">
            <Compass className="w-3.5 h-3.5 text-[#C65319]" />
            <span>वारी मार्ग सुविधा निर्देशिका / Route Facilities</span>
          </div>
          <h1 className="text-xl sm:text-3xl lg:text-4xl font-display font-bold text-[#292723]">
            वारी मार्ग अधिकृत सुविधा केंद्र
          </h1>
          <p className="text-xs sm:text-sm text-[#7A6858] max-w-xl">
            पंढरपूर पालखी मार्गावरील पिण्याचे पाणी, वैद्यकीय मदत शिबिरे, अन्नछत्रे आणि निवारा केंद्रांची माहिती.
          </p>
        </div>

        {/* Language switcher */}
        <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-[#E2DDD3] self-start md:self-auto shrink-0">
          {[
            { code: 'mr-IN', label: 'मराठी' },
            { code: 'hi-IN', label: 'हिन्दी' },
            { code: 'en-IN', label: 'English' }
          ].map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSelectedLanguage(lang.code)}
              className={`px-2.5 sm:px-3 py-1.5 text-xs font-bold rounded-lg transition-all min-h-[36px] ${
                selectedLanguage === lang.code
                  ? 'bg-[#C65319] text-white shadow-xs'
                  : 'text-[#594333] hover:bg-[#F0EDE5]'
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      {/* Category Pills & Search Bar */}
      <div className="space-y-3 sm:space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full max-w-lg">
          <div className="relative flex-1 min-w-0">
            <Search className="w-4 h-4 text-[#A09385] absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="नाव किंवा ठिकाण शोधा (वाखारी, पाणी...)..."
              className="w-full pl-9 sm:pl-10 pr-3 sm:pr-4 py-2.5 bg-white border border-[#E2DDD3] rounded-xl text-xs sm:text-sm text-[#292723] placeholder-[#A09385] focus:outline-hidden focus:border-[#C65319]"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2.5 bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-semibold rounded-xl transition-all shadow-xs shrink-0 min-h-[42px]"
          >
            शोधा
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.key;
            return (
              <button
                key={cat.key}
                onClick={() => setSelectedCategory(cat.key)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border transition-all min-h-[38px] ${
                  isSelected
                    ? 'bg-[#C65319] text-white border-[#C65319] shadow-xs'
                    : 'bg-white text-[#594333] border-[#E2DDD3] hover:bg-[#F0EDE5]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-[#C65319]'}`} />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Facilities List + Inspection Pane */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#C65319] animate-spin mx-auto" />
          <p className="text-xs text-[#7A6858]">सुविधा माहिती लोड होत आहे...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : facilities.length === 0 ? (
        <div className="py-16 text-center bg-white border border-[#E2DDD3] rounded-3xl space-y-2">
          <Compass className="w-8 h-8 text-[#A09385] mx-auto" />
          <h3 className="text-sm font-bold text-[#292723]">कोणतीही सुविधा आढळली नाही</h3>
          <p className="text-xs text-[#7A6858]">कृपया अन्य श्रेणी किंवा शोध संज्ञा वापरून पहा.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Facility List (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <p className="text-xs text-[#7A6858] font-medium">
              एकूण {facilities.length} सुविधा उपलब्ध:
            </p>

            <div className="space-y-3">
              {facilities.map((fac) => {
                const isSelected = selectedFacility?.id === fac.id;
                return (
                  <div
                    key={fac.id}
                    onClick={() => setSelectedFacility(fac)}
                    className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-[#FAF8F3] border-[#C65319] shadow-sm'
                        : 'bg-white border-[#E2DDD3] hover:border-[#C69A52]/60 hover:bg-[#FAF8F3]/50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-[#292723] font-marathi">
                            {fac.name}
                          </h3>
                          {fac.is_verified ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>पडताळलेले (Verified)</span>
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
                              डेमो माहिती (Unverified)
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[#594333] flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-[#C65319]" />
                          <span>{fac.location || 'पंढरपूर वारी मार्ग'}</span>
                        </p>
                      </div>

                      <span className="text-[11px] font-mono font-bold text-[#A83E16] bg-[#FAF8F3] px-2 py-1 rounded border border-[#E2DDD3] uppercase">
                        {fac.category.replace('_', ' ')}
                      </span>
                    </div>

                    {fac.description && (
                      <p className="text-xs text-[#7A6858] mt-2 line-clamp-2 leading-relaxed">
                        {fac.description}
                      </p>
                    )}

                    <div className="pt-3 mt-3 border-t border-[#E2DDD3] flex items-center justify-between text-[11px] text-[#A09385]">
                      <span>स्थिती: <strong className="text-emerald-700">{fac.operational_status || 'कार्यरत (Operational)'}</strong></span>
                      {fac.latitude && fac.longitude && (
                        <span className="font-mono">
                          {fac.latitude.toFixed(4)}°N, {fac.longitude.toFixed(4)}°E
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed Inspection Pane (1 col) */}
          <div className="bg-white border border-[#E2DDD3] rounded-3xl p-6 shadow-xs sticky top-24 space-y-5">
            {selectedFacility ? (
              <>
                <div className="space-y-1 pb-4 border-b border-[#E2DDD3]">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#C65319]">
                    सुविधा सविस्तर माहिती / Details
                  </span>
                  <h2 className="text-base font-bold text-[#292723] font-marathi">
                    {selectedFacility.name}
                  </h2>
                  <p className="text-xs text-[#594333]">
                    {selectedFacility.location}
                  </p>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <span className="font-semibold text-[#292723]">प्रकार (Category):</span>
                    <p className="text-[#594333] mt-0.5 capitalize">
                      {selectedFacility.category.replace('_', ' ')}
                    </p>
                  </div>

                  <div>
                    <span className="font-semibold text-[#292723]">तपशील (Description):</span>
                    <p className="text-[#594333] mt-0.5 leading-relaxed">
                      {selectedFacility.description || 'माहिती उपलब्ध नाही.'}
                    </p>
                  </div>

                  <div>
                    <span className="font-semibold text-[#292723]">अचूक GPS समन्वय (Coordinates):</span>
                    <p className="font-mono text-[#292723] bg-[#FAF8F3] p-2 rounded-lg border border-[#E2DDD3] mt-1 text-center">
                      {selectedFacility.latitude ? `${selectedFacility.latitude}, ${selectedFacility.longitude}` : 'Coordinates pending verification'}
                    </p>
                  </div>

                  {selectedFacility.contact_phone && (
                    <div>
                      <span className="font-semibold text-[#292723]">हेल्पलाईन / संपर्क:</span>
                      <p className="text-[#C65319] font-bold mt-0.5 flex items-center gap-1.5">
                        <Phone className="w-3.5 h-3.5" />
                        <span>{selectedFacility.contact_phone}</span>
                      </p>
                    </div>
                  )}

                  {selectedFacility.latitude && selectedFacility.longitude && (
                    <div className="pt-2">
                      <a
                        href={`https://www.openstreetmap.org/?mlat=${selectedFacility.latitude}&mlon=${selectedFacility.longitude}#map=16/${selectedFacility.latitude}/${selectedFacility.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 bg-[#FAF8F3] hover:bg-[#F0EDE5] text-[#292723] font-semibold rounded-xl border border-[#E2DDD3] transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5 text-[#C65319]" />
                        <span>View on OpenStreetMap</span>
                      </a>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="text-xs text-[#7A6858] text-center py-8">
                कोणतीही सुविधा निवडा.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
