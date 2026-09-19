import { useState, useEffect, useCallback } from "react";

const TOUR_STEPS = [
  {
    target: '[data-tour="active-dataset"]',
    title: "1. Preloaded Netflix Dataset",
    description: "You're exploring Netflix's catalog with 8,800+ titles pre-indexed. In full mode, you can upload your own CSV datasets here.",
    position: "bottom",
  },
  {
    target: '[data-tour="tab-switcher"]',
    title: "2. Insights, Spreadsheet & Dashboard",
    description: "Switch seamlessly between AI Chat, the live Spreadsheet data editor (to view/edit rows), and pinned KPI Dashboard widgets.",
    position: "bottom",
  },
  {
    target: '[data-tour="chat-input"]',
    title: "3. Autonomous Analysis",
    description: "Ask any analytical question in plain English or click sample prompt chips. The AI writes Python/pandas code and executes it automatically.",
    position: "top",
  },
  {
    target: '[data-tour="chart-panel"]',
    title: "4. Live Charts & Visualizations",
    description: "Generated bar, line, and pie charts render interactively here in real time. You can zoom in, download charts, or pin them to your dashboard.",
    position: "left",
  },
];

export default function ProductTour({ isOpen, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [coords, setCoords] = useState(null);

  const step = TOUR_STEPS[currentStep];

  const updatePosition = useCallback(() => {
    if (!isOpen || !step) return;
    const el = document.querySelector(step.target);
    if (el) {
      const rect = el.getBoundingClientRect();
      setCoords({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
        bottom: rect.bottom,
        right: rect.right,
      });
      // Scroll into view if needed
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      setCoords(null);
    }
  }, [isOpen, step]);

  useEffect(() => {
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [updatePosition]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "ArrowLeft") handlePrev();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem("hasSeenTour", "true");
    onClose();
  };

  // Compute tooltip card position relative to target
  let tooltipStyle = {};
  if (coords) {
    const padding = 12;
    if (step.position === "bottom") {
      tooltipStyle = {
        top: Math.min(window.innerHeight - 220, coords.bottom + padding),
        left: Math.max(16, Math.min(window.innerWidth - 340, coords.left)),
      };
    } else if (step.position === "top") {
      tooltipStyle = {
        bottom: window.innerHeight - coords.top + padding,
        left: Math.max(16, Math.min(window.innerWidth - 340, coords.left)),
      };
    } else if (step.position === "left") {
      tooltipStyle = {
        top: Math.max(70, Math.min(window.innerHeight - 240, coords.top + 20)),
        right: window.innerWidth - coords.left + padding,
      };
    }
  } else {
    tooltipStyle = {
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
    };
  }

  return (
    <div className="fixed inset-0 z-50 pointer-events-auto">
      {/* Dark overlay with spotlight cutout */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-[1.5px] transition-all duration-300" onClick={handleComplete} />

      {/* Target highlight ring */}
      {coords && (
        <div
          className="fixed pointer-events-none rounded-xl border-2 border-accent ring-4 ring-accent/30 transition-all duration-300 z-50 shadow-2xl"
          style={{
            top: coords.top - 4,
            left: coords.left - 4,
            width: coords.width + 8,
            height: coords.height + 8,
          }}
        />
      )}

      {/* Tooltip Card */}
      <div
        className="fixed z-50 w-80 sm:w-96 p-5 rounded-2xl bg-white dark:bg-gray-900 border border-surface-200 dark:border-gray-800 shadow-2xl transition-all duration-300 animate-scale-up"
        style={tooltipStyle}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider rounded-full bg-accent/15 text-accent">
            Step {currentStep + 1} of {TOUR_STEPS.length}
          </span>
          <button
            onClick={handleComplete}
            className="text-xs text-surface-400 dark:text-gray-500 hover:text-surface-700 dark:hover:text-gray-300 transition-colors"
          >
            Skip tour
          </button>
        </div>

        <h4 className="text-base font-bold text-surface-900 dark:text-white mb-1.5">
          {step.title}
        </h4>
        <p className="text-xs text-surface-600 dark:text-gray-300 leading-relaxed mb-5">
          {step.description}
        </p>

        <div className="flex items-center justify-between pt-2 border-t border-surface-100 dark:border-gray-800">
          <div className="flex gap-1.5">
            {TOUR_STEPS.map((_, idx) => (
              <div
                key={idx}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  idx === currentStep ? "w-5 bg-accent" : "w-1.5 bg-surface-200 dark:bg-gray-700"
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                type="button"
                onClick={handlePrev}
                className="px-3 py-1.5 text-xs font-medium rounded-lg text-surface-600 dark:text-gray-300 hover:bg-surface-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
              >
                Back
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-accent hover:bg-accent-hover text-white shadow-xs transition-colors cursor-pointer"
            >
              {currentStep === TOUR_STEPS.length - 1 ? "Got it!" : "Next →"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
