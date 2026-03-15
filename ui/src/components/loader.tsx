export function MementoLoader() {
  return (
    <svg viewBox="0 0 100 80" width="48" height="48" xmlns="http://www.w3.org/2000/svg"
      style={{ display: "block" }}>
      <style>{`
        @keyframes mDiag {
          0%,5%    { stroke-dashoffset:120; opacity:.3 }
          40%      { stroke-dashoffset:0;   opacity:1  }
          85%,100% { stroke-dashoffset:0;   opacity:1  }
        }
        @keyframes mDot {
          0%,35%  { r:0; opacity:0 }
          55%     { r:7; opacity:1 }
          65%     { r:5; opacity:1 }
          85%,100%{ r:5; opacity:1 }
        }
        @keyframes mOut {
          0%,50%   { stroke-dashoffset:60; opacity:0 }
          52%      { opacity:1 }
          80%      { stroke-dashoffset:0;  opacity:1 }
          85%,100% { stroke-dashoffset:0;  opacity:1 }
        }
        @keyframes mFade {
          0%,80%{ opacity:1 }
          95%   { opacity:0 }
          100%  { opacity:0 }
        }
        .mw  { animation: mFade  2.4s ease-in-out infinite; }
        .mlt { stroke-dasharray:120; stroke-dashoffset:120; animation: mDiag 2.4s ease-in-out infinite; }
        .mlb { stroke-dasharray:120; stroke-dashoffset:120; animation: mDiag 2.4s ease-in-out infinite; }
        .mld { animation: mDot 2.4s ease-in-out infinite; }
        .mlo { stroke-dasharray:60;  stroke-dashoffset:60;  animation: mOut  2.4s ease-in-out infinite; }
      `}</style>
      <g className="mw">
        <line className="mlt" x1="8"  y1="14" x2="52" y2="40" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/>
        <line className="mlb" x1="8"  y1="66" x2="52" y2="40" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/>
        <circle className="mld" cx="52" cy="40" fill="currentColor"/>
        <line className="mlo" x1="52" y1="40" x2="92" y2="40" stroke="currentColor" strokeWidth="4" strokeLinecap="round"/>
      </g>
    </svg>
  );
}