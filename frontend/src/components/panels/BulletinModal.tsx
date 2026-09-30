import { useId } from 'react'
import type { Threat } from '../../types/forecast'
import { CATEGORY_LABELS, formatDate, formatPeople } from '../../lib/format'

interface BulletinModalProps {
  date: string
  leadTime: number
  threats: Threat[]
  onClose: () => void
}

/** National Emblem of India (Lion Capital of Ashoka with Satyameva Jayate) */
function StateEmblem({ className = 'h-12 w-10' }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 120" className={className} fill="currentColor" aria-hidden="true">
      <g>
        {/* Central Lion Head & Mane */}
        <path d="M42 16 C42 11, 46 7, 50 7 C54 7, 58 11, 58 16 C58 20, 61 24, 62 29 C63 34, 59 38, 50 38 C41 38, 37 34, 38 29 C39 24, 42 20, 42 16 Z" />
        {/* Left Lion Profile */}
        <path d="M38 18 C35 15, 30 15, 27 18 C24 21, 23 27, 26 32 C28 35, 33 37, 39 37 C38 33, 37 25, 38 18 Z" />
        {/* Right Lion Profile */}
        <path d="M62 18 C65 15, 70 15, 73 18 C76 21, 77 27, 74 32 C72 35, 67 37, 61 37 C62 33, 63 25, 62 18 Z" />
        {/* Chest & Posture */}
        <path d="M31 37 C25 40, 22 47, 24 55 C26 62, 33 66, 37 66 L63 66 C67 66, 74 62, 76 55 C78 47, 75 40, 69 37 C64 42, 57 44, 50 44 C43 44, 36 42, 31 37 Z" />
        {/* Pillar Abacus Platform */}
        <rect x="18" y="68" width="64" height="6" rx="2" />
        {/* Dharma Chakra (24-spoke wheel) */}
        <circle cx="50" cy="82" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
        <circle cx="50" cy="82" r="2.5" />
        {/* Wheel spokes */}
        <line x1="50" y1="74" x2="50" y2="90" stroke="currentColor" strokeWidth="1.2" />
        <line x1="42" y1="82" x2="58" y2="82" stroke="currentColor" strokeWidth="1.2" />
        <line x1="44.3" y1="76.3" x2="55.7" y2="87.7" stroke="currentColor" strokeWidth="1.2" />
        <line x1="44.3" y1="87.7" x2="55.7" y2="76.3" stroke="currentColor" strokeWidth="1.2" />
        {/* Left Guardian (Bull) & Right Guardian (Horse) silhouettes */}
        <ellipse cx="28" cy="82" rx="6" ry="4" />
        <ellipse cx="72" cy="82" rx="6" ry="4" />
        {/* Bell Lotus Base */}
        <path d="M22 92 C28 91, 35 93, 50 93 C65 93, 72 91, 78 92 C74 100, 64 103, 50 103 C36 103, 26 100, 22 92 Z" />
        {/* Satyameva Jayate Motto Banner */}
        <rect x="25" y="105" width="50" height="2" rx="1" />
        <text
          x="50"
          y="116"
          textAnchor="middle"
          fontSize="7"
          fontFamily="'Noto Sans Devanagari', 'Inter', sans-serif"
          fontWeight="bold"
          fill="currentColor"
        >
          सत्यमेव जयते
        </text>
      </g>
    </svg>
  )
}

export function BulletinModal({ date, leadTime, threats, onClose }: BulletinModalProps) {
  const titleId = useId()
  const extremeCount = threats.filter((t) => t.category === 'extremely_heavy').length
  const veryHeavyCount = threats.filter((t) => t.category === 'very_heavy').length
  const heavyCount = threats.filter((t) => t.category === 'heavy').length
  const totalExposed = threats.reduce((sum, t) => sum + t.population_exposed, 0)

  const handlePrint = () => {
    window.print()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      className="print-bulletin-dialog fixed inset-0 z-[1200] grid place-items-center overflow-y-auto bg-slate-950/85 p-4 backdrop-blur-sm print:static print:inset-auto print:block print:h-auto print:w-full print:bg-white print:p-0 print:backdrop-blur-none"
    >
      <div className="print-bulletin-card relative my-6 w-full max-w-4xl rounded-2xl border border-white/15 bg-slate-900/95 p-6 text-slate-100 shadow-2xl print:my-0 print:w-full print:max-w-none print:border-none print:bg-white print:p-0 print:text-black print:shadow-none">
        {/* Actions bar (hidden in print) */}
        <div className="mb-5 flex items-center justify-between border-b border-white/10 pb-3 print:hidden">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-red-400" />
            <span className="text-xs font-semibold tracking-wider text-slate-300 uppercase">
              Official Civil Advisory Bulletin
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handlePrint}
              className="flex items-center gap-1.5 rounded-lg bg-cyan-500/20 px-3.5 py-1.5 text-xs font-semibold text-cyan-200 ring-1 ring-cyan-400/40 transition-colors hover:bg-cyan-500/30 cursor-pointer"
            >
              <span>Print / Save PDF</span>
              <span>🖨</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg bg-white/5 px-3 py-1.5 text-xs text-slate-300 ring-1 ring-white/10 transition-colors hover:bg-white/10 hover:text-white cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>

        {/* Official Letterhead Header */}
        <div className="print-avoid-break border-b-2 border-slate-700 pb-3 text-center print:border-black print:pb-2">
          <div className="flex flex-col items-center">
            <div className="text-amber-400 print:text-black">
              <StateEmblem className="h-10 w-9" />
            </div>
            <p className="mt-1 text-xs font-bold text-slate-300 print:text-black">
              <span lang="hi">भारत सरकार</span>
              <span className="mx-2 text-slate-500 print:text-gray-400">|</span>
              <span className="tracking-wider uppercase">Government of India</span>
            </p>
            <h2 className="mt-0.5 text-base font-extrabold text-white print:text-black">
              <span lang="hi">पृथ्वी विज्ञान मंत्रालय</span>
              <span className="mx-2 font-normal text-slate-500 print:text-gray-400">|</span>
              <span className="tracking-wide uppercase">Ministry of Earth Sciences</span>
            </h2>
            <p className="mt-0.5 text-sm font-bold text-cyan-300 print:text-black">
              <span lang="hi">भारत मौसम विज्ञान विभाग</span>
              <span className="mx-2 font-normal text-slate-500 print:text-gray-400">|</span>
              <span className="tracking-wide uppercase">India Meteorological Department</span>
            </p>
            <p className="mt-1 text-[11px] text-slate-400 print:text-gray-700">
              <span lang="hi">राष्ट्रीय मौसम पूर्वानुमान केंद्र, नई दिल्ली</span>
              <span className="mx-1.5 text-slate-500 print:text-gray-400">·</span>
              <span>National Weather Forecasting Centre, New Delhi</span>
            </p>
            <p className="text-[10px] text-slate-500 print:text-gray-600">
              Meghdrishti AI-NWP Super-UNet High-Resolution Ensemble Decision Support System (SIH26081)
            </p>
          </div>

          <div className="mt-2.5 rounded-lg border border-slate-700/80 bg-slate-800/40 p-2 print:border-black print:bg-gray-100 print:p-1.5">
            <h1 id={titleId} className="text-sm font-extrabold tracking-wide text-white uppercase print:text-black sm:text-base">
              SPECIAL IMPACT-BASED SEVERE RAINFALL ADVISORY BULLETIN
            </h1>
            <div className="mt-1 flex flex-wrap justify-center gap-x-6 gap-y-0.5 font-mono text-[11px] text-slate-300 print:text-gray-900 sm:text-xs">
              <span><strong>Bulletin ID:</strong> IMD/MoES/IBF-{date.replace(/-/g, '')}-T{leadTime}H</span>
              <span><strong>Forecast Issue:</strong> {formatDate(date)}</span>
              <span><strong>Valid Horizon:</strong> +{leadTime}h (Day {leadTime / 24})</span>
              <span><strong>Target:</strong> National Weather Grid</span>
            </div>
          </div>
        </div>

        {/* Executive Summary Stats */}
        <div className="print-avoid-break my-3 grid grid-cols-2 gap-2 print:my-2 sm:grid-cols-4 print:grid-cols-4">
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-2 text-center print:rounded print:border print:border-gray-400 print:bg-white print:p-1.5">
            <p className="text-[11px] font-semibold text-red-300 uppercase print:text-red-700">Red Warning</p>
            <p className="mt-0.5 text-2xl font-bold text-white print:text-black">{extremeCount}</p>
            <p className="text-[10px] text-slate-400 print:text-gray-600">≥ 204.5 mm / 24h</p>
          </div>
          <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-2 text-center print:rounded print:border print:border-gray-400 print:bg-white print:p-1.5">
            <p className="text-[11px] font-semibold text-orange-300 uppercase print:text-orange-700">Orange Alert</p>
            <p className="mt-0.5 text-2xl font-bold text-white print:text-black">{veryHeavyCount}</p>
            <p className="text-[10px] text-slate-400 print:text-gray-600">115.6 – 204.4 mm</p>
          </div>
          <div className="rounded-xl border border-yellow-400/30 bg-yellow-400/10 p-2 text-center print:rounded print:border print:border-gray-400 print:bg-white print:p-1.5">
            <p className="text-[11px] font-semibold text-yellow-200 uppercase print:text-amber-800">Yellow Watch</p>
            <p className="mt-0.5 text-2xl font-bold text-white print:text-black">{heavyCount}</p>
            <p className="text-[10px] text-slate-400 print:text-gray-600">64.5 – 115.5 mm</p>
          </div>
          <div className="rounded-xl border border-cyan-400/30 bg-cyan-500/10 p-2 text-center print:rounded print:border print:border-gray-400 print:bg-white print:p-1.5">
            <p className="text-[11px] font-semibold text-cyan-200 uppercase print:text-blue-800">Total Population</p>
            <p className="mt-0.5 text-xl font-bold text-white print:text-black">{formatPeople(totalExposed)}</p>
            <p className="text-[10px] text-slate-400 print:text-gray-600">Exposed In Hazard Zones</p>
          </div>
        </div>

        {/* Tabular District Threat Matrix */}
        <div className="print-avoid-break my-3 print:my-2">
          <h3 className="mb-1.5 text-xs font-bold tracking-wider text-slate-300 uppercase print:text-black">
            Priority Districts Requiring Immediate Civil Protection Measures
          </h3>
          <div className="overflow-x-auto rounded-xl ring-1 ring-white/10 print:rounded-none print:ring-1 print:ring-black">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/5 font-semibold text-slate-300 print:border-b print:border-black print:bg-gray-100 print:text-black">
                <tr>
                  <th className="px-3 py-2 print:py-1">#</th>
                  <th className="px-3 py-2 print:py-1">District & State</th>
                  <th className="px-3 py-2 print:py-1">Peak Rain</th>
                  <th className="px-3 py-2 print:py-1">IMD Classification</th>
                  <th className="px-3 py-2 print:py-1">Population at Risk</th>
                  <th className="px-3 py-2 print:py-1">Risk Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 print:divide-y print:divide-gray-300">
                {threats.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-3 text-center text-slate-400 print:text-gray-700">
                      No severe rainfall regions detected for the selected period.
                    </td>
                  </tr>
                ) : (
                  threats.slice(0, 8).map((t) => (
                    <tr key={t.id} className="hover:bg-white/[0.02] print:hover:bg-transparent">
                      <td className="px-3 py-1.5 font-mono text-slate-400 print:text-black">#{t.severity_rank}</td>
                      <td className="px-3 py-1.5 font-semibold text-white print:text-black">
                        {t.district}, <span className="font-normal text-slate-400 print:text-gray-700">{t.state}</span>
                      </td>
                      <td className="px-3 py-1.5 font-mono font-semibold text-cyan-300 print:text-black">{t.peak_mm} mm</td>
                      <td className="px-3 py-1.5">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                            t.category === 'extremely_heavy'
                              ? 'bg-red-600/25 text-red-200 print:border print:border-red-700 print:bg-red-50 print:text-red-900'
                              : t.category === 'very_heavy'
                                ? 'bg-orange-500/25 text-orange-200 print:border print:border-orange-600 print:bg-orange-50 print:text-orange-900'
                                : 'bg-yellow-400/20 text-yellow-200 print:border print:border-amber-600 print:bg-amber-50 print:text-amber-900'
                          }`}
                        >
                          {CATEGORY_LABELS[t.category]}
                        </span>
                      </td>
                      <td className="px-3 py-1.5 font-mono text-slate-300 print:text-black">{formatPeople(t.population_exposed)}</td>
                      <td className="px-3 py-1.5 font-mono font-bold text-white print:text-black">{t.risk_index}/100</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {threats.length > 8 && (
            <p className="mt-1 text-[10px] text-slate-400 print:text-gray-600">
              * Showing top 8 high-risk districts. Full list of {threats.length} affected districts monitored in digital system.
            </p>
          )}
        </div>

        {/* Standard Operational Directives (NDMA / IMD Protocols) */}
        <div className="print-avoid-break my-3 rounded-xl border border-white/10 bg-white/[0.02] p-3 text-xs leading-relaxed text-slate-300 print:my-2 print:rounded print:border print:border-black print:bg-gray-50 print:p-2.5 print:text-black">
          <p className="font-bold text-white uppercase print:text-black">Standard Civil Action Directives (NDMA / SDMA SOP):</p>
          <ul className="mt-1.5 list-disc space-y-0.5 pl-4 text-[11px] sm:text-xs">
            <li>
              <strong>Emergency Operations Centres (EOC):</strong> District Magistrates in Red/Orange alert zones are advised to activate district control rooms 24×7.
            </li>
            <li>
              <strong>Pre-positioning of Response Forces:</strong> National Disaster Response Force (NDRF) & State Disaster Response Force (SDRF) units to be placed on immediate standby.
            </li>
            <li>
              <strong>Vulnerable Terrains:</strong> Prohibit civilian movement along landslide-prone mountain routes and riverbanks in hilly catchment areas.
            </li>
            <li>
              <strong>Public Dissemination:</strong> Trigger localized Common Alerting Protocol (CAP) and Cell Broadcast SMS in corresponding regional languages.
            </li>
          </ul>
        </div>

        {/* Official Sign-off */}
        <div className="print-avoid-break mt-4 flex items-end justify-between border-t-2 border-slate-700 pt-2 text-xs text-slate-400 print:mt-3 print:border-black print:pt-2 print:text-black">
          <div>
            <p className="font-semibold text-slate-200 print:text-black">Meghdrishti Super-UNet Blending Engine</p>
            <p className="text-[10px] text-slate-400 print:text-gray-700">Ministry of Earth Sciences · Government of India (SIH26081)</p>
            <p className="text-[9px] text-slate-500 font-mono print:text-gray-600">Issued: {date} · Auto-generated Certified Civil Advisory</p>
          </div>
          <div className="text-right">
            <p className="font-bold text-slate-200 print:text-black">Duty Meteorological Officer</p>
            <p className="text-[11px] text-slate-400 print:text-gray-700">National Weather Forecasting Centre (NWFC)</p>
            <p className="text-[10px] text-slate-500 print:text-gray-600">India Meteorological Department, New Delhi</p>
          </div>
        </div>
      </div>
    </div>
  )
}
